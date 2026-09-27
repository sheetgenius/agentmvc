# loco · comprehension after-6-polish

| | |
| --- | --- |
| Codex session | `01a0e147-afb2-7cb0-a751-2d40af521f69` |
| Started, finished (UTC) | 2026-09-27T05:12:46Z, 2026-09-27T05:14:13Z (87 s) |
| Exit code | 0 |
| Agent tokens (uncached input + output) | 25,218 |
| Prompt | [steps/comprehension.md](../../../steps/comprehension.md) |
| Raw events | [comprehension-after-6-polish.jsonl](comprehension-after-6-polish.jsonl) |

Outputs longer than 40 lines are cut here; the `.jsonl` file next to this one has them in full.

**Agent:**

I’ll trace the routes, models, and response helpers for these rules. I’ll only read files in this directory and won’t run the backend.

```sh
$ /bin/zsh -lc "rg --files -g 'AGENTS.md' -g '"'!node_modules'"' -g '"'!vendor'"' -g '"'!dist'"' -g '"'!build'"' -g '"'!coverage'"' -g '"'!*.lock'"' -g '"'!package-lock.json'"' | head -80"
```

```sh
$ /bin/zsh -lc "rg --files -g '"'!node_modules'"' -g '"'!vendor'"' -g '"'!dist'"' -g '"'!build'"' -g '"'!coverage'"' -g '"'!*.lock'"' -g '"'!package-lock.json'"'"
```
<details><summary>output (exit 0)</summary>

```
conduit/src/views/realworld.rs
conduit/src/views/mod.rs
conduit/src/controllers/api.rs
conduit/src/controllers/articles.rs
conduit/src/controllers/comments.rs
conduit/src/controllers/mod.rs
conduit/src/controllers/profiles.rs
conduit/src/controllers/users.rs
conduit/src/app.rs
conduit/src/models/articles.rs
conduit/src/models/favorites.rs
conduit/src/models/comments.rs
conduit/src/models/mod.rs
conduit/src/models/users.rs
conduit/src/models/follows.rs
conduit/src/lib.rs
conduit/src/bin/main.rs
conduit/migration/src/m20260927_000002_drafts.rs
conduit/migration/src/m20260927_000003_tags_index.rs
conduit/migration/src/lib.rs
conduit/migration/src/m20260927_000001_conduit.rs
conduit/migration/Cargo.toml
conduit/config/development.yaml
conduit/config/production.yaml
conduit/Cargo.toml
```

</details>

```sh
$ /bin/zsh -lc "rg -n 'slug|favoritesCount|favorites_count|tagList|tag_list|feed|limit|register|delete|bio|jwt|token|password|Already|Conflict|Unauthor|Forbidden' conduit/src/controllers conduit/src/models conduit/src/views conduit/migration/src/m20260927_000001_conduit.rs"
```
<details><summary>output (exit 0)</summary>

