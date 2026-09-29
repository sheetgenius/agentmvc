CREATE TABLE IF NOT EXISTS users (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  username text NOT NULL UNIQUE CHECK (length(username) > 0),
  email text NOT NULL UNIQUE CHECK (length(email) > 0),
  password_hash text NOT NULL,
  bio text,
  image text
);
CREATE TABLE IF NOT EXISTS follows (
  follower_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  followed_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  PRIMARY KEY (follower_id, followed_id),
  CHECK (follower_id <> followed_id)
);
CREATE TABLE IF NOT EXISTS articles (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  slug text NOT NULL UNIQUE,
  title text NOT NULL CHECK (length(title) > 0),
  description text NOT NULL CHECK (length(description) > 0),
  body text NOT NULL CHECK (length(body) > 0),
  author_id bigint NOT NULL REFERENCES users(id),
  status text NOT NULL DEFAULT 'published' CHECK (status IN ('draft','published')),
  revision integer NOT NULL DEFAULT 1 CHECK (revision >= 1),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz,
  CHECK ((status = 'draft' AND published_at IS NULL) OR (status = 'published' AND published_at IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS articles_published_page ON articles (id DESC) WHERE status = 'published';
CREATE INDEX IF NOT EXISTS articles_author_page ON articles (author_id, id DESC);
CREATE TABLE IF NOT EXISTS article_tags (
  article_id bigint NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  tag text NOT NULL CHECK (length(tag) > 0),
  PRIMARY KEY (article_id, tag)
);
CREATE INDEX IF NOT EXISTS article_tags_filter ON article_tags (tag, article_id);
CREATE TABLE IF NOT EXISTS favorites (
  user_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  article_id bigint NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, article_id)
);
CREATE INDEX IF NOT EXISTS favorites_article ON favorites (article_id);
CREATE TABLE IF NOT EXISTS comments (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  article_id bigint NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  author_id bigint NOT NULL REFERENCES users(id),
  body text NOT NULL CHECK (length(body) > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS comments_article ON comments (article_id, id);
CREATE TABLE IF NOT EXISTS exports (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id bigint NOT NULL REFERENCES users(id),
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','done')),
  created_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  articles jsonb,
  CHECK ((status = 'pending' AND completed_at IS NULL AND articles IS NULL)
      OR (status = 'done' AND completed_at IS NOT NULL AND articles IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS exports_pending ON exports (id) WHERE status = 'pending';
CREATE TABLE IF NOT EXISTS shares (
  id text PRIMARY KEY,
  article_id bigint NOT NULL UNIQUE REFERENCES articles(id) ON DELETE CASCADE,
  key_hash text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS login_failures (
  email text PRIMARY KEY,
  failures integer NOT NULL DEFAULT 0,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION profile_payload(u users, viewer bigint)
RETURNS jsonb LANGUAGE sql STABLE AS $$
 SELECT jsonb_build_object('username',u.username,'bio',u.bio,'image',u.image,
   'following', EXISTS(SELECT 1 FROM follows f WHERE f.follower_id=viewer AND f.followed_id=u.id))
$$;

CREATE OR REPLACE FUNCTION article_payload(a articles, viewer bigint, include_body boolean)
RETURNS jsonb LANGUAGE sql STABLE AS $$
 SELECT jsonb_build_object(
  'slug',a.slug,'title',a.title,'description',a.description,
  'tagList',COALESCE((SELECT jsonb_agg(t.tag ORDER BY t.tag) FROM article_tags t WHERE t.article_id=a.id),'[]'::jsonb),
  'createdAt',a.created_at,'updatedAt',a.updated_at,
  'publishedAt',a.published_at,'status',a.status,'revision',a.revision,
  'favorited',EXISTS(SELECT 1 FROM favorites f WHERE f.article_id=a.id AND f.user_id=viewer),
  'favoritesCount',(SELECT count(*) FROM favorites f WHERE f.article_id=a.id),
  'author',profile_payload(u,viewer)) ||
  CASE WHEN include_body THEN jsonb_build_object('body',a.body) ELSE '{}'::jsonb END
 FROM users u WHERE u.id=a.author_id
$$;

CREATE OR REPLACE FUNCTION shared_payload(a articles)
RETURNS jsonb LANGUAGE sql STABLE AS $$
 SELECT jsonb_build_object('slug',a.slug,'title',a.title,'body',a.body,'revision',a.revision)
$$;

CREATE OR REPLACE FUNCTION replace_article_tags(article bigint, tags jsonb)
RETURNS boolean LANGUAGE plpgsql AS $$
BEGIN
 DELETE FROM article_tags WHERE article_id=article;
 INSERT INTO article_tags(article_id,tag)
 SELECT article, value FROM jsonb_array_elements_text(tags) AS value WHERE length(value)>0
 ON CONFLICT DO NOTHING;
 RETURN true;
END
$$;
