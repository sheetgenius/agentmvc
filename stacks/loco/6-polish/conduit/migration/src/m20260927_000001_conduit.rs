use loco_rs::schema::*;
use sea_orm_migration::prelude::*;

#[derive(DeriveMigrationName)]
pub struct Migration;

#[async_trait::async_trait]
impl MigrationTrait for Migration {
    async fn up(&self, m: &SchemaManager) -> Result<(), DbErr> {
        create_table(
            m,
            "users",
            &[
                ("id", ColType::PkAuto),
                ("pid", ColType::UuidUniq),
                ("email", ColType::StringUniq),
                ("password", ColType::String),
                ("username", ColType::StringUniq),
                ("bio", ColType::TextNull),
                ("image", ColType::StringNull),
            ],
            &[],
        )
        .await?;
        create_table(
            m,
            "articles",
            &[
                ("id", ColType::PkAuto),
                ("slug", ColType::StringUniq),
                ("title", ColType::String),
                ("description", ColType::Text),
                ("body", ColType::Text),
                ("tag_list", ColType::Json),
            ],
            &[("users", "author_id")],
        )
        .await?;
        create_table(
            m,
            "comments",
            &[("id", ColType::PkAuto), ("body", ColType::Text)],
            &[("articles", "article_id"), ("users", "author_id")],
        )
        .await?;
        create_table(
            m,
            "follows",
            &[("id", ColType::PkAuto)],
            &[("users", "follower_id"), ("users", "followed_id")],
        )
        .await?;
        create_table(
            m,
            "favorites",
            &[("id", ColType::PkAuto)],
            &[("users", "user_id"), ("articles", "article_id")],
        )
        .await?;
        m.create_index(
            Index::create()
                .name("follows_pair")
                .table(Alias::new("follows"))
                .col(Alias::new("follower_id"))
                .col(Alias::new("followed_id"))
                .unique()
                .to_owned(),
        )
        .await?;
        m.create_index(
            Index::create()
                .name("favorites_pair")
                .table(Alias::new("favorites"))
                .col(Alias::new("user_id"))
                .col(Alias::new("article_id"))
                .unique()
                .to_owned(),
        )
        .await?;
        Ok(())
    }

    async fn down(&self, m: &SchemaManager) -> Result<(), DbErr> {
        for table in ["favorites", "follows", "comments", "articles", "users"] {
            drop_table(m, table).await?;
        }
        Ok(())
    }
}
