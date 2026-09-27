pub use super::_entities::follows::{self, ActiveModel, Column, Entity, Model};
use loco_rs::prelude::*;
impl ActiveModelBehavior for ActiveModel {}

impl Model {
    pub async fn is_following(
        db: &DatabaseConnection,
        follower_id: i64,
        followed_id: i64,
    ) -> std::result::Result<bool, DbErr> {
        Ok(Entity::find()
            .filter(follows::Column::FollowerId.eq(follower_id))
            .filter(follows::Column::FollowedId.eq(followed_id))
            .one(db)
            .await?
            .is_some())
    }

    pub async fn set(
        db: &DatabaseConnection,
        follower_id: i64,
        followed_id: i64,
        following: bool,
    ) -> std::result::Result<(), DbErr> {
        if following {
            Entity::insert(ActiveModel {
                follower_id: Set(follower_id),
                followed_id: Set(followed_id),
                ..Default::default()
            })
            .on_conflict_do_nothing_on([Column::FollowerId, Column::FollowedId])
            .exec(db)
            .await?;
        } else {
            Entity::delete_many()
                .filter(Column::FollowerId.eq(follower_id))
                .filter(Column::FollowedId.eq(followed_id))
                .exec(db)
                .await?;
        }
        Ok(())
    }
}
