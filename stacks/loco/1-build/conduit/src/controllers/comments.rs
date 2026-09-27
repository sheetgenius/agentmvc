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
    let article = articles::find(&ctx, &slug).await?;
    let comments = comments::Model::for_article(&ctx.db, article.id).await?;
    let mut views = Vec::new();
    for comment in &comments {
        views.push(CommentView::load(&ctx.db, comment, viewer.as_ref()).await?);
    }
    Ok(api::json_response(
        StatusCode::OK,
        json!({"comments": views}),
    ))
}

#[debug_handler]
async fn create(
    Path(slug): Path<String>,
    Viewer(viewer): Viewer,
    State(ctx): State<AppContext>,
    Json(Envelope { comment }): Json<Envelope<NewComment>>,
) -> ApiResult {
    let article = articles::find(&ctx, &slug).await?;
    api::required(&comment.body, "body")?;
    let comment = comments::Model::add(&ctx.db, article.id, viewer.id, comment.body).await?;
    let view = CommentView::load(&ctx.db, &comment, Some(&viewer)).await?;
    Ok(api::json_response(
        StatusCode::CREATED,
        json!({"comment": view}),
    ))
}

#[debug_handler]
async fn remove(
    Path((slug, id)): Path<(String, i64)>,
    Viewer(viewer): Viewer,
    State(ctx): State<AppContext>,
) -> ApiResult {
    let article = articles::find(&ctx, &slug).await?;
    let comment = comments::Entity::find_by_id(id)
        .one(&ctx.db)
        .await?
        .filter(|comment| comment.article_id == article.id)
        .ok_or(ApiError::missing("comment"))?;
    if comment.author_id != viewer.id {
        return Err(ApiError::forbidden("comment"));
    }
    comment.delete(&ctx.db).await?;
    Ok(StatusCode::NO_CONTENT.into_response())
}

pub fn routes() -> Routes {
    Routes::new()
        .prefix("/api/articles/{slug}/comments")
        .add("/", get(list))
        .add("/", post(create))
        .add("/{id}", delete(remove))
}