```
conduit/migration/src/m20260927_000001_conduit.rs:17:                ("password", ColType::String),
conduit/migration/src/m20260927_000001_conduit.rs:19:                ("bio", ColType::TextNull),
conduit/migration/src/m20260927_000001_conduit.rs:30:                ("slug", ColType::StringUniq),
conduit/migration/src/m20260927_000001_conduit.rs:34:                ("tag_list", ColType::Json),
conduit/src/views/realworld.rs:12:    pub token: String,
conduit/src/views/realworld.rs:14:    pub bio: Option<String>,
conduit/src/views/realworld.rs:19:    pub fn new(user: &users::Model, token: String) -> Self {
conduit/src/views/realworld.rs:22:            token,
conduit/src/views/realworld.rs:24:            bio: user.bio.clone(),
conduit/src/views/realworld.rs:33:    pub bio: Option<String>,
conduit/src/views/realworld.rs:42:            bio: user.bio.clone(),
conduit/src/views/realworld.rs:65:    pub slug: String,
conduit/src/views/realworld.rs:70:    pub tag_list: Vec<String>,
conduit/src/views/realworld.rs:77:    pub favorites_count: u64,
conduit/src/views/realworld.rs:93:        favorites_count: u64,
conduit/src/views/realworld.rs:97:            slug: article.slug.clone(),
conduit/src/views/realworld.rs:101:            tag_list: article.tags(),
conduit/src/views/realworld.rs:108:            favorites_count,
conduit/src/views/realworld.rs:204:        let favorites_count = favorites::Model::count(db, article.id).await?;
conduit/src/views/realworld.rs:215:            favorites_count,
conduit/src/models/articles.rs:29:        limit: usize,
conduit/src/models/articles.rs:35:            .limit(limit as u64)
conduit/src/models/articles.rs:41:    fn with_slug(slug: &str) -> Select<Entity> {
conduit/src/models/articles.rs:42:        Entity::find().filter(articles::Column::Slug.eq(slug))
conduit/src/models/articles.rs:49:    pub async fn by_slug<C: ConnectionTrait>(
conduit/src/models/articles.rs:51:        slug: &str,
conduit/src/models/articles.rs:53:        Self::with_slug(slug).one(db).await
conduit/src/models/articles.rs:56:    pub async fn by_slug_for_update(
conduit/src/models/articles.rs:58:        slug: &str,
conduit/src/models/articles.rs:60:        Self::with_slug(slug).lock_exclusive().one(db).await
conduit/src/models/articles.rs:74:            slug: Set(Self::slug_for(&title)),
conduit/src/models/articles.rs:78:            tag_list: Set(serde_json::json!(tags)),
conduit/src/models/articles.rs:89:        serde_json::from_value(self.tag_list.clone()).unwrap_or_default()
conduit/src/models/articles.rs:109:    pub fn slug_for(title: &str) -> String {
conduit/src/models/articles.rs:110:        format!("{}-{}", slug::slugify(title), Uuid::new_v4().simple())
conduit/src/models/articles.rs:118:        feed: Option<i64>,
conduit/src/models/articles.rs:119:        limit: usize,
conduit/src/models/articles.rs:145:        if let Some(user_id) = feed {
conduit/src/models/articles.rs:156:        Self::page(db, query, limit, offset).await
conduit/src/models/articles.rs:162:        limit: usize,
[... 91 more lines]
```

</details>

```sh
$ /bin/zsh -lc "sed -n '1,220p' conduit/src/models/articles.rs"
```
<details><summary>output (exit 0)</summary>

```
use std::collections::BTreeSet;

use chrono::Utc;
use loco_rs::prelude::*;
use sea_orm::sea_query::{extension::postgres::PgExpr, Expr};
use sea_orm::{DatabaseTransaction, QueryTrait, Select};
use serde_json::{json, Value};
use uuid::Uuid;

pub use super::_entities::articles::{self, ActiveModel, Entity, Model};

#[async_trait::async_trait]
impl ActiveModelBehavior for ActiveModel {
    async fn before_save<C>(mut self, _db: &C, insert: bool) -> std::result::Result<Self, DbErr>
    where
        C: ConnectionTrait,
    {
        if !insert {
            self.updated_at = Set(Utc::now().into());
        }
        Ok(self)
    }
}

impl Model {
    async fn page(
        db: &DatabaseConnection,
        query: Select<Entity>,
        limit: usize,
        offset: usize,
    ) -> std::result::Result<(Vec<Self>, usize), DbErr> {
        let count = query.clone().count(db).await? as usize;
        let articles = query
            .offset(offset as u64)
            .limit(limit as u64)
            .all(db)
            .await?;
        Ok((articles, count))
    }

[... 150 more lines]
```

</details>

```sh
$ /bin/zsh -lc "sed -n '1,380p' conduit/src/controllers/articles.rs"
```
<details><summary>output (exit 0)</summary>

```
use axum::{
    extract::{Json, Path, Query, State},
    http::StatusCode,
};
use loco_rs::prelude::*;
use sea_orm::DatabaseTransaction;
use serde::Deserialize;
use serde_json::{json, Value};

use crate::{
    controllers::api::{self, ApiError, ApiResult, OptionalViewer, Viewer},
    models::{articles, favorites, users},
    views::realworld::ArticleView,
};

#[derive(Default, Deserialize)]
pub struct ListQuery {
    tag: Option<String>,
    author: Option<String>,
    favorited: Option<String>,
    limit: Option<usize>,
    offset: Option<usize>,
}

impl ListQuery {
    fn page(&self) -> (usize, usize) {
        (self.limit.unwrap_or(20), self.offset.unwrap_or(0))
    }
}

#[derive(Deserialize)]
struct Envelope<T> {
    article: T,
}

#[derive(Deserialize)]
struct NewArticle {
    #[serde(default)]
    title: String,
    #[serde(default)]
[... 301 more lines]
```

