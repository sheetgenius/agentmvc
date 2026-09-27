use axum::{
    extract::{Json, State},
    http::StatusCode,
};
use loco_rs::prelude::*;
use serde::Deserialize;
use serde_json::{json, Value};

use crate::{
    controllers::api::{self, ApiError, ApiResult, Viewer},
    models::users,
    views::realworld::UserView,
};

#[derive(Deserialize)]
struct Envelope<T> {
    user: T,
}

#[derive(Deserialize)]
struct Registration {
    #[serde(default)]
    username: String,
    #[serde(default)]
    email: String,
    #[serde(default)]
    password: String,
}

#[derive(Deserialize)]
struct Login {
    #[serde(default)]
    email: String,
    #[serde(default)]
    password: String,
}

fn response(ctx: &AppContext, user: &users::Model, status: StatusCode) -> ApiResult {
    let config = ctx
        .config
        .get_jwt_config()
        .map_err(|_| ApiError::new(StatusCode::INTERNAL_SERVER_ERROR, "server", "error"))?;
    let token = user.token(&config.secret, config.expiration)?;
    Ok(api::json_response(
        status,
        json!({"user": UserView::new(user, token)}),
    ))
}

#[debug_handler]
async fn register(
    State(ctx): State<AppContext>,
    Json(Envelope { user }): Json<Envelope<Registration>>,
) -> ApiResult {
    api::required(&user.username, "username")?;
    api::required(&user.email, "email")?;
    api::required(&user.password, "password")?;
    if users::Model::by_username(&ctx.db, &user.username)
        .await?
        .is_some()
    {
        return Err(ApiError::taken("username"));
    }
    if users::Model::by_email(&ctx.db, &user.email)
        .await?
        .is_some()
    {
        return Err(ApiError::taken("email"));
    }
    let user = users::Model::register(&ctx.db, user.username, user.email, user.password).await?;
    response(&ctx, &user, StatusCode::CREATED)
}

#[debug_handler]
async fn login(
    State(ctx): State<AppContext>,
    Json(Envelope { user }): Json<Envelope<Login>>,
) -> ApiResult {
    api::required(&user.email, "email")?;
    api::required(&user.password, "password")?;
    let user = users::Model::by_email(&ctx.db, &user.email)
        .await?
        .filter(|record| record.verify_password(&user.password))
        .ok_or(ApiError::new(
            StatusCode::UNAUTHORIZED,
            "credentials",
            "invalid",
        ))?;
    response(&ctx, &user, StatusCode::OK)
}

#[debug_handler]
async fn current(Viewer(user): Viewer, State(ctx): State<AppContext>) -> ApiResult {
    response(&ctx, &user, StatusCode::OK)
}

fn text_update(value: &Value, field: &'static str) -> std::result::Result<String, ApiError> {
    let text = value.as_str().ok_or(ApiError::blank(field))?;
    api::required(text, field)?;
    Ok(text.to_owned())
}

#[debug_handler]
async fn update(
    Viewer(user): Viewer,
    State(ctx): State<AppContext>,
    Json(Envelope { user: changes }): Json<Envelope<Value>>,
) -> ApiResult {
    let mut active = user.clone().into_active_model();
    if let Some(value) = changes.get("username") {
        let username = text_update(value, "username")?;
        if username != user.username
            && users::Model::by_username(&ctx.db, &username)
                .await?
                .is_some()
        {
            return Err(ApiError::taken("username"));
        }
        active.username = Set(username);
    }
    if let Some(value) = changes.get("email") {
        let email = text_update(value, "email")?;
        if email != user.email && users::Model::by_email(&ctx.db, &email).await?.is_some() {
            return Err(ApiError::taken("email"));
        }
        active.email = Set(email);
    }
    for (field, slot) in [("bio", &mut active.bio), ("image", &mut active.image)] {
        if let Some(value) = changes.get(field) {
            let text = match value {
                Value::Null => None,
                Value::String(text) if text.is_empty() => None,
                Value::String(text) => Some(text.clone()),
                _ => return Err(ApiError::invalid(field)),
            };
            *slot = Set(text);
        }
    }
    if let Some(value) = changes.get("password") {
        let password = text_update(value, "password")?;
        if password.len() < 8 {
            return Err(ApiError::invalid("password"));
        }
        let saved = active.change_password(&ctx.db, &password).await?;
        return response(&ctx, &saved, StatusCode::OK);
    }
    let saved = active.update(&ctx.db).await?;
    response(&ctx, &saved, StatusCode::OK)
}

pub fn routes() -> Routes {
    Routes::new()
        .prefix("/api")
        .add("/users", post(register))
        .add("/users/login", post(login))
        .add("/user", get(current))
        .add("/user", put(update))
}
