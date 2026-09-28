use sea_orm_migration::prelude::*;

#[derive(DeriveMigrationName)]
pub struct Migration;

#[async_trait::async_trait]
impl MigrationTrait for Migration {
    async fn up(&self, m: &SchemaManager) -> Result<(), DbErr> {
        m.get_connection().execute_unprepared(r#"
            CREATE TABLE rw_users (id BIGSERIAL PRIMARY KEY, username TEXT NOT NULL UNIQUE, email TEXT NOT NULL UNIQUE, password TEXT NOT NULL, bio TEXT, image TEXT);
            CREATE TABLE rw_follows (follower BIGINT REFERENCES rw_users(id) ON DELETE CASCADE, followed BIGINT REFERENCES rw_users(id) ON DELETE CASCADE, PRIMARY KEY(follower, followed));
            CREATE TABLE rw_articles (id BIGSERIAL PRIMARY KEY, author_id BIGINT NOT NULL REFERENCES rw_users(id), slug TEXT NOT NULL UNIQUE, title TEXT NOT NULL, description TEXT NOT NULL, body TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'published', revision BIGINT NOT NULL DEFAULT 1, published_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now());
            CREATE TABLE rw_tags (article_id BIGINT REFERENCES rw_articles(id) ON DELETE CASCADE, tag TEXT NOT NULL, position INT NOT NULL, PRIMARY KEY(article_id, tag));
            CREATE TABLE rw_favorites (article_id BIGINT REFERENCES rw_articles(id) ON DELETE CASCADE, user_id BIGINT REFERENCES rw_users(id) ON DELETE CASCADE, PRIMARY KEY(article_id, user_id));
            CREATE TABLE rw_comments (id BIGSERIAL PRIMARY KEY, article_id BIGINT NOT NULL REFERENCES rw_articles(id) ON DELETE CASCADE, author_id BIGINT NOT NULL REFERENCES rw_users(id), body TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now());
            CREATE TABLE rw_exports (id TEXT PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES rw_users(id), status TEXT NOT NULL DEFAULT 'pending', created_at TIMESTAMPTZ NOT NULL DEFAULT now(), completed_at TIMESTAMPTZ, articles JSONB);
            CREATE TABLE rw_shares (id TEXT PRIMARY KEY, article_id BIGINT NOT NULL UNIQUE REFERENCES rw_articles(id) ON DELETE CASCADE, key_hash TEXT NOT NULL);
        "#).await?;
        Ok(())
    }
    async fn down(&self, m: &SchemaManager) -> Result<(), DbErr> {
        m.get_connection().execute_unprepared("DROP TABLE rw_shares, rw_exports, rw_comments, rw_favorites, rw_tags, rw_articles, rw_follows, rw_users CASCADE").await?;
        Ok(())
    }
}