</details>

```sh
$ /bin/zsh -lc "sed -n '1,220p' conduit/src/controllers/users.rs"
```
<details><summary>output (exit 0)</summary>

```
use axum::{
    extract::{Json, State},
    http::StatusCode,
};
use governor::{DefaultKeyedRateLimiter, Quota, RateLimiter};
use loco_rs::prelude::*;
use serde::Deserialize;
use serde_json::{json, Value};
use std::{
    num::NonZeroU32,
    sync::{
        atomic::{AtomicUsize, Ordering},
        LazyLock,
    },
};

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
[... 149 more lines]
```

</details>

```sh
$ /bin/zsh -lc "sed -n '1,240p' conduit/src/controllers/api.rs"
```
<details><summary>output (exit 0)</summary>

```
use axum::{
    extract::FromRequestParts,
    http::{request::Parts, StatusCode},
    response::{IntoResponse, Response},
    Json,
};
use loco_rs::{app::AppContext, auth::jwt};
use sea_orm::DbErr;
use serde::Serialize;
use serde_json::json;

use crate::models::users;

pub type ApiResult = std::result::Result<Response, ApiError>;

pub struct ApiError {
    status: StatusCode,
    field: &'static str,
    message: &'static str,
}

impl ApiError {
    pub fn new(status: StatusCode, field: &'static str, message: &'static str) -> Self {
        Self {
            status,
            field,
            message,
        }
    }
    pub fn blank(field: &'static str) -> Self {
        Self::new(StatusCode::UNPROCESSABLE_ENTITY, field, "can't be blank")
    }
    pub fn invalid(field: &'static str) -> Self {
        Self::new(StatusCode::UNPROCESSABLE_ENTITY, field, "is invalid")
    }
    pub fn taken(field: &'static str) -> Self {
        Self::new(StatusCode::CONFLICT, field, "has already been taken")
    }
    pub fn missing(field: &'static str) -> Self {
        Self::new(StatusCode::NOT_FOUND, field, "not found")
[... 89 more lines]
```

</details>

**Agent:**

The route code confirms several behaviors already: title updates regenerate the slug, registration checks both unique fields before insertion, and article lists default to 20 items. I’ll check the model queries and response code next for feed ordering, tags, favorites, and error bodies.

```sh
$ /bin/zsh -lc "sed -n '1,150p' conduit/src/models/favorites.rs"
```
<details><summary>output (exit 0)</summary>

```
pub use super::_entities::favorites::{self, ActiveModel, Column, Entity, Model};
use loco_rs::prelude::*;
impl ActiveModelBehavior for ActiveModel {}

impl Model {
    pub async fn count(
        db: &DatabaseConnection,
        article_id: i64,
    ) -> std::result::Result<u64, DbErr> {
        Entity::find()
            .filter(favorites::Column::ArticleId.eq(article_id))
            .count(db)
            .await
    }

    pub async fn is_favorited(
        db: &DatabaseConnection,
        user_id: i64,
        article_id: i64,
    ) -> std::result::Result<bool, DbErr> {
        Ok(Entity::find()
            .filter(favorites::Column::UserId.eq(user_id))
            .filter(favorites::Column::ArticleId.eq(article_id))
            .one(db)
            .await?
            .is_some())
    }

    pub async fn set(
        db: &DatabaseConnection,
        user_id: i64,
        article_id: i64,
        favorited: bool,
    ) -> std::result::Result<(), DbErr> {
        if favorited {
            Entity::insert(ActiveModel {
                user_id: Set(user_id),
                article_id: Set(article_id),
                ..Default::default()
            })
[... 13 more lines]
```

</details>

```sh
$ /bin/zsh -lc "sed -n '1,250p' conduit/src/views/realworld.rs"
```
<details><summary>output (exit 0)</summary>

```
use std::collections::{HashMap, HashSet};

use loco_rs::prelude::*;
use sea_orm::FromQueryResult;
use serde::Serialize;

use crate::models::{articles, comments, favorites, follows, users};

#[derive(Serialize)]
pub struct UserView {
    pub email: String,
    pub token: String,
    pub username: String,
    pub bio: Option<String>,
    pub image: Option<String>,
}

impl UserView {
    pub fn new(user: &users::Model, token: String) -> Self {
        Self {
            email: user.email.clone(),
            token,
            username: user.username.clone(),
            bio: user.bio.clone(),
            image: user.image.clone(),
        }
    }
}

#[derive(Serialize)]
pub struct ProfileView {
    pub username: String,
    pub bio: Option<String>,
    pub image: Option<String>,
    pub following: bool,
}

impl ProfileView {
    fn new(user: &users::Model, following: bool) -> Self {
        Self {
[... 209 more lines]
```

