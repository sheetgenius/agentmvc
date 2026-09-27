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
            .on_conflict_do_nothing_on([Column::UserId, Column::ArticleId])
            .exec(db)
            .await?;
        } else {
            Entity::delete_many()
                .filter(Column::UserId.eq(user_id))
                .filter(Column::ArticleId.eq(article_id))
                .exec(db)
                .await?;
        }
        Ok(())
    }
}
