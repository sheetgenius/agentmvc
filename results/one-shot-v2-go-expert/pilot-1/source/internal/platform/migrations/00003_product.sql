-- +goose Up
CREATE TABLE users (
 id bigserial PRIMARY KEY, username text NOT NULL UNIQUE CHECK (length(username)>0),
 email text NOT NULL UNIQUE CHECK (length(email)>0), password_hash text NOT NULL,
 bio text, image text
);
CREATE TABLE follows (follower_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 followed_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 PRIMARY KEY(follower_id,followed_id), CHECK(follower_id<>followed_id));
CREATE TABLE articles (
 id bigserial PRIMARY KEY, author_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 slug text NOT NULL UNIQUE, title text NOT NULL CHECK(length(title)>0),
 description text NOT NULL CHECK(length(description)>0), body text NOT NULL CHECK(length(body)>0),
 status text NOT NULL CHECK(status IN ('draft','published')), revision integer NOT NULL DEFAULT 1 CHECK(revision>0),
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), published_at timestamptz,
 CHECK ((status='draft' AND published_at IS NULL) OR (status='published' AND published_at IS NOT NULL))
);
CREATE INDEX articles_listing ON articles(status,created_at DESC,id DESC);
CREATE INDEX articles_author ON articles(author_id,status,created_at DESC,id DESC);
CREATE TABLE article_tags (article_id bigint NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
 tag text NOT NULL, PRIMARY KEY(article_id,tag));
CREATE INDEX article_tags_tag ON article_tags(tag,article_id);
CREATE TABLE favorites (user_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 article_id bigint NOT NULL REFERENCES articles(id) ON DELETE CASCADE, PRIMARY KEY(user_id,article_id));
CREATE INDEX favorites_article ON favorites(article_id);
CREATE TABLE comments (id bigserial PRIMARY KEY, article_id bigint NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
 author_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE, body text NOT NULL CHECK(length(body)>0),
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX comments_article ON comments(article_id,id);
CREATE TABLE shares (id text PRIMARY KEY, article_id bigint NOT NULL UNIQUE REFERENCES articles(id) ON DELETE CASCADE,
 key_hash bytea NOT NULL);
CREATE TABLE exports (id bigserial PRIMARY KEY, user_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','done')),
 created_at timestamptz NOT NULL DEFAULT now(), completed_at timestamptz, articles jsonb);
-- +goose Down
DROP TABLE exports,shares,comments,favorites,article_tags,articles,follows,users;