</details>

```sh
$ /bin/zsh -lc "sed -n '1,150p' conduit/src/controllers/comments.rs"
```
<details><summary>output (exit 0)</summary>

```
use axum::{
    extract::{Json, Path, State},
    http::StatusCode,
    response::IntoResponse,
};
use loco_rs::prelude::*;
use serde::Deserialize;
use serde_json::json;

use crate::{
    controllers::{
        api::{self, ApiError, ApiResult, OptionalViewer, Viewer},
        articles,
    },
    models::comments,
    views::realworld::CommentView,
};

#[derive(Deserialize)]
struct Envelope<T> {
    comment: T,
}

#[derive(Deserialize)]
struct NewComment {
    #[serde(default)]
    body: String,
}

#[debug_handler]
async fn list(
    Path(slug): Path<String>,
    OptionalViewer(viewer): OptionalViewer,
    State(ctx): State<AppContext>,
) -> ApiResult {
    let article = articles::find(&ctx, &slug, viewer.as_ref().map(|user| user.id)).await?;
    let comments = comments::Model::for_article(&ctx.db, article.id).await?;
    let mut views = Vec::new();
    for comment in &comments {
        views.push(CommentView::load(&ctx.db, comment, viewer.as_ref()).await?);
[... 52 more lines]
```

</details>

```sh
$ /bin/zsh -lc "sed -n '1,150p' conduit/src/models/users.rs"
```
<details><summary>output (exit 0)</summary>

```
use loco_rs::{auth::jwt, hash, prelude::*};
use serde_json::Map;
use uuid::Uuid;

pub use super::_entities::users::{self, ActiveModel, Column, Entity, Model};

#[async_trait::async_trait]
impl ActiveModelBehavior for ActiveModel {
    async fn before_save<C>(mut self, _db: &C, insert: bool) -> std::result::Result<Self, DbErr>
    where
        C: ConnectionTrait,
    {
        if insert {
            self.pid = Set(Uuid::new_v4());
        }
        Ok(self)
    }
}

impl Model {
    pub async fn by_username(
        db: &DatabaseConnection,
        username: &str,
    ) -> std::result::Result<Option<Self>, DbErr> {
        Entity::find()
            .filter(users::Column::Username.eq(username))
            .one(db)
            .await
    }

    pub async fn by_email(
        db: &DatabaseConnection,
        email: &str,
    ) -> std::result::Result<Option<Self>, DbErr> {
        Entity::find()
            .filter(users::Column::Email.eq(email))
            .one(db)
            .await
    }

[... 51 more lines]
```

</details>

```sh
$ /bin/zsh -lc "sed -n '1,130p' conduit/src/models/comments.rs"
```
<details><summary>output (exit 0)</summary>

```
use loco_rs::prelude::*;

pub use super::_entities::comments::{self, ActiveModel, Column, Entity, Model};

impl ActiveModelBehavior for ActiveModel {}

impl Model {
    pub async fn for_article(
        db: &DatabaseConnection,
        article_id: i64,
    ) -> std::result::Result<Vec<Self>, DbErr> {
        Entity::find()
            .filter(comments::Column::ArticleId.eq(article_id))
            .order_by_asc(comments::Column::Id)
            .all(db)
            .await
    }

    pub async fn add(
        db: &DatabaseConnection,
        article_id: i64,
        author_id: i64,
        body: String,
    ) -> std::result::Result<Self, DbErr> {
        ActiveModel {
            article_id: Set(article_id),
            author_id: Set(author_id),
            body: Set(body),
            ..Default::default()
        }
        .insert(db)
        .await
    }
}
```

</details>

```sh
$ /bin/zsh -lc "sed -n '1,130p' conduit/migration/src/m20260927_000001_conduit.rs"
```
<details><summary>output (exit 0)</summary>

