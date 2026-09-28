use crate::{
    controllers::{articles::visible, common::*},
    models::realworld as db,
};
use axum::{
    extract::ws::{Message, WebSocket, WebSocketUpgrade},
    http::{HeaderMap, StatusCode},
    response::Response,
    Json,
};
use futures_util::SinkExt;
use loco_rs::prelude::*;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::HashMap,
    sync::{Mutex, OnceLock},
};
use tokio::sync::broadcast;
use uuid::Uuid;

const ROOM_LIMIT: usize = 100;
struct Room {
    count: usize,
    sender: broadcast::Sender<Value>,
}
static ROOMS: OnceLock<Mutex<HashMap<String, Room>>> = OnceLock::new();
fn rooms() -> &'static Mutex<HashMap<String, Room>> {
    ROOMS.get_or_init(|| Mutex::new(HashMap::new()))
}
fn digest(key: &str) -> String {
    hex::encode(Sha256::digest(key.as_bytes()))
}

async fn link(ctx: &AppContext, share_id: &str, key: &str) -> Result<Value, ApiError> {
    let share=db::row(&ctx.db,"SELECT row_to_json(t)::text data FROM (SELECT article_id,key_hash FROM rw_shares WHERE id=$1) t",vec![share_id.into()]).await?.ok_or_else(|| missing("share"))?;
    if share["key_hash"].as_str() != Some(digest(key).as_str()) {
        return Err(missing("share"));
    }
    db::article_by_id(&ctx.db, share["article_id"].as_i64().unwrap_or_default())
        .await?
        .ok_or_else(|| missing("share"))
}

fn header_key(headers: &HeaderMap) -> &str {
    headers
        .get("x-share-key")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("")
}

async fn create(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Path(slug): Path<String>,
) -> ApiResult {
    let viewer = required_viewer(&ctx, &headers)?;
    let article = visible(&ctx, &slug, Some(viewer)).await?;
    if article["author_id"].as_i64() != Some(viewer) {
        return Err(forbidden("article"));
    }
    revoke_article(&ctx, id(&article)).await?;
    let share_id = Uuid::new_v4().to_string();
    let key = format!("{}{}", Uuid::new_v4().simple(), Uuid::new_v4().simple());
    db::exec(
        &ctx.db,
        "INSERT INTO rw_shares(id,article_id,key_hash) VALUES($1,$2,$3)",
        vec![
            share_id.clone().into(),
            id(&article).into(),
            digest(&key).into(),
        ],
    )
    .await?;
    Ok(respond(
        StatusCode::CREATED,
        json!({"share":{"id":share_id,"key":key}}),
    ))
}

async fn remove(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Path(slug): Path<String>,
) -> ApiResult {
    let viewer = required_viewer(&ctx, &headers)?;
    let article = visible(&ctx, &slug, Some(viewer)).await?;
    if article["author_id"].as_i64() != Some(viewer) {
        return Err(forbidden("article"));
    }
    revoke_article(&ctx, id(&article)).await?;
    Ok(empty())
}

pub async fn revoke_article(ctx: &AppContext, article_id: i64) -> Result<(), ApiError> {
    let old=db::row(&ctx.db,"WITH t AS (DELETE FROM rw_shares WHERE article_id=$1 RETURNING id) SELECT row_to_json(t)::text data FROM t",vec![article_id.into()]).await?;
    if let Some(old) = old {
        if let Some(share_id) = old["id"].as_str() {
            if let Some(room) = rooms().lock().expect("rooms").get(share_id) {
                let _ = room.sender.send(json!({"type":"revoked"}));
            }
        }
    }
    Ok(())
}

pub async fn broadcast_update(ctx: &AppContext, article_id: i64) {
    let result = db::row(
        &ctx.db,
        "SELECT row_to_json(t)::text data FROM (SELECT id FROM rw_shares WHERE article_id=$1) t",
        vec![article_id.into()],
    )
    .await;
    if let Ok(Some(share)) = result {
        if let (Some(share_id), Ok(Some(article))) = (
            share["id"].as_str(),
            db::article_by_id(&ctx.db, article_id).await,
        ) {
            if let Some(room) = rooms().lock().expect("rooms").get(share_id) {
                let _ = room
                    .sender
                    .send(json!({"type":"updated","article":db::shared(&article)}));
            }
        }
    }
}

async fn show(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Path(share_id): Path<String>,
) -> ApiResult {
    let article = link(&ctx, &share_id, header_key(&headers)).await?;
    Ok(respond(
        StatusCode::OK,
        json!({"article":db::shared(&article)}),
    ))
}

