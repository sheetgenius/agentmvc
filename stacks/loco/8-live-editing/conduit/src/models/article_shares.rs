use loco_rs::prelude::*;
use sea_orm::DatabaseTransaction;
use sha2::{Digest, Sha256};
use uuid::Uuid;

pub use super::_entities::article_shares::{self, ActiveModel, Entity, Model};

impl Model {
    fn hash(key: &str) -> String {
        format!("{:x}", Sha256::digest(key.as_bytes()))
    }

    pub async fn authorized<C: ConnectionTrait>(
        db: &C,
        id: &str,
        key: &str,
    ) -> std::result::Result<Option<Self>, DbErr> {
        Entity::find()
            .filter(article_shares::Column::Id.eq(id))
            .filter(article_shares::Column::KeyHash.eq(Self::hash(key)))
            .one(db)
            .await
    }

    pub async fn for_article<C: ConnectionTrait>(
        db: &C,
        article_id: i64,
    ) -> std::result::Result<Option<Self>, DbErr> {
        Entity::find()
            .filter(article_shares::Column::ArticleId.eq(article_id))
            .one(db)
            .await
    }

    pub async fn rotate(
        txn: &DatabaseTransaction,
        article_id: i64,
    ) -> std::result::Result<(String, String, Option<String>), DbErr> {
        let old = Self::revoke(txn, article_id).await?;
        let id = Uuid::new_v4().simple().to_string();
        let key = format!("{}{}", Uuid::new_v4().simple(), Uuid::new_v4().simple());
        ActiveModel {
            id: Set(id.clone()),
            article_id: Set(article_id),
            key_hash: Set(Self::hash(&key)),
        }
        .insert(txn)
        .await?;
        Ok((id, key, old))
    }

    pub async fn revoke(
        txn: &DatabaseTransaction,
        article_id: i64,
    ) -> std::result::Result<Option<String>, DbErr> {
        let old = Self::for_article(txn, article_id).await?;
        if let Some(share) = &old {
            Entity::delete_by_id(&share.id).exec(txn).await?;
        }
        Ok(old.map(|share| share.id))
    }
}
