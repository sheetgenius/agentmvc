use std::{collections::HashMap, sync::Arc};

use loco_rs::{app::AppContext, prelude::*};
use sea_orm::DbErr;
use tokio::sync::{broadcast, Mutex};

use super::{article_shares, articles};
use crate::views::realworld::SharedArticleView;

#[derive(Clone)]
pub enum Event {
    Updated(SharedArticleView),
    Presence(usize),
    Revoked,
}

pub enum Admission {
    Ready {
        article: SharedArticleView,
        presence: usize,
        events: broadcast::Receiver<Event>,
    },
    Invalid,
    Full,
}

struct RoomState {
    count: usize,
    revoked: bool,
}

struct Room {
    state: Mutex<RoomState>,
    sender: broadcast::Sender<Event>,
}

impl Room {
    fn new() -> Self {
        let (sender, _) = broadcast::channel(1024);
        Self {
            state: Mutex::new(RoomState {
                count: 0,
                revoked: false,
            }),
            sender,
        }
    }

    async fn admit(
        &self,
        db: &DatabaseConnection,
        id: &str,
        key: &str,
    ) -> std::result::Result<Admission, DbErr> {
        let mut state = self.state.lock().await;
        if state.revoked {
            return Ok(Admission::Invalid);
        }
        let Some(share) = article_shares::Model::authorized(db, id, key).await? else {
            return Ok(Admission::Invalid);
        };
        if state.count == 100 {
            return Ok(Admission::Full);
        }
        let Some(article) = articles::Entity::find_by_id(share.article_id)
            .one(db)
            .await?
        else {
            return Ok(Admission::Invalid);
        };
        state.count += 1;
        let events = self.sender.subscribe();
        let _ = self.sender.send(Event::Presence(state.count));
        Ok(Admission::Ready {
            article: SharedArticleView::from(&article),
            presence: state.count,
            events,
        })
    }

    async fn leave(&self) {
        let mut state = self.state.lock().await;
        state.count -= 1;
        if !state.revoked {
            let _ = self.sender.send(Event::Presence(state.count));
        }
    }

    async fn updated(&self, article: SharedArticleView) {
        let state = self.state.lock().await;
        if !state.revoked && state.count > 0 {
            let _ = self.sender.send(Event::Updated(article));
        }
    }

    async fn revoke(&self) {
        let mut state = self.state.lock().await;
        state.revoked = true;
        let _ = self.sender.send(Event::Revoked);
    }
}

#[derive(Default)]
pub struct Hub {
    rooms: Mutex<HashMap<String, Arc<Room>>>,
}

impl Hub {
    pub fn from_ctx(ctx: &AppContext) -> Arc<Self> {
        ctx.shared_store
            .get::<Arc<Self>>()
            .expect("live room hub is registered at boot")
    }

    async fn room(&self, id: &str) -> Arc<Room> {
        self.rooms
            .lock()
            .await
            .entry(id.to_owned())
            .or_insert_with(|| Arc::new(Room::new()))
            .clone()
    }

    pub async fn admit(
        &self,
        db: &DatabaseConnection,
        id: &str,
        key: &str,
    ) -> std::result::Result<Option<Live>, DbErr> {
        if article_shares::Model::authorized(db, id, key)
            .await?
            .is_none()
        {
            return Ok(None);
        }
        let room = self.room(id).await;
        let admission = room.admit(db, id, key).await?;
        Ok(Some(Live { room, admission }))
    }

    pub async fn updated(&self, id: &str, article: SharedArticleView) {
        let room = self.rooms.lock().await.get(id).cloned();
        if let Some(room) = room {
            room.updated(article).await;
        }
    }

    pub async fn article_saved(
        ctx: &AppContext,
        article: &articles::Model,
    ) -> std::result::Result<(), DbErr> {
        if let Some(share) = article_shares::Model::for_article(&ctx.db, article.id).await? {
            Self::from_ctx(ctx)
                .updated(&share.id, SharedArticleView::from(article))
                .await;
        }
        Ok(())
    }

    pub async fn revoke(&self, id: &str) {
        let room = self.rooms.lock().await.remove(id);
        if let Some(room) = room {
            room.revoke().await;
        }
    }
}

pub struct Live {
    room: Arc<Room>,
    pub admission: Admission,
}

impl Live {
    pub async fn leave(self) {
        if matches!(self.admission, Admission::Ready { .. }) {
            self.room.leave().await;
        }
    }
}
