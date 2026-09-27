use loco_rs::prelude::*;
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
        Ok(Self {
            username: user.username.clone(),
            bio: user.bio.clone(),
            image: user.image.clone(),
            following,
        })
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

impl ArticleView {
    pub async fn load(
        db: &DatabaseConnection,
        article: &articles::Model,
        viewer: Option<&users::Model>,
        include_body: bool,
    ) -> std::result::Result<Self, DbErr> {
        let author = users::Entity::find_by_id(article.author_id)
            .one(db)
            .await?
            .ok_or(DbErr::RecordNotFound("author".into()))?;
        let favorited = if let Some(viewer) = viewer {
            favorites::Model::is_favorited(db, viewer.id, article.id).await?
        } else {
            false
        };
        Ok(Self {
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
            favorites_count: favorites::Model::count(db, article.id).await?,
            author: ProfileView::load(db, &author, viewer).await?,
        })
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
