CREATE TYPE article_status AS ENUM ('draft', 'published');
CREATE TABLE users (id SERIAL PRIMARY KEY NOT NULL);
CREATE TABLE articles (
    id SERIAL PRIMARY KEY NOT NULL,
    author_id INT NOT NULL,
    status article_status NOT NULL DEFAULT 'draft',
    revision INT NOT NULL DEFAULT 1,
    published_at TIMESTAMP WITH TIME ZONE
);
ALTER TABLE articles ADD CONSTRAINT articles_ref_author_id FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE CASCADE;
ALTER TABLE articles ADD CONSTRAINT revision_positive CHECK (revision >= 1);
ALTER TABLE articles ADD CONSTRAINT published_status CHECK (status = 'published' OR published_at IS NULL);