```
use loco_rs::schema::*;
use sea_orm_migration::prelude::*;

#[derive(DeriveMigrationName)]
pub struct Migration;

#[async_trait::async_trait]
impl MigrationTrait for Migration {
    async fn up(&self, m: &SchemaManager) -> Result<(), DbErr> {
        create_table(
            m,
            "users",
            &[
                ("id", ColType::PkAuto),
                ("pid", ColType::UuidUniq),
                ("email", ColType::StringUniq),
                ("password", ColType::String),
                ("username", ColType::StringUniq),
                ("bio", ColType::TextNull),
                ("image", ColType::StringNull),
            ],
            &[],
        )
        .await?;
        create_table(
            m,
            "articles",
            &[
                ("id", ColType::PkAuto),
                ("slug", ColType::StringUniq),
                ("title", ColType::String),
                ("description", ColType::Text),
                ("body", ColType::Text),
                ("tag_list", ColType::Json),
            ],
            &[("users", "author_id")],
        )
        .await?;
        create_table(
            m,
[... 49 more lines]
```

</details>

```sh
$ /bin/zsh -lc "rg -n -C 3 'jwt|expiration|secret|hash|bcrypt|argon|password' conduit/config conduit/Cargo.toml conduit/src"
```
<details><summary>output (exit 0)</summary>

```
conduit/config/development.yaml-19-  max_connections: 10
conduit/config/development.yaml-20-  auto_migrate: true
conduit/config/development.yaml-21-auth:
conduit/config/development.yaml:22:  jwt:
conduit/config/development.yaml:23:    secret: <%= get_env(name="JWT_SECRET", default="LRKkNeVr4liTgqOglDoA") %>
conduit/config/development.yaml:24:    expiration: 604800
--
conduit/config/production.yaml-19-  min_connections: 1
conduit/config/production.yaml-20-  max_connections: 10
conduit/config/production.yaml-21-auth:
conduit/config/production.yaml:22:  jwt:
conduit/config/production.yaml:23:    secret: <%= get_env(name="SECRET_KEY_BASE") %>
conduit/config/production.yaml:24:    expiration: 604800
--
conduit/src/controllers/api.rs-4-    response::{IntoResponse, Response},
conduit/src/controllers/api.rs-5-    Json,
conduit/src/controllers/api.rs-6-};
conduit/src/controllers/api.rs:7:use loco_rs::{app::AppContext, auth::jwt};
conduit/src/controllers/api.rs-8-use sea_orm::DbErr;
conduit/src/controllers/api.rs-9-use serde::Serialize;
conduit/src/controllers/api.rs-10-use serde_json::json;
--
conduit/src/controllers/api.rs-102-            ))?;
conduit/src/controllers/api.rs-103-        let config = ctx
conduit/src/controllers/api.rs-104-            .config
conduit/src/controllers/api.rs:105:            .get_jwt_config()
conduit/src/controllers/api.rs-106-            .map_err(|_| ApiError::new(StatusCode::INTERNAL_SERVER_ERROR, "server", "error"))?;
conduit/src/controllers/api.rs:107:        let claims = jwt::JWT::new(&config.secret)
conduit/src/controllers/api.rs-108-            .validate(token)
conduit/src/controllers/api.rs-109-            .map_err(|_| ApiError::new(StatusCode::UNAUTHORIZED, "token", "is invalid"))?;
conduit/src/controllers/api.rs-110-        let user = users::Model::by_pid(&ctx.db, &claims.claims.pid).await?;
--
conduit/src/models/users.rs:1:use loco_rs::{auth::jwt, hash, prelude::*};
conduit/src/models/users.rs-2-use serde_json::Map;
conduit/src/models/users.rs-3-use uuid::Uuid;
conduit/src/models/users.rs-4-
--
conduit/src/models/users.rs-55-        db: &DatabaseConnection,
conduit/src/models/users.rs-56-        username: String,
conduit/src/models/users.rs-57-        email: String,
[... 105 more lines]
```

</details>

```sh
$ /bin/zsh -lc "sed -n '1,180p' conduit/Cargo.toml"
```
<details><summary>output (exit 0)</summary>

```
[workspace]

[package]
name = "conduit"
version = "0.1.0"
edition = "2021"
publish = false

[workspace.dependencies]
loco-rs = "1.2"

[dependencies]
loco-rs = { workspace = true }
migration = { path = "migration" }
sea-orm = { version = "2.0", features = ["sqlx-postgres", "runtime-tokio-rustls", "macros"] }
axum = "0.8"
async-trait = "0.1"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
chrono = "0.4"
uuid = { version = "1.6", features = ["v4"] }
slug = "0.1"
tokio = { version = "1.45", default-features = false, features = ["rt-multi-thread"] }
governor = { version = "0.10", default-features = false, features = ["std", "dashmap"] }

[[bin]]
name = "conduit-cli"
path = "src/bin/main.rs"
```

