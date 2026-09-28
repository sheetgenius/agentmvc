//! Conduit persistence and article representation. SQL parameters are always bound.
use sea_orm::{ConnectionTrait, DatabaseConnection, DbBackend, DbErr, Statement, Value};
use serde_json::{json, Value as Json};

pub async fn rows(
    db: &DatabaseConnection,
    sql: &str,
    args: Vec<Value>,
) -> Result<Vec<Json>, DbErr> {
    let statement = Statement::from_sql_and_values(DbBackend::Postgres, sql, args);
    db.query_all_raw(statement)
        .await?
        .into_iter()
        .map(|row| {
            let text: String = row.try_get("", "data")?;
            serde_json::from_str(&text).map_err(|error| DbErr::Custom(error.to_string()))
        })
        .collect()
}

pub async fn row(
    db: &DatabaseConnection,
    sql: &str,
    args: Vec<Value>,
) -> Result<Option<Json>, DbErr> {
    Ok(rows(db, sql, args).await?.into_iter().next())
}

pub async fn exec(db: &DatabaseConnection, sql: &str, args: Vec<Value>) -> Result<u64, DbErr> {
    Ok(db
        .execute_raw(Statement::from_sql_and_values(
            DbBackend::Postgres,
            sql,
            args,
        ))
        .await?
        .rows_affected())
}

pub async fn user(db: &DatabaseConnection, id: i64) -> Result<Option<Json>, DbErr> {
    row(db, "SELECT row_to_json(t)::text data FROM (SELECT id, username, email, password, bio, image FROM rw_users WHERE id=$1) t", vec![id.into()]).await
}

pub async fn user_by(
    db: &DatabaseConnection,
    field: &str,
    value: &str,
) -> Result<Option<Json>, DbErr> {
    let sql = match field { "email" => "SELECT row_to_json(t)::text data FROM (SELECT id, username, email, password, bio, image FROM rw_users WHERE email=$1) t", _ => "SELECT row_to_json(t)::text data FROM (SELECT id, username, email, password, bio, image FROM rw_users WHERE username=$1) t" };
    row(db, sql, vec![value.into()]).await
}

pub fn public_user(user: &Json, token: String) -> Json {
    json!({"email":user["email"],"username":user["username"],"bio":user["bio"],"image":user["image"],"token":token})
}

pub async fn profile(
    db: &DatabaseConnection,
    username: &str,
    viewer: Option<i64>,
) -> Result<Option<Json>, DbErr> {
    let user = user_by(db, "username", username).await?;
    if let Some(user) = user {
        let following = if let Some(viewer) = viewer {
            row(db, "SELECT row_to_json(t)::text data FROM (SELECT EXISTS(SELECT 1 FROM rw_follows WHERE follower=$1 AND followed=$2) AS following) t", vec![viewer.into(), user["id"].as_i64().unwrap_or_default().into()]).await?.map(|v| v["following"] == true).unwrap_or(false)
        } else {
            false
        };
        Ok(Some(
            json!({"username":user["username"],"bio":user["bio"],"image":user["image"],"following":following}),
        ))
    } else {
        Ok(None)
    }
}

pub async fn article_by_slug(db: &DatabaseConnection, slug: &str) -> Result<Option<Json>, DbErr> {
    row(db, "SELECT row_to_json(t)::text data FROM (SELECT id, author_id, slug, title, description, body, status, revision, published_at FROM rw_articles WHERE slug=$1) t", vec![slug.into()]).await
}

pub async fn article_by_id(db: &DatabaseConnection, id: i64) -> Result<Option<Json>, DbErr> {
    row(db, "SELECT row_to_json(t)::text data FROM (SELECT id, author_id, slug, title, description, body, status, revision, published_at FROM rw_articles WHERE id=$1) t", vec![id.into()]).await
}

pub async fn article_view(
    db: &DatabaseConnection,
    id: i64,
    viewer: Option<i64>,
    list: bool,
) -> Result<Option<Json>, DbErr> {
    let Some(a) = row(db, r#"SELECT row_to_json(t)::text data FROM (
      SELECT a.slug, a.title, a.description, a.body, a.status, a.revision, a.created_at, a.updated_at, a.published_at,
      u.username, u.bio, u.image,
      ARRAY(SELECT tag FROM rw_tags WHERE article_id=a.id ORDER BY position) AS tags,
      (SELECT count(*) FROM rw_favorites WHERE article_id=a.id) AS favorites_count,
      EXISTS(SELECT 1 FROM rw_favorites WHERE article_id=a.id AND user_id=$2) AS favorited,
      EXISTS(SELECT 1 FROM rw_follows WHERE follower=$2 AND followed=a.author_id) AS following
      FROM rw_articles a JOIN rw_users u ON u.id=a.author_id WHERE a.id=$1) t"#, vec![id.into(), viewer.unwrap_or_default().into()]).await? else { return Ok(None) };
    let mut view = json!({"slug":a["slug"],"title":a["title"],"description":a["description"],"tagList":a["tags"],"createdAt":a["created_at"],"updatedAt":a["updated_at"],"favorited":a["favorited"],"favoritesCount":a["favorites_count"],"author":{"username":a["username"],"bio":a["bio"],"image":a["image"],"following":a["following"]},"status":a["status"],"publishedAt":a["published_at"],"revision":a["revision"]});
    if !list {
        view["body"] = a["body"].clone();
    }
    Ok(Some(view))
}

pub fn shared(a: &Json) -> Json {
    json!({"slug":a["slug"],"title":a["title"],"body":a["body"],"revision":a["revision"]})
}

pub fn slug(title: &str) -> String {
    let stem = title
        .to_ascii_lowercase()
        .chars()
        .map(|c| if c.is_ascii_alphanumeric() { c } else { '-' })
        .collect::<String>();
    format!(
        "{}-{}",
        stem.trim_matches('-'),
        uuid::Uuid::new_v4().simple()
    )
}

pub async fn change_article(
    db: &DatabaseConnection,
    article_id: i64,
    revision: i64,
    title: Option<String>,
    description: Option<String>,
    body: Option<String>,
) -> Result<Option<Json>, DbErr> {
    let new_slug = title.as_ref().map(|s| slug(s));
    row(db,"WITH t AS (UPDATE rw_articles SET title=COALESCE($3,title),description=COALESCE($4,description),body=COALESCE($5,body),slug=COALESCE($6,slug),revision=revision+1,updated_at=now() WHERE id=$1 AND revision=$2 RETURNING id,slug,title,body,revision) SELECT row_to_json(t)::text data FROM t",vec![article_id.into(),revision.into(),title.into(),description.into(),body.into(),new_slug.into()]).await
}

pub async fn export_snapshot(db: &DatabaseConnection, user_id: i64) -> Result<Json, DbErr> {
    let articles = rows(
        db,
        r#"SELECT row_to_json(t)::text data FROM (
      SELECT a.slug, a.title, a.description, a.body, a.status,
      ARRAY(SELECT tag FROM rw_tags WHERE article_id=a.id ORDER BY position) AS "tagList",
      (SELECT count(*) FROM rw_comments WHERE article_id=a.id) AS "commentsCount"
      FROM rw_articles a WHERE author_id=$1 ORDER BY a.created_at, a.id) t"#,
        vec![user_id.into()],
    )
    .await?;
    Ok(json!(articles))
}
