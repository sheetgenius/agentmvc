use std::collections::HashMap;

use chrono::Utc;
use loco_rs::prelude::*;
use sea_orm::{FromQueryResult, IsolationLevel, TransactionTrait};
use serde::Serialize;

use super::{articles, articles::articles::Column as ArticleColumn, comments};

pub use super::_entities::exports::{self, ActiveModel, Entity, Model};

impl ActiveModelBehavior for ActiveModel {}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct ExportArticle {
    slug: String,
    title: String,
    description: String,
    body: String,
    tag_list: Vec<String>,
    status: String,
    comments_count: i64,
}

#[derive(FromQueryResult)]
struct CommentCount {
    article_id: i64,
    count: i64,
}

impl Model {
    pub async fn create(db: &DatabaseConnection, user_id: i64) -> std::result::Result<Self, DbErr> {
        ActiveModel {
            user_id: Set(user_id),
            ..Default::default()
        }
        .insert(db)
        .await
    }

    pub async fn for_user(
        db: &DatabaseConnection,
        id: i64,
        user_id: i64,
    ) -> std::result::Result<Option<Self>, DbErr> {
        Entity::find()
            .filter(exports::Column::Id.eq(id))
            .filter(exports::Column::UserId.eq(user_id))
            .one(db)
            .await
    }

    pub async fn complete(db: &DatabaseConnection, id: i64) -> std::result::Result<(), DbErr> {
        let txn = db
            .begin_with_config(Some(IsolationLevel::RepeatableRead), None)
            .await?;
        let Some(export) = Entity::find_by_id(id).one(&txn).await? else {
            return Ok(());
        };
        if export.completed_at.is_some() {
            return Ok(());
        }
        let articles = articles::Entity::find()
            .filter(ArticleColumn::AuthorId.eq(export.user_id))
            .order_by_asc(ArticleColumn::Id)
            .all(&txn)
            .await?;
        let ids: Vec<_> = articles.iter().map(|article| article.id).collect();
        let counts: HashMap<_, _> = comments::Entity::find()
            .select_only()
            .column(comments::Column::ArticleId)
            .column_as(comments::Column::Id.count(), "count")
            .filter(comments::Column::ArticleId.is_in(ids))
            .group_by(comments::Column::ArticleId)
            .into_model::<CommentCount>()
            .all(&txn)
            .await?
            .into_iter()
            .map(|row| (row.article_id, row.count))
            .collect();
        let snapshot: Vec<_> = articles
            .into_iter()
            .map(|article| {
                let tag_list = article.tags();
                ExportArticle {
                    slug: article.slug,
                    title: article.title,
                    description: article.description,
                    body: article.body,
                    tag_list,
                    status: article.status,
                    comments_count: *counts.get(&article.id).unwrap_or(&0),
                }
            })
            .collect();
        let mut active = export.into_active_model();
        active.articles = Set(Some(serde_json::json!(snapshot)));
        active.completed_at = Set(Some(Utc::now().into()));
        active.update(&txn).await?;
        txn.commit().await
    }
}