</details>

**Agent:**

## 1
Answer: The slug is the slugified title followed by a hyphen and a new UUID without separators. Supplying a title in an update generates a new slug, even if the title text is unchanged; omitting the title leaves the slug alone.
Where: `conduit/src/models/articles.rs` — `Model::slug_for`, `Model::create`; `conduit/src/controllers/articles.rs` — `update`
Confidence: high

## 2
Answer: An existing username or email produces HTTP 409 with `{"errors":{"username":["has already been taken"]}}` or `{"errors":{"email":["has already been taken"]}}`. The username check runs first.
Where: `conduit/src/controllers/users.rs` — `register`; `conduit/src/controllers/api.rs` — `ApiError::taken`, `IntoResponse for ApiError`
Confidence: high

## 3
Answer: The feed requires authentication and lists published articles by users the viewer follows, ordered by descending article ID. Supplied `author`, `favorited`, and `tag` filters also apply.
Where: `conduit/src/controllers/articles.rs` — `feed`, `list_response`; `conduit/src/models/articles.rs` — `Model::list`
Confidence: high

## 4
Answer: `favoritesCount` is the number of rows in `favorites` for that article. List responses calculate counts in a grouped query and use zero when an article has no matching rows.
Where: `conduit/src/views/realworld.rs` — `ArticleView::load`, `ArticleView::load_many`; `conduit/src/models/favorites.rs` — `Model::count`
Confidence: high

## 5
Answer: Deleting another user's comment returns HTTP 403 with `{"errors":{"comment":["forbidden"]}}`.
Where: `conduit/src/controllers/comments.rs` — `remove`; `conduit/src/controllers/api.rs` — `ApiError::forbidden`, `IntoResponse for ApiError`
Confidence: high

## 6
Answer: An empty string for `bio` is converted to `None` and saved as a null value.
Where: `conduit/src/controllers/users.rs` — `update`
Confidence: high

## 7
Answer: Each article stores its tags as a JSON array in the `tag_list` column. `GET /api/tags` collects tags from published articles into a `BTreeSet`, so its `tags` array is sorted and contains no duplicates.
Where: `conduit/migration/src/m20260927_000001_conduit.rs` — `Migration::up`; `conduit/src/models/articles.rs` — `Model::create`, `Model::all_tags`; `conduit/src/controllers/articles.rs` — `tags`
Confidence: high

## 8
Answer: The default `limit` is 20. The code applies no maximum to a supplied `limit`.
Where: `conduit/src/controllers/articles.rs` — `ListQuery::page`; `conduit/src/models/articles.rs` — `Model::page`
Confidence: high

## 9
Answer: The backend creates a JWT using Loco's JWT helper and the configured secret, passing the user's UUID `pid` and an empty extra-claims map. Both configuration files set its expiration to `604800` seconds, or seven days.
Where: `conduit/src/models/users.rs` — `Model::token`; `conduit/src/controllers/users.rs` — `response`; `conduit/config/development.yaml`, `conduit/config/production.yaml` — `auth.jwt`
Confidence: medium

## 10
Answer: `owned` rejects an article whose `author_id` differs from the viewer's ID. The update path calls it through `find_owned_for_update`, and the delete path calls it directly.
Where: `conduit/src/controllers/articles.rs` — `owned`, `find_owned_for_update`, `update`, `remove`
Confidence: high

## 11
Answer: Omitting `tagList` leaves the stored tags unchanged. Sending `"tagList": null` fails deserialization as `Vec<String>` and returns HTTP 422 with `{"errors":{"tagList":["is invalid"]}}`.
Where: `conduit/src/controllers/articles.rs` — `update`; `conduit/src/controllers/api.rs` — `ApiError::invalid`, `IntoResponse for ApiError`
Confidence: high

## 12
Answer: Passwords are stored as hashes returned by `loco_rs::hash::hash_password`, both at registration and when changed; verification uses `loco_rs::hash::verify_password`. This directory does not specify the hash algorithm used inside Loco.
Where: `conduit/src/models/users.rs` — `Model::register`, `ActiveModel::change_password`, `Model::verify_password`
Confidence: high

Files read: 13

