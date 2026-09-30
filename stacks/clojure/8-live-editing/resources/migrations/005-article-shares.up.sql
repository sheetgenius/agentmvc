CREATE TABLE article_shares (
  id TEXT PRIMARY KEY,
  article_id BIGINT NOT NULL UNIQUE REFERENCES articles(id) ON DELETE CASCADE,
  key_hash TEXT NOT NULL
);
