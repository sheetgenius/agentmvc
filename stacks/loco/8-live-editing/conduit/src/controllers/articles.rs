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
    description: String,
    #[serde(default)]
    body: String,
    #[serde(default, rename = "tagList")]
    tag_list: Vec<String>,
    #[serde(default = "published_status")]
    status: Value,
}

fn published_status() -> Value {
    json!("published")
}

fn visible(
    article: Option<articles::Model>,
    viewer_id: Option<i64>,
) -> std::result::Result<articles::Model, ApiError> {
    let article = article.ok_or(ApiError::missing("article"))?;
    if article.is_draft() && Some(article.author_id) != viewer_id {
        return Err(ApiError::missing("article"));
    }
    Ok(article)
}

fn owned(
    article: articles::Model,
    viewer_id: i64,
) -> std::result::Result<articles::Model, ApiError> {
    if article.author_id != viewer_id {
        return Err(ApiError::forbidden("article"));
    }
    Ok(article)
}

pub async fn find(
    ctx: &AppContext,
    slug: &str,
    viewer_id: Option<i64>,
) -> std::result::Result<articles::Model, ApiError> {
    visible(articles::Model::by_slug(&ctx.db, slug).await?, viewer_id)
}

pub(crate) async fn find_owned_for_update(
    txn: &DatabaseTransaction,
    slug: &str,
    viewer_id: i64,
) -> std::result::Result<articles::Model, ApiError> {
    let article = articles::Model::by_slug_for_update(txn, slug).await?;
    owned(visible(article, Some(viewer_id))?, viewer_id)
}

pub fn interactable(article: &articles::Model) -> std::result::Result<(), ApiError> {
    if article.is_draft() {
        Err(ApiError::new(
            StatusCode::UNPROCESSABLE_ENTITY,
            "article",
            "is a draft",
        ))
    } else {
        Ok(())
    }
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
    let (limit, offset) = query.page();
    let (articles, count) = articles::Model::list(
        &ctx.db,
        query.author.as_deref(),
        query.favorited.as_deref(),
        query.tag.as_deref(),
        if feed { viewer.map(|u| u.id) } else { None },
        limit,
        offset,
    )
    .await?;
    many(ctx, &articles, count, viewer).await
}

async fn many(
    ctx: &AppContext,
    articles: &[articles::Model],
    count: usize,
    viewer: Option<&users::Model>,
) -> ApiResult {
    let views = ArticleView::load_many(&ctx.db, articles, viewer).await?;
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
async fn drafts(
    Viewer(viewer): Viewer,
    State(ctx): State<AppContext>,
    Query(query): Query<ListQuery>,
) -> ApiResult {
    let (limit, offset) = query.page();
    let (articles, count) = articles::Model::drafts(&ctx.db, viewer.id, limit, offset).await?;
    many(&ctx, &articles, count, Some(&viewer)).await
}

#[debug_handler]
async fn show(
    Path(slug): Path<String>,
    OptionalViewer(viewer): OptionalViewer,
    State(ctx): State<AppContext>,
) -> ApiResult {
    let article = find(&ctx, &slug, viewer.as_ref().map(|user| user.id)).await?;
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
    let status = match article.status.as_str() {
        Some("draft") => "draft",
        Some("published") => "published",
        _ => return Err(ApiError::invalid("status")),
    };
    let article = articles::Model::create(
        &ctx.db,
        viewer.id,
        article.title,
        article.description,
        article.body,
        article.tag_list,
        status.to_owned(),
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
    let txn = ctx.db.begin().await?;
    let article = find_owned_for_update(&txn, &slug, viewer.id).await?;
    if let Some(revision) = changes.get("revision") {
        if !revision.is_i64() && !revision.is_u64() {
            return Err(ApiError::invalid("revision"));
        }
        if *revision != json!(article.revision) {
            let current = ArticleView::load(&ctx.db, &article, Some(&viewer), true).await?;
            return Ok(api::json_response(
                StatusCode::CONFLICT,
                json!({"errors": {"revision": ["is stale"]}, "article": current}),
            ));
        }
    }
    let mut active = article.revised();
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
    let article = active.update(&txn).await?;
    txn.commit().await?;
    crate::models::live_rooms::Hub::article_saved(&ctx, &article).await?;
    single(&ctx, &article, Some(&viewer), StatusCode::OK).await
}

#[debug_handler]
async fn remove(
    Path(slug): Path<String>,
    Viewer(viewer): Viewer,
    State(ctx): State<AppContext>,
) -> ApiResult {
    let article = owned(find(&ctx, &slug, Some(viewer.id)).await?, viewer.id)?;
    let share = crate::models::article_shares::Model::for_article(&ctx.db, article.id).await?;
    article.delete(&ctx.db).await?;
    if let Some(share) = share {
        crate::models::live_rooms::Hub::from_ctx(&ctx)
            .revoke(&share.id)
            .await;
    }
    Ok(StatusCode::NO_CONTENT.into_response())
}

#[debug_handler]
async fn publish(
    Path(slug): Path<String>,
    Viewer(viewer): Viewer,
    State(ctx): State<AppContext>,
) -> ApiResult {
    let txn = ctx.db.begin().await?;
    let article = find_owned_for_update(&txn, &slug, viewer.id).await?;
    if !article.is_draft() {
        txn.commit().await?;
        return single(&ctx, &article, Some(&viewer), StatusCode::OK).await;
    }
    let article = article.publish().update(&txn).await?;
    txn.commit().await?;
    crate::models::live_rooms::Hub::article_saved(&ctx, &article).await?;
    single(&ctx, &article, Some(&viewer), StatusCode::OK).await
}

#[debug_handler]
async fn favorite(
    Path(slug): Path<String>,
    Viewer(viewer): Viewer,
    State(ctx): State<AppContext>,
) -> ApiResult {
    let article = find(&ctx, &slug, Some(viewer.id)).await?;
    interactable(&article)?;
    favorites::Model::set(&ctx.db, viewer.id, article.id, true).await?;
    single(&ctx, &article, Some(&viewer), StatusCode::OK).await
}

#[debug_handler]
async fn unfavorite(
    Path(slug): Path<String>,
    Viewer(viewer): Viewer,
    State(ctx): State<AppContext>,
) -> ApiResult {
    let article = find(&ctx, &slug, Some(viewer.id)).await?;
    interactable(&article)?;
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
        .add("/user/drafts", get(drafts))
        .add("/articles/{slug}", get(show))
        .add("/articles/{slug}", put(update))
        .add("/articles/{slug}", delete(remove))
        .add("/articles/{slug}/publish", post(publish))
        .add("/articles/{slug}/favorite", post(favorite))
        .add("/articles/{slug}/favorite", delete(unfavorite))
        .add("/tags", get(tags))
}
