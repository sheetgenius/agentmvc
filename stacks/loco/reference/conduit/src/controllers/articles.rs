use crate::{
    controllers::{common::*, shares},
    models::realworld as db,
};
use axum::{
    http::{HeaderMap, StatusCode},
    Json,
};
use loco_rs::prelude::*;
use serde_json::{json, Value};
use std::collections::HashMap;

pub async fn visible(ctx: &AppContext, slug: &str, viewer: Option<i64>) -> Result<Value, ApiError> {
    let article = db::article_by_slug(&ctx.db, slug)
        .await?
        .ok_or_else(|| missing("article"))?;
    if article["status"] == "draft" && article["author_id"].as_i64() != viewer {
        return Err(missing("article"));
    }
    Ok(article)
}

fn owner(article: &Value, viewer: i64) -> Result<(), ApiError> {
    if article["author_id"].as_i64() == Some(viewer) {
        Ok(())
    } else {
        Err(forbidden("article"))
    }
}

fn tags(value: &Value) -> Result<Option<Vec<String>>, ApiError> {
    match value.get("tagList") {
        None => Ok(None),
        Some(Value::Array(items)) if items.iter().all(Value::is_string) => Ok(Some(
            items
                .iter()
                .filter_map(Value::as_str)
                .map(str::to_owned)
                .collect(),
        )),
        _ => Err(invalid("tagList")),
    }
}

async fn save_tags(ctx: &AppContext, article_id: i64, tags: &[String]) -> Result<(), ApiError> {
    db::exec(
        &ctx.db,
        "DELETE FROM rw_tags WHERE article_id=$1",
        vec![article_id.into()],
    )
    .await?;
    for (position, tag) in tags.iter().enumerate() {
        db::exec(
            &ctx.db,
            "INSERT INTO rw_tags(article_id,tag,position) VALUES($1,$2,$3) ON CONFLICT DO NOTHING",
            vec![
                article_id.into(),
                tag.clone().into(),
                (position as i32).into(),
            ],
        )
        .await?;
    }
    Ok(())
}

async fn create(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Json(body): Json<Value>,
) -> ApiResult {
    let viewer = required_viewer(&ctx, &headers)?;
    let article = object(&body, "article")?;
    let title = required(article, "title")?;
    let description = required(article, "description")?;
    let text = required(article, "body")?;
    let tag_list = tags(article)?.unwrap_or_default();
    let status = match article.get("status") {
        None => "published",
        Some(Value::String(value)) => value.as_str(),
        _ => return Err(invalid("status")),
    };
    if !["draft", "published"].contains(&status) {
        return Err(invalid("status"));
    }
    let slug = db::slug(title);
    let saved = db::row(&ctx.db,"WITH t AS (INSERT INTO rw_articles(author_id,slug,title,description,body,status,published_at) VALUES($1,$2,$3,$4,$5,$6,CASE WHEN $6='published' THEN now() ELSE NULL END) RETURNING id) SELECT row_to_json(t)::text data FROM t",vec![viewer.into(),slug.into(),title.into(),description.into(),text.into(),status.into()]).await?.ok_or_else(|| missing("article"))?;
    save_tags(&ctx, id(&saved), &tag_list).await?;
    Ok(respond(
        StatusCode::CREATED,
        json!({"article":db::article_view(&ctx.db,id(&saved),Some(viewer),false).await?}),
    ))
}

async fn show(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Path(slug): Path<String>,
) -> ApiResult {
    let viewer = viewer(&ctx, &headers);
    let article = visible(&ctx, &slug, viewer).await?;
    Ok(respond(
        StatusCode::OK,
        json!({"article":db::article_view(&ctx.db,id(&article),viewer,false).await?}),
    ))
}

async fn update(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Path(slug): Path<String>,
    Json(body): Json<Value>,
) -> ApiResult {
    let viewer = required_viewer(&ctx, &headers)?;
    let current = visible(&ctx, &slug, Some(viewer)).await?;
    owner(&current, viewer)?;
    let changes = object(&body, "article")?;
    let revision = match changes.get("revision") {
        Some(v) => Some(v.as_i64().ok_or_else(|| invalid("revision"))?),
        None => None,
    };
    if revision.is_some_and(|r| r != current["revision"].as_i64().unwrap_or_default()) {
        let article = db::article_view(&ctx.db, id(&current), Some(viewer), false).await?;
        return Err(ApiError(
            StatusCode::CONFLICT,
            json!({"errors":{"revision":["is stale"]},"article":article}),
        ));
    }
    let title = optional_text(changes, "title")?;
    let description = optional_text(changes, "description")?;
    let text = optional_text(changes, "body")?;
    let tag_list = tags(changes)?;
    let saved = db::change_article(
        &ctx.db,
        id(&current),
        current["revision"].as_i64().unwrap_or_default(),
        title,
        description,
        text,
    )
    .await?;
    if saved.is_none() {
        let article = db::article_view(&ctx.db, id(&current), Some(viewer), false).await?;
        return Err(ApiError(
            StatusCode::CONFLICT,
            json!({"errors":{"revision":["is stale"]},"article":article}),
        ));
    }
    if let Some(tags) = tag_list {
        save_tags(&ctx, id(&current), &tags).await?;
    }
    shares::broadcast_update(&ctx, id(&current)).await;
    Ok(respond(
        StatusCode::OK,
        json!({"article":db::article_view(&ctx.db,id(&current),Some(viewer),false).await?}),
    ))
}

