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
