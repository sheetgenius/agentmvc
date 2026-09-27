use std::time::Duration;

use axum::{
    body::Bytes,
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        Path, State,
    },
    http::{HeaderMap, StatusCode},
    response::Response,
};
use loco_rs::prelude::*;
use serde::Deserialize;
use serde_json::{json, Value};

use crate::{
    controllers::{
        api::{self, ApiError, ApiResult, Viewer},
        articles,
    },
    models::{
        article_shares, articles as article_model,
        live_rooms::{Admission, Event, Hub},
    },
    views::realworld::SharedArticleView,
};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Envelope {
    article: Changes,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Changes {
    title: String,
    body: String,
    revision: i32,
}

async fn authorize(
    ctx: &AppContext,
    id: &str,
    key: &str,
) -> std::result::Result<article_shares::Model, ApiError> {
    article_shares::Model::authorized(&ctx.db, id, key)
        .await?
        .ok_or(ApiError::missing("share"))
}

fn key(headers: &HeaderMap) -> &str {
    headers
        .get("x-share-key")
        .and_then(|value| value.to_str().ok())
        .unwrap_or("")
}

#[debug_handler]
async fn create(
    Path(slug): Path<String>,
    Viewer(viewer): Viewer,
    State(ctx): State<AppContext>,
) -> ApiResult {
    let txn = ctx.db.begin().await?;
    let article = articles::find_owned_for_update(&txn, &slug, viewer.id).await?;
    let (id, key, old) = article_shares::Model::rotate(&txn, article.id).await?;
    txn.commit().await?;
    if let Some(old) = old {
        Hub::from_ctx(&ctx).revoke(&old).await;
    }
    Ok(api::json_response(
        StatusCode::CREATED,
        json!({"share": {"id": id, "key": key}}),
    ))
}

#[debug_handler]
async fn remove(
    Path(slug): Path<String>,
    Viewer(viewer): Viewer,
    State(ctx): State<AppContext>,
) -> ApiResult {
    let txn = ctx.db.begin().await?;
    let article = articles::find_owned_for_update(&txn, &slug, viewer.id).await?;
    let old = article_shares::Model::revoke(&txn, article.id).await?;
    txn.commit().await?;
    if let Some(old) = old {
        Hub::from_ctx(&ctx).revoke(&old).await;
    }
    Ok(StatusCode::NO_CONTENT.into_response())
}

#[debug_handler]
async fn show(
    Path(id): Path<String>,
    State(ctx): State<AppContext>,
    headers: HeaderMap,
) -> ApiResult {
    let share = authorize(&ctx, &id, key(&headers)).await?;
    let article = article_model::Entity::find_by_id(share.article_id)
        .one(&ctx.db)
        .await?
        .ok_or(ApiError::missing("share"))?;
    Ok(api::json_response(
        StatusCode::OK,
        json!({"article": SharedArticleView::from(&article)}),
    ))
}

#[debug_handler]
async fn update(
    Path(id): Path<String>,
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    body: Bytes,
) -> ApiResult {
    let key = key(&headers);
    let share = authorize(&ctx, &id, key).await?;
    let Envelope { article: changes } =
        serde_json::from_slice(&body).map_err(|_| ApiError::invalid("article"))?;
    api::required(&changes.title, "title")?;
    api::required(&changes.body, "body")?;
    let txn = ctx.db.begin().await?;
    let article = article_model::Model::by_id_for_update(&txn, share.article_id)
        .await?
        .ok_or(ApiError::missing("share"))?;
    if article_shares::Model::authorized(&txn, &id, key)
        .await?
        .is_none()
    {
        return Err(ApiError::missing("share"));
    }
    if changes.revision != article.revision {
        return Ok(api::json_response(
            StatusCode::CONFLICT,
            json!({
                "errors": {"revision": ["is stale"]},
                "article": SharedArticleView::from(&article)
            }),
        ));
    }
    let mut active = article.revised();
    active.slug = Set(article_model::Model::slug_for(&changes.title));
    active.title = Set(changes.title);
    active.body = Set(changes.body);
    let article = active.update(&txn).await?;
    txn.commit().await?;
    let view = SharedArticleView::from(&article);
    Hub::from_ctx(&ctx).updated(&id, view.clone()).await;
    Ok(api::json_response(StatusCode::OK, json!({"article": view})))
}

#[debug_handler]
async fn live(
    Path(id): Path<String>,
    State(ctx): State<AppContext>,
    ws: WebSocketUpgrade,
) -> Response {
    ws.on_upgrade(move |socket| socket_session(socket, ctx, id))
}

async fn send(socket: &mut WebSocket, value: Value) -> bool {
    socket
        .send(Message::Text(value.to_string().into()))
        .await
        .is_ok()
}

async fn reject(socket: &mut WebSocket, value: Value) {
    let _ = send(socket, value).await;
    let _ = socket.send(Message::Close(None)).await;
}

async fn socket_session(mut socket: WebSocket, ctx: AppContext, id: String) {
    let first = tokio::time::timeout(Duration::from_secs(5), socket.recv()).await;
    let Some(Ok(Message::Text(text))) = first.ok().flatten() else {
        let _ = socket.send(Message::Close(None)).await;
        return;
    };
    let message = serde_json::from_str::<Value>(&text).ok();
    let key = message.as_ref().and_then(|message| {
        (message.get("type")?.as_str()? == "subscribe")
            .then(|| message.get("key")?.as_str())
            .flatten()
    });
    let Some(key) = key else {
        reject(&mut socket, json!({"type": "invalid_link"})).await;
        return;
    };
    let Ok(admission) = Hub::from_ctx(&ctx).admit(&ctx.db, &id, key).await else {
        let _ = socket.send(Message::Close(None)).await;
        return;
    };
    let Some(mut live) = admission else {
        reject(&mut socket, json!({"type": "invalid_link"})).await;
        return;
    };
    match &mut live.admission {
        Admission::Invalid => reject(&mut socket, json!({"type": "invalid_link"})).await,
        Admission::Full => reject(&mut socket, json!({"type": "room_full", "limit": 100})).await,
        Admission::Ready {
            article,
            presence,
            events,
        } => {
            let mut last_revision = article.revision;
            if send(
                &mut socket,
                json!({"type": "ready", "article": article, "presence": presence}),
            )
            .await
            {
                loop {
                    tokio::select! {
                        incoming = socket.recv() => {
                            if !matches!(incoming, Some(Ok(_))) {
                                break;
                            }
                        }
                        event = events.recv() => {
                            let message = match event {
                                Ok(Event::Updated(article)) if article.revision > last_revision => {
                                    last_revision = article.revision;
                                    Some(json!({"type": "updated", "article": article}))
                                }
                                Ok(Event::Presence(count)) => Some(json!({"type": "presence", "count": count})),
                                Ok(Event::Revoked) => {
                                    reject(&mut socket, json!({"type": "revoked"})).await;
                                    break;
                                }
                                Err(tokio::sync::broadcast::error::RecvError::Lagged(_)) => {
                                    let Ok(share) = authorize(&ctx, &id, key).await else {
                                        reject(&mut socket, json!({"type": "revoked"})).await;
                                        break;
                                    };
                                    let Ok(Some(current)) = article_model::Entity::find_by_id(share.article_id).one(&ctx.db).await else {
                                        break;
                                    };
                                    let article = SharedArticleView::from(&current);
                                    if article.revision > last_revision {
                                        last_revision = article.revision;
                                        Some(json!({"type": "updated", "article": article}))
                                    } else {
                                        None
                                    }
                                }
                                Err(tokio::sync::broadcast::error::RecvError::Closed) => break,
                                _ => None,
                            };
                            if let Some(message) = message {
                                if !send(&mut socket, message).await { break; }
                            }
                        }
                    }
                }
            }
        }
    }
    live.leave().await;
}

pub fn routes() -> Routes {
    Routes::new()
        .prefix("/api")
        .add("/articles/{slug}/share", post(create))
        .add("/articles/{slug}/share", delete(remove))
        .add("/shares/{id}/article", get(show))
        .add("/shares/{id}/article", put(update))
        .add("/shares/{id}/live", get(live))
}