async fn remove(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Path(slug): Path<String>,
) -> ApiResult {
    let viewer = required_viewer(&ctx, &headers)?;
    let article = visible(&ctx, &slug, Some(viewer)).await?;
    owner(&article, viewer)?;
    shares::revoke_article(&ctx, id(&article)).await?;
    db::exec(
        &ctx.db,
        "DELETE FROM rw_articles WHERE id=$1",
        vec![id(&article).into()],
    )
    .await?;
    Ok(empty())
}

async fn publish(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Path(slug): Path<String>,
) -> ApiResult {
    let viewer = required_viewer(&ctx, &headers)?;
    let article = visible(&ctx, &slug, Some(viewer)).await?;
    owner(&article, viewer)?;
    if article["status"] == "draft" {
        db::exec(&ctx.db,"UPDATE rw_articles SET status='published',published_at=now(),revision=revision+1,updated_at=now() WHERE id=$1",vec![id(&article).into()]).await?;
        shares::broadcast_update(&ctx, id(&article)).await;
    }
    Ok(respond(
        StatusCode::OK,
        json!({"article":db::article_view(&ctx.db,id(&article),Some(viewer),false).await?}),
    ))
}

async fn list(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Query(params): Query<HashMap<String, String>>,
) -> ApiResult {
    list_with(&ctx, viewer(&ctx, &headers), &params, "all").await
}
async fn feed(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Query(params): Query<HashMap<String, String>>,
) -> ApiResult {
    let viewer = required_viewer(&ctx, &headers)?;
    list_with(&ctx, Some(viewer), &params, "feed").await
}
async fn drafts(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Query(params): Query<HashMap<String, String>>,
) -> ApiResult {
    let viewer = required_viewer(&ctx, &headers)?;
    list_with(&ctx, Some(viewer), &params, "drafts").await
}

async fn list_with(
    ctx: &AppContext,
    viewer: Option<i64>,
    params: &HashMap<String, String>,
    mode: &str,
) -> ApiResult {
    let author = params.get("author").map(String::as_str).unwrap_or("");
    let tag = params.get("tag").map(String::as_str).unwrap_or("");
    let favorited = params.get("favorited").map(String::as_str).unwrap_or("");
    let sql = "SELECT row_to_json(t)::text data FROM (SELECT a.id FROM rw_articles a JOIN rw_users u ON u.id=a.author_id WHERE (($1='drafts' AND a.status='draft' AND a.author_id=$2) OR ($1<>'drafts' AND a.status='published' AND ($1<>'feed' OR EXISTS(SELECT 1 FROM rw_follows WHERE follower=$2 AND followed=a.author_id)))) AND ($3='' OR u.username=$3) AND ($4='' OR EXISTS(SELECT 1 FROM rw_tags WHERE article_id=a.id AND tag=$4)) AND ($5='' OR EXISTS(SELECT 1 FROM rw_favorites f JOIN rw_users fu ON fu.id=f.user_id WHERE f.article_id=a.id AND fu.username=$5)) ORDER BY a.created_at DESC,a.id DESC) t";
    let found = db::rows(
        &ctx.db,
        sql,
        vec![
            mode.into(),
            viewer.unwrap_or_default().into(),
            author.into(),
            tag.into(),
            favorited.into(),
        ],
    )
    .await?;
    let count = found.len();
    let offset = params
        .get("offset")
        .and_then(|s| s.parse::<usize>().ok())
        .unwrap_or(0);
    let limit = params
        .get("limit")
        .and_then(|s| s.parse::<usize>().ok())
        .unwrap_or(20)
        .min(1000);
    let mut articles = Vec::new();
    for item in found.into_iter().skip(offset).take(limit) {
        if let Some(article) = db::article_view(&ctx.db, id(&item), viewer, true).await? {
            articles.push(article);
        }
    }
    Ok(respond(
        StatusCode::OK,
        json!({"articles":articles,"articlesCount":count}),
    ))
}

async fn tag_list(State(ctx): State<AppContext>) -> ApiResult {
    let tags = db::rows(&ctx.db,"SELECT row_to_json(t)::text data FROM (SELECT DISTINCT tag FROM rw_tags JOIN rw_articles ON rw_articles.id=rw_tags.article_id WHERE rw_articles.status='published' ORDER BY tag) t",vec![]).await?;
    Ok(respond(
        StatusCode::OK,
        json!({"tags":tags.iter().map(|v|v["tag"].clone()).collect::<Vec<_>>()}),
    ))
}

