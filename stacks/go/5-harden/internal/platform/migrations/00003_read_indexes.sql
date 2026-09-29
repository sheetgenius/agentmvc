-- +goose Up
CREATE INDEX articles_status_recent_idx ON articles (status, created_at DESC, id DESC);
CREATE INDEX article_tags_tag_article_idx ON article_tags (tag, article_id);
CREATE INDEX favorites_article_user_idx ON favorites (article_id, user_id);
CREATE INDEX comments_article_id_idx ON comments (article_id, id);

-- +goose Down
DROP INDEX comments_article_id_idx;
DROP INDEX favorites_article_user_idx;
DROP INDEX article_tags_tag_article_idx;
DROP INDEX articles_status_recent_idx;
