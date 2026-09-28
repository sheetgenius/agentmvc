use crate::{
    controllers::common::*,
    models::realworld as db,
    workers::export::{ExportArgs, ExportWorker},
};
use axum::{
    http::{HeaderMap, StatusCode},
    Json,
};
use loco_rs::prelude::*;
use serde_json::{json, Value};
use std::{
    collections::HashMap,
    sync::{Mutex, OnceLock},
    time::{Duration, Instant},
};
use uuid::Uuid;

static LOGIN_FAILURES: OnceLock<Mutex<HashMap<String, (u32, Instant)>>> = OnceLock::new();

async fn register(State(ctx): State<AppContext>, Json(body): Json<Value>) -> ApiResult {
    let user = object(&body, "user")?;
    let username = required(user, "username")?;
    let email = required(user, "email")?;
    let password = required(user, "password")?;
    if db::user_by(&ctx.db, "username", username).await?.is_some() {
        return Err(fail(
            StatusCode::CONFLICT,
            "username",
            "has already been taken",
        ));
    }
    if db::user_by(&ctx.db, "email", email).await?.is_some() {
        return Err(fail(
            StatusCode::CONFLICT,
            "email",
            "has already been taken",
        ));
    }
    let hash = loco_rs::hash::hash_password(password).map_err(|_| invalid("password"))?;
    let saved = db::row(&ctx.db, "WITH t AS (INSERT INTO rw_users(username,email,password) VALUES($1,$2,$3) RETURNING id,username,email,bio,image) SELECT row_to_json(t)::text data FROM t", vec![username.into(), email.into(), hash.into()]).await?.ok_or_else(|| missing("user"))?;
    Ok(respond(
        StatusCode::CREATED,
        json!({"user":db::public_user(&saved, token(&ctx, id(&saved)))}),
    ))
}

async fn login(State(ctx): State<AppContext>, Json(body): Json<Value>) -> ApiResult {
    let user = object(&body, "user")?;
    let email = required(user, "email")?;
    let password = required(user, "password")?;
    let attempts = LOGIN_FAILURES.get_or_init(|| Mutex::new(HashMap::new()));
    {
        let failures = attempts.lock().expect("login counter");
        if failures
            .get(email)
            .is_some_and(|(n, t)| *n >= 20 && t.elapsed() < Duration::from_secs(300))
        {
            return Err(fail(
                StatusCode::TOO_MANY_REQUESTS,
                "credentials",
                "rate limited",
            ));
        }
    }
    let found = db::user_by(&ctx.db, "email", email).await?;
    if let Some(ref found) = found {
        if loco_rs::hash::verify_password(password, found["password"].as_str().unwrap_or_default())
        {
            attempts.lock().expect("login counter").remove(email);
            return Ok(respond(
                StatusCode::OK,
                json!({"user":db::public_user(found, token(&ctx, id(found)))}),
            ));
        }
    }
    let mut failures = attempts.lock().expect("login counter");
    let entry = failures
        .entry(email.to_owned())
        .or_insert((0, Instant::now()));
    if entry.1.elapsed() >= Duration::from_secs(300) {
        *entry = (0, Instant::now());
    }
    entry.0 += 1;
    Err(fail(StatusCode::UNAUTHORIZED, "credentials", "invalid"))
}

async fn current(State(ctx): State<AppContext>, headers: HeaderMap) -> ApiResult {
    let user_id = required_viewer(&ctx, &headers)?;
    let user = db::user(&ctx.db, user_id)
        .await?
        .ok_or_else(|| missing("user"))?;
    Ok(respond(
        StatusCode::OK,
        json!({"user":db::public_user(&user, token(&ctx,user_id))}),
    ))
}

