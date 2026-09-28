CREATE TABLE users (id SERIAL PRIMARY KEY NOT NULL, username TEXT NOT NULL UNIQUE, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, bio TEXT, image TEXT, token TEXT NOT NULL UNIQUE, failed_logins INT NOT NULL DEFAULT 0);
CREATE TABLE follows (follower_id INTEGER NOT NULL, followed_id INTEGER NOT NULL, PRIMARY KEY (follower_id, followed_id));
CREATE TABLE articles (id SERIAL PRIMARY KEY NOT NULL, author_id INTEGER NOT NULL, slug TEXT NOT NULL UNIQUE, title TEXT NOT NULL, description TEXT NOT NULL, body TEXT NOT NULL, tags TEXT[] NOT NULL DEFAULT '{}', status TEXT NOT NULL DEFAULT 'published', revision INT NOT NULL DEFAULT 1, created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), published_at TIMESTAMP WITH TIME ZONE);
CREATE TABLE comments (id SERIAL PRIMARY KEY NOT NULL, article_id INTEGER NOT NULL, author_id INTEGER NOT NULL, body TEXT NOT NULL, created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now());
CREATE TABLE favorites (user_id INTEGER NOT NULL, article_id INTEGER NOT NULL, PRIMARY KEY (user_id, article_id));
CREATE TABLE shares (id TEXT PRIMARY KEY NOT NULL, article_id INTEGER NOT NULL UNIQUE, key_hash TEXT NOT NULL);
CREATE TABLE exports (id SERIAL PRIMARY KEY NOT NULL, user_id INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), completed_at TIMESTAMP WITH TIME ZONE, articles JSONB);
CREATE TABLE export_jobs (id UUID DEFAULT gen_random_uuid() PRIMARY KEY NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, status JOB_STATUS DEFAULT 'job_status_not_started' NOT NULL, last_error TEXT, attempts_count INT DEFAULT 0 NOT NULL, locked_at TIMESTAMP WITH TIME ZONE, locked_by UUID, run_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, export_id INTEGER NOT NULL);
CREATE FUNCTION user_json(user_id INTEGER) RETURNS JSONB LANGUAGE SQL AS $$
    SELECT jsonb_build_object('email', email, 'token', token, 'username', username, 'bio', bio, 'image', image) FROM users WHERE id = user_id
$$;
CREATE FUNCTION profile_json(user_id INTEGER, viewer_id INTEGER) RETURNS JSONB LANGUAGE SQL AS $$
    SELECT jsonb_build_object('username', u.username, 'bio', u.bio, 'image', u.image,
      'following', EXISTS (SELECT 1 FROM follows f WHERE f.follower_id = viewer_id AND f.followed_id = u.id)) FROM users u WHERE u.id = user_id
$$;
CREATE FUNCTION article_json(article_id INTEGER, viewer_id INTEGER, with_body BOOLEAN) RETURNS JSONB LANGUAGE SQL AS $$
    SELECT CASE WHEN with_body THEN payload ELSE payload - 'body' END FROM (
      SELECT jsonb_build_object('slug', a.slug, 'title', a.title, 'description', a.description, 'body', a.body,
        'tagList', a.tags, 'status', a.status, 'revision', a.revision, 'createdAt', a.created_at,
        'updatedAt', a.updated_at, 'publishedAt', a.published_at,
        'favorited', EXISTS (SELECT 1 FROM favorites f WHERE f.user_id = viewer_id AND f.article_id = a.id),
        'favoritesCount', (SELECT count(*) FROM favorites f WHERE f.article_id = a.id),
        'author', profile_json(a.author_id, viewer_id)) AS payload FROM articles a WHERE a.id = article_id
    ) s
$$;
CREATE FUNCTION comment_json(comment_id INTEGER, viewer_id INTEGER) RETURNS JSONB LANGUAGE SQL AS $$
    SELECT jsonb_build_object('id', c.id, 'createdAt', c.created_at, 'updatedAt', c.updated_at,
      'body', c.body, 'author', profile_json(c.author_id, viewer_id)) FROM comments c WHERE c.id = comment_id
$$;
CREATE FUNCTION shared_article_json(article_id INTEGER) RETURNS JSONB LANGUAGE SQL AS $$
    SELECT jsonb_build_object('slug', slug, 'title', title, 'body', body, 'revision', revision) FROM articles WHERE id = article_id
$$;
CREATE FUNCTION export_json(export_id INTEGER) RETURNS JSONB LANGUAGE SQL AS $$
    SELECT jsonb_build_object('id', id, 'status', status, 'createdAt', created_at, 'completedAt', completed_at, 'articles', articles) FROM exports WHERE id = export_id
$$;
