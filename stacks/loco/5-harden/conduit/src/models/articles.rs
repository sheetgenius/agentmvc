use std::collections::BTreeSet;

use chrono::Utc;
use loco_rs::prelude::*;
use sea_orm::sea_query::{extension::postgres::PgExpr, Expr};
use sea_orm::{DatabaseTransaction, QueryTrait, Select};
use serde_json::{json, Value};
use uuid::Uuid;

pub use super::_entities::articles::{self, ActiveModel, Entity, Model};

#[async_trait::async_trait]
impl ActiveModelBehavior for ActiveModel {
    async fn before_save<C>(mut self, _db: &C, insert: bool) -> std::result::Result<Self, DbErr>
    where
        C: ConnectionTrait,
    {
        if !insert {
            self.updated_at = Set(Utc::now().into());
        }
        Ok(self)
    }
}

impl Model {
    fn with_slug(slug: &str) -> Select<Entity> {
        Entity::find().filter(articles::Column::Slug.eq(slug))
    }

    fn published() -> Select<Entity> {
        Entity::find().filter(articles::Column::Status.eq("published"))
    }

    pub async fn by_slug<C: ConnectionTrait>(
        db: &C,
        slug: &str,
    ) -> std::result::Result<Option<Self>, DbErr> {
        Self::with_slug(slug).one(db).await
    }

    pub async fn by_slug_for_update(
        db: &DatabaseTransaction,
        slug: &str,
    ) -> std::result::Result<Option<Self>, DbErr> {
        Self::with_slug(slug).lock_exclusive().one(db).await
    }

    pub async fn create(
        db: &DatabaseConnection,
        author_id: i64,
        title: String,
        description: String,
        body: String,
        tags: Vec<String>,
        status: String,
    ) -> std::result::Result<Self, DbErr> {
        let published_at = (status == "published").then(|| Utc::now().into());
        ActiveModel {
            slug: Set(Self::slug_for(&title)),
            title: Set(title),
            description: Set(description),
            body: Set(body),
            tag_list: Set(serde_json::json!(tags)),
            author_id: Set(author_id),
            status: Set(status),
            published_at: Set(published_at),
            ..Default::default()
        }
        .insert(db)
        .await
    }

    pub fn tags(&self) -> Vec<String> {
        serde_json::from_value(self.tag_list.clone()).unwrap_or_default()
    }

    pub fn is_draft(&self) -> bool {
        self.status == "draft"
    }

    pub fn revised(&self) -> ActiveModel {
        let mut active = self.clone().into_active_model();
        active.revision = Set(self.revision + 1);
        active
    }

    pub fn slug_for(title: &str) -> String {
        format!("{}-{}", slug::slugify(title), Uuid::new_v4().simple())
    }

    pub async fn list(
        db: &DatabaseConnection,
        author: Option<i64>,
        favorited: Option<i64>,
        tag: Option<&str>,
        feed: Option<i64>,
        limit: usize,
        offset: usize,
    ) -> std::result::Result<(Vec<Self>, usize), DbErr> {
        use super::favorites;
        use super::follows;
        let mut query = Self::published().order_by_desc(articles::Column::Id);
        if let Some(author) = author {
            query = query.filter(articles::Column::AuthorId.eq(author));
        }
        if let Some(user_id) = favorited {
            let ids = favorites::Entity::find()
                .select_only()
                .column(favorites::Column::ArticleId)
                .filter(favorites::Column::UserId.eq(user_id))
                .into_query();
            query = query.filter(articles::Column::Id.in_subquery(ids));
        }
        if let Some(user_id) = feed {
            let ids = follows::Entity::find()
                .select_only()
                .column(follows::Column::FollowedId)
                .filter(follows::Column::FollowerId.eq(user_id))
                .into_query();
            query = query.filter(articles::Column::AuthorId.in_subquery(ids));
        }
        if let Some(tag) = tag {
            query = query.filter(Expr::col(articles::Column::TagList).contains(json!([tag])));
        }
        let count = query.clone().count(db).await? as usize;
        let articles = query
            .offset(offset as u64)
            .limit(limit as u64)
            .all(db)
            .await?;
        Ok((articles, count))
    }

    pub async fn drafts(
        db: &DatabaseConnection,
        author_id: i64,
        limit: usize,
        offset: usize,
    ) -> std::result::Result<(Vec<Self>, usize), DbErr> {
        let query = Entity::find()
            .filter(articles::Column::AuthorId.eq(author_id))
            .filter(articles::Column::Status.eq("draft"))
            .order_by_desc(articles::Column::Id);
        let count = query.clone().count(db).await? as usize;
        let articles = query
            .offset(offset as u64)
            .limit(limit as u64)
            .all(db)
            .await?;
        Ok((articles, count))
    }

    pub async fn all_tags(db: &DatabaseConnection) -> std::result::Result<BTreeSet<String>, DbErr> {
        Ok(Self::published()
            .select_only()
            .column(articles::Column::TagList)
            .into_tuple::<Value>()
            .all(db)
            .await?
            .into_iter()
            .flat_map(|tags| serde_json::from_value::<Vec<String>>(tags).unwrap_or_default())
            .collect())
    }
}

impl ActiveModel {
    pub fn replace_tags(mut self, tags: Vec<String>) -> Self {
        self.tag_list = Set(Value::from(tags));
        self
    }
}
