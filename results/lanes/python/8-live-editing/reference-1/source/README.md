# Conduit API

A RealWorld API built with Django 6, Django Ninja, PostgreSQL, and Uvicorn.
Django owns the data model, relationships, password hashes, and migrations;
Ninja owns typed request bodies, routes, authentication hooks, and API errors.

## Run and verify

```sh
harness/db.sh start 4111
harness/python.sh start
```

The API listens on `0.0.0.0:4111`. `bin/check` starts a fresh development
database and runs the 17 Hurl files, shared live protocol and four browser
tests, 13 security files, Ruff, Django's system check, and project tests.
`bin/check-production` builds the image and runs the same shared checks against
a fresh production container.
`bin/dev` and `bin/serve` apply Django and Procrastinate migrations, then start
the web server and `manage.py procrastinate worker`. Development reloads the web server;
restart `bin/dev` after changing a job.

## Code map

- `conduit/models.py`: users, follows, articles, favorites, comments, login attempts, exports, and article queries.
- `conduit/accounts.py`: account and profile schemas, tokens, identity validation, and routes.
- `conduit/articles.py`: article and comment schemas, response shapes, access checks, and routes.
- `conduit/exports.py`: authenticated export routes and response shape.
- `conduit/sharing.py`: editing link permissions, shared article shape, revision-checked saves, and post-commit events.
- `conduit/live.py`: WebSocket subscription, presence, and room capacity.
- `conduit/tasks.py`: Procrastinate job that completes exports.
- `conduit/http.py`: shared pagination bounds and API error responses.
- `conduit/api.py`: health route and router registration.
- `conduit/tests.py`: focused authentication, rate limit, and pagination tests.
- `conduit/migrations/`: schema history, including drafts, revisions, login attempts, exports, and editing links.
- `config/`: Django settings, URLs, and ASGI entry point.
- `bin/dev` and `bin/serve`: migrate and run Uvicorn plus the worker in development and production.
- `pyproject.toml` and `uv.lock`: runtime and Ruff dependencies.
- `Dockerfile`: locked, non-root production image.

## Rule map

`Article.set_title` creates a unique readable slug, and `Article.publish`
records the first publication time and advances the revision. The article
queryset's `published` method excludes drafts; `with_viewer` loads favorite
counts, the viewer's favorite state, and author follow state with the article
query. List pages defer article bodies.

`LoginAttempt.failed` counts failed logins per normalized email in PostgreSQL.
`accounts.validate_identity` and `accounts.password` validate account changes;
`accounts.viewer` reads signed 30-day HS256 tokens. In `articles.py`,
`article_or_404`, `require_published`, and `owned` enforce visibility and
permissions; `article_page` owns counts and pagination; the `*_data` functions
own response shapes. Routes connect these rules to HTTP methods.

`POST /api/user/exports` creates a pending export and queues its job in the
same PostgreSQL transaction. `GET /api/user/exports/{id}` reads only the
current user's export; missing, foreign, and malformed IDs return 404. Both
routes require a token. `Export.complete` captures all articles authored when
the job runs, drafts included, oldest first, with tags and comment counts.
The JSON snapshot stays unchanged after later edits or deletions. A pending
export has `completedAt` and `articles` set to null; a finished one has
`status: "done"`. Article order breaks timestamp ties by ID, a choice where
the suite is silent.

`EditingLink` gives an article one active capability. Its ID points to the
article's database row, so title changes do not break the link. The server
returns a fresh 256-bit random key only when the author creates or rotates a
link and stores its SHA-256 hash. The author's normal article visibility and
ownership checks protect link management. A holder can read and update only
the shared title and body; unknown, wrong, and revoked credentials all return
404. The shared PUT checks the key before parsing fields, locks the article,
checks its revision, and saves one increment or returns 409 with the current
shared snapshot. Both shared and author edits publish socket updates after
commit. Rotation, revocation, and article deletion close the old link's sockets.

`EditingConsumer` registers for room events before reading its authorized
snapshot, so an edit racing with subscription appears in `ready` or a later
`updated`. It sends no article or presence before the first valid `subscribe`.
Rooms count sockets in the single ASGI process and admit up to 100 per article;
presence events read the current room count when delivered. The in-memory
Channels layer broadcasts updates and revocations. Socket revisions discard
late older events. The PostgreSQL article row remains the source of truth.

## Contract choices

Articles are published by default. An author can create a draft, list their
drafts at `/api/user/drafts`, and publish one at
`POST /api/articles/{slug}/publish`. Only its author can read a draft by slug.
Drafts are absent from public lists, feeds, and tags, and cannot be favorited
or commented on. Publishing twice leaves the publication time and revision
unchanged.

Every successful article update advances its revision. An optional integer
`revision` makes the update conditional; a stale value returns 409 with the
current article. Updates lock the article row while checking and writing it.
Lists contain article summaries without `body` and count the full filtered
result before pagination. Article tags keep input order; `/api/tags` returns
currently used public tags alphabetically.

Duplicate titles get distinct slugs, and changing a title changes its slug.
Invalid or missing tokens return 401, duplicate usernames or email addresses
return 409, and lists default to 20 articles with a maximum page size of 1,000.
Email domains are normalized on registration, login, and update. Failed logins
return the same error for known and unknown accounts; the sixth failure within
15 minutes returns 429. A valid password still works during that window.

## Production image

The image applies migrations, then runs Uvicorn and a Procrastinate worker as
a non-root user in the same container. Procrastinate stores jobs in the app's
PostgreSQL database, so queued exports survive restarts. It requires
`DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT`. For a local Docker deployment:

```sh
docker build -t conduit-api .
docker network create conduit
docker volume create conduit-data
DB_PASSWORD="$(openssl rand -hex 32)"
docker run -d --name conduit-db --network conduit \
  -e POSTGRES_USER=conduit -e POSTGRES_PASSWORD="$DB_PASSWORD" -e POSTGRES_DB=conduit \
  -v conduit-data:/var/lib/postgresql/data postgres:17
docker run --rm --network conduit -p 4111:4111 \
  -e DATABASE_URL="postgresql://conduit:${DB_PASSWORD}@conduit-db:5432/conduit" \
  -e SECRET_KEY_BASE="$(openssl rand -hex 64)" -e PORT=4111 conduit-api
```