async fn update(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Json(body): Json<Value>,
) -> ApiResult {
    let user_id = required_viewer(&ctx, &headers)?;
    let changes = object(&body, "user")?;
    for field in ["username", "email", "password"] {
        if changes.get(field).is_some() {
            required(changes, field)?;
        }
    }
    if let Some(password) = changes.get("password") {
        if password.as_str().unwrap_or_default().chars().count() < 8 {
            return Err(invalid("password"));
        }
    }
    if let Some(username) = changes.get("username").and_then(Value::as_str) {
        if db::user_by(&ctx.db, "username", username)
            .await?
            .is_some_and(|v| id(&v) != user_id)
        {
            return Err(fail(
                StatusCode::CONFLICT,
                "username",
                "has already been taken",
            ));
        }
    }
    if let Some(email) = changes.get("email").and_then(Value::as_str) {
        if db::user_by(&ctx.db, "email", email)
            .await?
            .is_some_and(|v| id(&v) != user_id)
        {
            return Err(fail(
                StatusCode::CONFLICT,
                "email",
                "has already been taken",
            ));
        }
    }
    let password = match changes.get("password").and_then(Value::as_str) {
        Some(value) => Some(loco_rs::hash::hash_password(value).map_err(|_| invalid("password"))?),
        None => None,
    };
    let saved = db::row(&ctx.db, "WITH t AS (UPDATE rw_users SET username=COALESCE($2,username),email=COALESCE($3,email),password=COALESCE($4,password),bio=CASE WHEN $7 THEN NULLIF($5,'') ELSE bio END,image=CASE WHEN $8 THEN NULLIF($6,'') ELSE image END WHERE id=$1 RETURNING id,username,email,bio,image) SELECT row_to_json(t)::text data FROM t", vec![user_id.into(), changes["username"].as_str().map(str::to_owned).into(), changes["email"].as_str().map(str::to_owned).into(), password.into(), changes["bio"].as_str().map(str::to_owned).into(), changes["image"].as_str().map(str::to_owned).into(), changes.get("bio").is_some().into(), changes.get("image").is_some().into()]).await?.ok_or_else(|| missing("user"))?;
    Ok(respond(
        StatusCode::OK,
        json!({"user":db::public_user(&saved,token(&ctx,user_id))}),
    ))
}

async fn profile(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Path(username): Path<String>,
) -> ApiResult {
    let profile = db::profile(&ctx.db, &username, viewer(&ctx, &headers))
        .await?
        .ok_or_else(|| missing("profile"))?;
    Ok(respond(StatusCode::OK, json!({"profile":profile})))
}

async fn follow(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Path(username): Path<String>,
) -> ApiResult {
    let follower = required_viewer(&ctx, &headers)?;
    let target = db::user_by(&ctx.db, "username", &username)
        .await?
        .ok_or_else(|| missing("profile"))?;
    if follower != id(&target) {
        db::exec(
            &ctx.db,
            "INSERT INTO rw_follows(follower,followed) VALUES($1,$2) ON CONFLICT DO NOTHING",
            vec![follower.into(), id(&target).into()],
        )
        .await?;
    }
    profile(State(ctx), headers, Path(username)).await
}

async fn unfollow(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Path(username): Path<String>,
) -> ApiResult {
    let follower = required_viewer(&ctx, &headers)?;
    let target = db::user_by(&ctx.db, "username", &username)
        .await?
        .ok_or_else(|| missing("profile"))?;
    db::exec(
        &ctx.db,
        "DELETE FROM rw_follows WHERE follower=$1 AND followed=$2",
        vec![follower.into(), id(&target).into()],
    )
    .await?;
    profile(State(ctx), headers, Path(username)).await
}

async fn create_export(State(ctx): State<AppContext>, headers: HeaderMap) -> ApiResult {
    let user_id = required_viewer(&ctx, &headers)?;
    let export_id = Uuid::new_v4().to_string();
    let export = db::row(&ctx.db,"WITH t AS (INSERT INTO rw_exports(id,user_id) VALUES($1,$2) RETURNING id,status,created_at AS \"createdAt\",completed_at AS \"completedAt\",articles) SELECT row_to_json(t)::text data FROM t",vec![export_id.clone().into(),user_id.into()]).await?.ok_or_else(|| missing("export"))?;
    ExportWorker::perform_later(&ctx, ExportArgs { id: export_id })
        .await
        .map_err(|error| {
            tracing::error!(%error,"enqueue export");
            fail(StatusCode::INTERNAL_SERVER_ERROR, "export", "failed")
        })?;
    Ok(respond(StatusCode::ACCEPTED, json!({"export":export})))
}

async fn show_export(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Path(export_id): Path<String>,
) -> ApiResult {
    let user_id = required_viewer(&ctx, &headers)?;
    let export = db::row(&ctx.db,"SELECT row_to_json(t)::text data FROM (SELECT id,status,created_at AS \"createdAt\",completed_at AS \"completedAt\",articles FROM rw_exports WHERE id=$1 AND user_id=$2) t",vec![export_id.into(),user_id.into()]).await?.ok_or_else(|| missing("export"))?;
    Ok(respond(StatusCode::OK, json!({"export":export})))
}

pub fn routes() -> Routes {
    Routes::new()
        .prefix("/api")
        .add("/users", post(register))
        .add("/users/login", post(login))
        .add("/user", get(current))
        .add("/user", put(update))
        .add("/profiles/{username}", get(profile))
        .add("/profiles/{username}/follow", post(follow))
        .add("/profiles/{username}/follow", delete(unfollow))
        .add("/user/exports", post(create_export))
        .add("/user/exports/{id}", get(show_export))
}