async fn update(
    State(ctx): State<AppContext>,
    headers: HeaderMap,
    Path(share_id): Path<String>,
    Json(body): Json<Value>,
) -> ApiResult {
    let current = link(&ctx, &share_id, header_key(&headers)).await?;
    let changes = object(&body, "article")?;
    if changes.as_object().is_none_or(|o| {
        o.len() != 3
            || !o.contains_key("title")
            || !o.contains_key("body")
            || !o.contains_key("revision")
    }) {
        return Err(invalid("article"));
    }
    let revision = changes["revision"]
        .as_i64()
        .ok_or_else(|| invalid("revision"))?;
    let title = required(changes, "title")?.to_string();
    let body = required(changes, "body")?.to_string();
    let current_revision = current["revision"].as_i64().unwrap_or_default();
    if revision != current_revision {
        return Err(ApiError(
            StatusCode::CONFLICT,
            json!({"errors":{"revision":["is stale"]},"article":db::shared(&current)}),
        ));
    }
    let saved = db::change_article(
        &ctx.db,
        id(&current),
        revision,
        Some(title),
        None,
        Some(body),
    )
    .await?;
    if saved.is_none() {
        let latest = db::article_by_id(&ctx.db, id(&current))
            .await?
            .ok_or_else(|| missing("share"))?;
        return Err(ApiError(
            StatusCode::CONFLICT,
            json!({"errors":{"revision":["is stale"]},"article":db::shared(&latest)}),
        ));
    }
    let article = db::shared(&saved.unwrap_or_default());
    broadcast_update(&ctx, id(&current)).await;
    Ok(respond(StatusCode::OK, json!({"article":article})))
}

async fn live(
    State(ctx): State<AppContext>,
    Path(share_id): Path<String>,
    ws: WebSocketUpgrade,
) -> Response {
    ws.on_upgrade(move |socket| socket_session(ctx, share_id, socket))
        .into_response()
}

async fn socket_session(ctx: AppContext, share_id: String, mut socket: WebSocket) {
    let first = tokio::time::timeout(std::time::Duration::from_secs(5), socket.recv()).await;
    let key = match first {
        Ok(Some(Ok(Message::Text(text)))) => serde_json::from_str::<Value>(&text)
            .ok()
            .filter(|v| v["type"] == "subscribe")
            .and_then(|v| v["key"].as_str().map(str::to_owned)),
        _ => None,
    };
    let Some(key) = key else {
        let _ = socket
            .send(Message::Text(
                json!({"type":"invalid_link"}).to_string().into(),
            ))
            .await;
        let _ = socket.close().await;
        return;
    };
    let article = match link(&ctx, &share_id, &key).await {
        Ok(article) => article,
        Err(_) => {
            let _ = socket
                .send(Message::Text(
                    json!({"type":"invalid_link"}).to_string().into(),
                ))
                .await;
            let _ = socket.close().await;
            return;
        }
    };
    let admission = {
        let mut rooms = rooms().lock().expect("rooms");
        let room = rooms.entry(share_id.clone()).or_insert_with(|| {
            let (sender, _) = broadcast::channel(512);
            Room { count: 0, sender }
        });
        if room.count >= ROOM_LIMIT {
            None
        } else {
            let receiver = room.sender.subscribe();
            room.count += 1;
            let count = room.count;
            let _ = room.sender.send(json!({"type":"presence","count":count}));
            Some((receiver, count))
        }
    };
    let Some((mut receiver, count)) = admission else {
        let _ = socket
            .send(Message::Text(
                json!({"type":"room_full","limit":ROOM_LIMIT})
                    .to_string()
                    .into(),
            ))
            .await;
        let _ = socket.close().await;
        return;
    };
    let snapshot = db::article_by_id(&ctx.db, id(&article))
        .await
        .ok()
        .flatten()
        .unwrap_or(article);
    let mut revision = snapshot["revision"].as_i64().unwrap_or_default();
    if socket
        .send(Message::Text(
            json!({"type":"ready","article":db::shared(&snapshot),"presence":count})
                .to_string()
                .into(),
        ))
        .await
        .is_ok()
    {
        loop {
            tokio::select! {
                event=receiver.recv()=>match event { Ok(message)=>{
                    if message["type"]=="updated" { let next=message["article"]["revision"].as_i64().unwrap_or_default(); if next<=revision { continue; } revision=next; }
                    let revoked=message["type"]=="revoked";
                    if socket.send(Message::Text(message.to_string().into())).await.is_err() || revoked { break; }
                }, Err(broadcast::error::RecvError::Lagged(_))=>continue, Err(_)=>break },
                incoming=socket.recv()=>if incoming.is_none_or(|v|v.is_err() || matches!(v,Ok(Message::Close(_)))) { break; }
            }
        }
    }
    let mut rooms = rooms().lock().expect("rooms");
    if let Some(room) = rooms.get_mut(&share_id) {
        room.count = room.count.saturating_sub(1);
        let _ = room
            .sender
            .send(json!({"type":"presence","count":room.count}));
        if room.count == 0 {
            rooms.remove(&share_id);
        }
    }
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
