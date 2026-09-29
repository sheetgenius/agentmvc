CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TYPE job_status AS ENUM ('job_status_not_started', 'job_status_running', 'job_status_failed', 'job_status_timed_out', 'job_status_succeeded', 'job_status_retry');
CREATE FUNCTION ihp_user_id() RETURNS UUID AS $$SELECT NULLIF(current_setting('rls.ihp_user_id'), '')::uuid;$$ language SQL;
CREATE TYPE article_status AS ENUM ('draft', 'published');
CREATE TABLE users (
    id INT PRIMARY KEY NOT NULL
);
CREATE TABLE articles (
    id INT PRIMARY KEY NOT NULL,
    author_id INT NOT NULL,
    status article_status DEFAULT 'draft' NOT NULL,
    revision INT DEFAULT 1 NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE DEFAULT null
);
ALTER TABLE articles ADD CONSTRAINT articles_ref_author_id FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE CASCADE;
ALTER TABLE articles ADD CONSTRAINT revision_positive CHECK (revision >= 1);
ALTER TABLE articles ADD CONSTRAINT published_status CHECK (status = 'published' OR published_at IS NULL);