async fn favorite(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Path(slug): Path<String>,
) -> ApiResult {
    favorite_with(ctx, headers, slug, true).await
}
async fn unfavorite(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Path(slug): Path<String>,
) -> ApiResult {
    favorite_with(ctx, headers, slug, false).await
}
async fn favorite_with(ctx: AppContext, headers: HeaderMap, slug: String, add: bool) -> ApiResult {
    let viewer = required_viewer(&ctx, &headers)?;
    let article = visible(&ctx, &slug, Some(viewer)).await?;
    if article["status"] == "draft" {
        return Err(fail(
            StatusCode::UNPROCESSABLE_ENTITY,
            "article",
            "is a draft",
        ));
    }
    if add {
        db::exec(
            &ctx.db,
            "INSERT INTO rw_favorites(article_id,user_id) VALUES($1,$2) ON CONFLICT DO NOTHING",
            vec![id(&article).into(), viewer.into()],
        )
        .await?;
    } else {
        db::exec(
            &ctx.db,
            "DELETE FROM rw_favorites WHERE article_id=$1 AND user_id=$2",
            vec![id(&article).into(), viewer.into()],
        )
        .await?;
    }
    Ok(respond(
        StatusCode::OK,
        json!({"article":db::article_view(&ctx.db,id(&article),Some(viewer),false).await?}),
    ))
}

async fn comment_list(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Path(slug): Path<String>,
) -> ApiResult {
    let viewer = viewer(&ctx, &headers);
    let article = visible(&ctx, &slug, viewer).await?;
    let comments=db::rows(&ctx.db,"SELECT row_to_json(t)::text data FROM (SELECT c.id,c.body,c.created_at AS \"createdAt\",c.updated_at AS \"updatedAt\",u.username,u.bio,u.image,EXISTS(SELECT 1 FROM rw_follows WHERE follower=$2 AND followed=u.id) AS following FROM rw_comments c JOIN rw_users u ON u.id=c.author_id WHERE c.article_id=$1 ORDER BY c.created_at,c.id) t",vec![id(&article).into(),viewer.unwrap_or_default().into()]).await?;
    Ok(respond(
        StatusCode::OK,
        json!({"comments":comments.into_iter().map(comment_view).collect::<Vec<_>>()}),
    ))
}

fn comment_view(c: Value) -> Value {
    json!({"id":c["id"],"body":c["body"],"createdAt":c["createdAt"],"updatedAt":c["updatedAt"],"author":{"username":c["username"],"bio":c["bio"],"image":c["image"],"following":c["following"]}})
}

async fn comment_create(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Path(slug): Path<String>,
    Json(body): Json<Value>,
) -> ApiResult {
    let viewer = required_viewer(&ctx, &headers)?;
    let article = visible(&ctx, &slug, Some(viewer)).await?;
    if article["status"] == "draft" {
        return Err(fail(
            StatusCode::UNPROCESSABLE_ENTITY,
            "article",
            "is a draft",
        ));
    }
    let text = required(object(&body, "comment")?, "body")?;
    let comment=db::row(&ctx.db,"WITH t AS (INSERT INTO rw_comments(article_id,author_id,body) VALUES($1,$2,$3) RETURNING id,body,created_at AS \"createdAt\",updated_at AS \"updatedAt\") SELECT row_to_json(t)::text data FROM t",vec![id(&article).into(),viewer.into(),text.into()]).await?.ok_or_else(|| missing("comment"))?;
    let author = db::user(&ctx.db, viewer)
        .await?
        .ok_or_else(|| missing("user"))?;
    let mut response = comment;
    response["author"] = json!({"username":author["username"],"bio":author["bio"],"image":author["image"],"following":false});
    Ok(respond(StatusCode::CREATED, json!({"comment":response})))
}

async fn comment_delete(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Path((slug, comment_id)): Path<(String, String)>,
) -> ApiResult {
    let viewer = required_viewer(&ctx, &headers)?;
    let article = visible(&ctx, &slug, Some(viewer)).await?;
    let comment_id = comment_id.parse::<i64>().map_err(|_| missing("comment"))?;
    let comment=db::row(&ctx.db,"SELECT row_to_json(t)::text data FROM (SELECT id,author_id FROM rw_comments WHERE id=$1 AND article_id=$2) t",vec![comment_id.into(),id(&article).into()]).await?.ok_or_else(|| missing("comment"))?;
    if comment["author_id"].as_i64() != Some(viewer) {
        return Err(forbidden("comment"));
    }
    db::exec(
        &ctx.db,
        "DELETE FROM rw_comments WHERE id=$1",
        vec![comment_id.into()],
    )
    .await?;
    Ok(empty())
}

pub fn routes() -> Routes {
    Routes::new()
        .prefix("/api")
        .add("/articles", get(list))
        .add("/articles", post(create))
        .add("/articles/feed", get(feed))
        .add("/user/drafts", get(drafts))
        .add("/tags", get(tag_list))
        .add("/articles/{slug}", get(show))
        .add("/articles/{slug}", put(update))
        .add("/articles/{slug}", delete(remove))
        .add("/articles/{slug}/publish", post(publish))
        .add("/articles/{slug}/favorite", post(favorite))
        .add("/articles/{slug}/favorite", delete(unfavorite))
        .add("/articles/{slug}/comments", get(comment_list))
        .add("/articles/{slug}/comments", post(comment_create))
        .add("/articles/{slug}/comments/{id}", delete(comment_delete))
}
