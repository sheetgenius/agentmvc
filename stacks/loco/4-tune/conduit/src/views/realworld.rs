use std::collections::{HashMap, HashSet};

use loco_rs::prelude::*;
use sea_orm::FromQueryResult;
use serde::Serialize;

use crate::models::{articles, comments, favorites, follows, users};

#[derive(Serialize)]
pub struct UserView {
    pub email: String,
    pub token: String,
    pub username: String,
    pub bio: Option<String>,
    pub image: Option<String>,
}

impl UserView {
    pub fn new(user: &users::Model, token: String) -> Self {
        Self {
            email: user.email.clone(),
            token,
            username: user.username.clone(),
            bio: user.bio.clone(),
            image: user.image.clone(),
        }
    }
}

#[derive(Serialize)]
pub struct ProfileView {
    pub username: String,
    pub bio: Option<String>,
    pub image: Option<String>,
    pub following: bool,
}

impl ProfileView {
    fn new(user: &users::Model, following: bool) -> Self {
        Self {
            username: user.username.clone(),
            bio: user.bio.clone(),
            image: user.image.clone(),
            following,
        }
    }

    pub async fn load(
        db: &DatabaseConnection,
        user: &users::Model,
        viewer: Option<&users::Model>,
    ) -> std::result::Result<Self, DbErr> {
        let following = if let Some(viewer) = viewer {
            follows::Model::is_following(db, viewer.id, user.id).await?
        } else {
            false
        };
        Ok(Self::new(user, following))
    }
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ArticleView {
    pub slug: String,
    pub title: String,
    pub description: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub body: Option<String>,
    pub tag_list: Vec<String>,
    pub created_at: String,
    pub updated_at: String,
    pub status: String,
    pub published_at: Option<String>,
    pub revision: i32,
    pub favorited: bool,
    pub favorites_count: u64,
    pub author: ProfileView,
}

#[derive(FromQueryResult)]
struct FavoriteCount {
    article_id: i64,
    count: i64,
}

impl ArticleView {
    fn new(
        article: &articles::Model,
        author: &users::Model,
        include_body: bool,
        favorited: bool,
        favorites_count: u64,
        following: bool,
    ) -> Self {
        Self {
            slug: article.slug.clone(),
            title: article.title.clone(),
            description: article.description.clone(),
            body: include_body.then(|| article.body.clone()),
            tag_list: article.tags(),
            created_at: article.created_at.to_rfc3339(),
            updated_at: article.updated_at.to_rfc3339(),
            status: article.status.clone(),
            published_at: article.published_at.map(|time| time.to_rfc3339()),
            revision: article.revision,
            favorited,
            favorites_count,
            author: ProfileView::new(author, following),
        }
    }

    pub async fn load_many(
        db: &DatabaseConnection,
        articles: &[articles::Model],
        viewer: Option<&users::Model>,
    ) -> std::result::Result<Vec<Self>, DbErr> {
        if articles.is_empty() {
            return Ok(Vec::new());
        }
        let article_ids: Vec<_> = articles.iter().map(|article| article.id).collect();
        let author_ids: Vec<_> = articles.iter().map(|article| article.author_id).collect();
        let authors: HashMap<_, _> = users::Entity::find()
            .filter(users::users::Column::Id.is_in(author_ids.clone()))
            .all(db)
            .await?
            .into_iter()
            .map(|author| (author.id, author))
            .collect();
        let counts: HashMap<_, _> = favorites::Entity::find()
            .select_only()
            .column(favorites::Column::ArticleId)
            .column_as(favorites::Column::Id.count(), "count")
            .filter(favorites::Column::ArticleId.is_in(article_ids.clone()))
            .group_by(favorites::Column::ArticleId)
            .into_model::<FavoriteCount>()
            .all(db)
            .await?
            .into_iter()
            .map(|row| (row.article_id, row.count as u64))
            .collect();
        let (favorited, following) = if let Some(viewer) = viewer {
            let favorited: HashSet<_> = favorites::Entity::find()
                .select_only()
                .column(favorites::Column::ArticleId)
                .filter(favorites::Column::UserId.eq(viewer.id))
                .filter(favorites::Column::ArticleId.is_in(article_ids))
                .into_tuple::<i64>()
                .all(db)
                .await?
                .into_iter()
                .collect();
            let following: HashSet<_> = follows::Entity::find()
                .select_only()
                .column(follows::Column::FollowedId)
                .filter(follows::Column::FollowerId.eq(viewer.id))
                .filter(follows::Column::FollowedId.is_in(author_ids))
                .into_tuple::<i64>()
                .all(db)
                .await?
                .into_iter()
                .collect();
            (favorited, following)
        } else {
            (HashSet::new(), HashSet::new())
        };
        articles
            .iter()
            .map(|article| {
                let author = authors
                    .get(&article.author_id)
                    .ok_or(DbErr::RecordNotFound("author".into()))?;
                Ok(Self::new(
                    article,
                    author,
                    false,
                    favorited.contains(&article.id),
                    *counts.get(&article.id).unwrap_or(&0),
                    following.contains(&article.author_id),
                ))
            })
            .collect()
    }

    pub async fn load(
        db: &DatabaseConnection,
        article: &articles::Model,
        viewer: Option<&users::Model>,
        include_body: bool,
    ) -> std::result::Result<Self, DbErr> {
        let author = if let Some(viewer) = viewer.filter(|user| user.id == article.author_id) {
            viewer.clone()
        } else {
            users::Entity::find_by_id(article.author_id)
                .one(db)
                .await?
                .ok_or(DbErr::RecordNotFound("author".into()))?
        };
        let favorited = if let Some(viewer) = viewer {
            favorites::Model::is_favorited(db, viewer.id, article.id).await?
        } else {
            false
        };
        let favorites_count = favorites::Model::count(db, article.id).await?;
        let following = if let Some(viewer) = viewer {
            follows::Model::is_following(db, viewer.id, author.id).await?
        } else {
            false
        };
        Ok(Self::new(
            article,
            &author,
            include_body,
            favorited,
            favorites_count,
            following,
        ))
    }
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CommentView {
    pub id: i64,
    pub created_at: String,
    pub updated_at: String,
    pub body: String,
    pub author: ProfileView,
}

impl CommentView {
    pub async fn load(
        db: &DatabaseConnection,
        comment: &comments::Model,
        viewer: Option<&users::Model>,
    ) -> std::result::Result<Self, DbErr> {
        let author = users::Entity::find_by_id(comment.author_id)
            .one(db)
            .await?
            .ok_or(DbErr::RecordNotFound("author".into()))?;
        Ok(Self {
            id: comment.id,
            created_at: comment.created_at.to_rfc3339(),
            updated_at: comment.updated_at.to_rfc3339(),
            body: comment.body.clone(),
            author: ProfileView::load(db, &author, viewer).await?,
        })
    }
}
