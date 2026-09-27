use axum::{
    extract::{Json, Path, Query, State},
    http::StatusCode,
};
use loco_rs::prelude::*;
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

#[derive(Deserialize)]
struct Envelope<T> {
    article: T,
}

#[derive(Deserialize)]
struct NewArticle {
    #[serde(default)]
    title: String,
    #[serde(default)]
    description: String,
    #[serde(default)]
    body: String,
    #[serde(default, rename = "tagList")]
    tag_list: Vec<String>,
}

pub async fn find(ctx: &AppContext, slug: &str) -> std::result::Result<articles::Model, ApiError> {
    articles::Model::by_slug(&ctx.db, slug)
        .await?
        .ok_or(ApiError::missing("article"))
}

async fn single(
    ctx: &AppContext,
    article: &articles::Model,
    viewer: Option<&users::Model>,
    status: StatusCode,
) -> ApiResult {
    let article = ArticleView::load(&ctx.db, article, viewer, true).await?;
    Ok(api::json_response(status, json!({"article": article})))
}

async fn list_response(
    ctx: &AppContext,
    viewer: Option<&users::Model>,
    query: ListQuery,
    feed: bool,
) -> ApiResult {
    let author = if let Some(name) = query.author.as_deref() {
        match users::Model::by_username(&ctx.db, name).await? {
            Some(user) => Some(user.id),
            None => {
                return Ok(api::json_response(
                    StatusCode::OK,
                    json!({"articles": [], "articlesCount": 0}),
                ))
            }
        }
    } else {
        None
    };
    let favorited = if let Some(name) = query.favorited.as_deref() {
        match users::Model::by_username(&ctx.db, name).await? {
            Some(user) => Some(user.id),
            None => {
                return Ok(api::json_response(
                    StatusCode::OK,
                    json!({"articles": [], "articlesCount": 0}),
                ))
            }
        }
    } else {
        None
    };
    let (articles, count) = articles::Model::list(
        &ctx.db,
        author,
        favorited,
        query.tag.as_deref(),
        if feed { viewer.map(|u| u.id) } else { None },
        query.limit.unwrap_or(20),
        query.offset.unwrap_or(0),
    )
    .await?;
    let mut views = Vec::new();
    for article in &articles {
        views.push(ArticleView::load(&ctx.db, article, viewer, false).await?);
    }
    Ok(api::json_response(
        StatusCode::OK,
        json!({"articles": views, "articlesCount": count}),
    ))
}

#[debug_handler]
async fn list(
    OptionalViewer(viewer): OptionalViewer,
    State(ctx): State<AppContext>,
    Query(query): Query<ListQuery>,
) -> ApiResult {
    list_response(&ctx, viewer.as_ref(), query, false).await
}

#[debug_handler]
async fn feed(
    Viewer(viewer): Viewer,
    State(ctx): State<AppContext>,
    Query(query): Query<ListQuery>,
) -> ApiResult {
    list_response(&ctx, Some(&viewer), query, true).await
}

#[debug_handler]
async fn show(
    Path(slug): Path<String>,
    OptionalViewer(viewer): OptionalViewer,
    State(ctx): State<AppContext>,
) -> ApiResult {
    let article = find(&ctx, &slug).await?;
    single(&ctx, &article, viewer.as_ref(), StatusCode::OK).await
}

#[debug_handler]
async fn create(
    Viewer(viewer): Viewer,
    State(ctx): State<AppContext>,
    Json(Envelope { article }): Json<Envelope<NewArticle>>,
) -> ApiResult {
    api::required(&article.title, "title")?;
    api::required(&article.description, "description")?;
    api::required(&article.body, "body")?;
    let article = articles::Model::create(
        &ctx.db,
        viewer.id,
        article.title,
        article.description,
        article.body,
        article.tag_list,
    )
    .await?;
    single(&ctx, &article, Some(&viewer), StatusCode::CREATED).await
}

fn changed_text(
    changes: &Value,
    field: &'static str,
) -> std::result::Result<Option<String>, ApiError> {
    changes
        .get(field)
        .map(|value| {
            let text = value.as_str().ok_or(ApiError::blank(field))?;
            api::required(text, field)?;
            Ok(text.to_owned())
        })
        .transpose()
}

#[debug_handler]
async fn update(
    Path(slug): Path<String>,
    Viewer(viewer): Viewer,
    State(ctx): State<AppContext>,
    Json(Envelope { article: changes }): Json<Envelope<Value>>,
) -> ApiResult {
    let article = find(&ctx, &slug).await?;
    if article.author_id != viewer.id {
        return Err(ApiError::forbidden("article"));
    }
    let mut active = article.into_active_model();
    if let Some(title) = changed_text(&changes, "title")? {
        active.slug = Set(articles::Model::slug_for(&title));
        active.title = Set(title);
    }
    if let Some(description) = changed_text(&changes, "description")? {
        active.description = Set(description);
    }
    if let Some(body) = changed_text(&changes, "body")? {
        active.body = Set(body);
    }
    if let Some(tags) = changes.get("tagList") {
        let tags: Vec<String> =
            serde_json::from_value(tags.clone()).map_err(|_| ApiError::invalid("tagList"))?;
        active = active.replace_tags(tags);
    }
    let article = active.update(&ctx.db).await?;
    single(&ctx, &article, Some(&viewer), StatusCode::OK).await
}

#[debug_handler]
async fn remove(
    Path(slug): Path<String>,
    Viewer(viewer): Viewer,
    State(ctx): State<AppContext>,
) -> ApiResult {
    let article = find(&ctx, &slug).await?;
    if article.author_id != viewer.id {
        return Err(ApiError::forbidden("article"));
    }
    article.delete(&ctx.db).await?;
    Ok(StatusCode::NO_CONTENT.into_response())
}

#[debug_handler]
async fn favorite(
    Path(slug): Path<String>,
    Viewer(viewer): Viewer,
    State(ctx): State<AppContext>,
) -> ApiResult {
    let article = find(&ctx, &slug).await?;
    favorites::Model::set(&ctx.db, viewer.id, article.id, true).await?;
    single(&ctx, &article, Some(&viewer), StatusCode::OK).await
}

#[debug_handler]
async fn unfavorite(
    Path(slug): Path<String>,
    Viewer(viewer): Viewer,
    State(ctx): State<AppContext>,
) -> ApiResult {
    let article = find(&ctx, &slug).await?;
    favorites::Model::set(&ctx.db, viewer.id, article.id, false).await?;
    single(&ctx, &article, Some(&viewer), StatusCode::OK).await
}

#[debug_handler]
async fn tags(State(ctx): State<AppContext>) -> ApiResult {
    let tags = articles::Model::all_tags(&ctx.db).await?;
    Ok(api::json_response(StatusCode::OK, json!({"tags": tags})))
}

pub fn routes() -> Routes {
    Routes::new()
        .prefix("/api")
        .add("/articles", get(list))
        .add("/articles", post(create))
        .add("/articles/feed", get(feed))
        .add("/articles/{slug}", get(show))
        .add("/articles/{slug}", put(update))
        .add("/articles/{slug}", delete(remove))
        .add("/articles/{slug}/favorite", post(favorite))
        .add("/articles/{slug}/favorite", delete(unfavorite))
        .add("/tags", get(tags))
}
