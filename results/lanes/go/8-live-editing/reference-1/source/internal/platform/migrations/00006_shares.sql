-- +goose Up
CREATE TABLE article_shares (
    id text PRIMARY KEY,
    article_id bigint NOT NULL UNIQUE REFERENCES articles(id) ON DELETE CASCADE,
    key_hash bytea NOT NULL
);

-- +goose Down
DROP TABLE article_shares;
