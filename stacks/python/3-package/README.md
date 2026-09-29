# Conduit API

Run `harness/db.sh start 4111`, then `harness/python.sh start`. The API listens on
port 4111. `bin/check` starts a fresh database and server, runs all 15 official
Hurl files plus Ruff and Django tests, and stops its services.

## Production image

Build and run with PostgreSQL on a Docker network:

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

The image applies Django migrations before starting the API and queue worker.
`bin/check-production` builds it, starts a fresh PostgreSQL database, runs all
15 Hurl files, and cleans up its containers.

## Stack

- Django: users, models, relationships, migrations, password hashing, and tests.
- Django Ninja: typed HTTP routes, request schemas, and error hooks.
- PostgreSQL and psycopg: durable data and ordered tag arrays.
- PyJWT: signed `Token` authentication with a 30-day expiry.
- django-cors-headers: browser preflight and cross-origin headers.
- Uvicorn and Channels: ASGI serving and WebSocket wiring supplied by the scaffold.
- Procrastinate: PostgreSQL job wiring supplied by the scaffold; this API has no background jobs.
- dj-database-url: database configuration from `DATABASE_URL`.
- argon2-cffi: Argon2 password hashes.
- Ruff: formatting and linting. Pytest, pytest-django, and httpx support local tests;
  Bandit and pip-audit support the prepared security checks.

## Code map

`conduit/models.py` describes users, follows, articles, favorites, tags, and comments.
`conduit/api.py` holds the HTTP contract: inputs, permissions, response shapes, and
routes. `conduit/tests.py` covers invalid tokens. `config/settings.py` and
`config/urls.py` install the app and mount the API. `bin/check` runs the prepared
development gate. The initial migration records the schema.

The rule map is small: `Article.set_title` owns slug changes, `Article.publish`
owns the transition to publication, and `ArticleQuerySet.published` selects public
articles; `validate_identity` and `password` own account
validation; `viewer`, `article_or_404`, and `owned` own access checks;
`article_page` owns list counts and pagination; the `*_data` functions own
response shapes. The route functions connect those rules to the HTTP contract.

## Drafts and revisions

`POST /api/articles` accepts `status: "draft"` or `"published"` (the default).
Every article response includes `status`, `publishedAt`, and `revision`. Drafts
have a null publication time and are visible through `GET /api/articles/{slug}`
only to their author. They are excluded from public lists, feeds, and tags.
`GET /api/user/drafts` lists the authenticated author's drafts, newest first,
with the same pagination and summary shape as the article list.

The author publishes through `POST /api/articles/{slug}/publish`. Publishing a
draft records its first publication time and advances its revision; repeating the
request leaves both unchanged. Drafts cannot be commented on or favorited.
`PUT /api/articles/{slug}` advances the revision on every successful update. An
optional integer `revision` protects the edit: a stale value returns 409 with
the current article, while omitting it keeps the previous last-write-wins behavior.
The update locks the article row while comparing and writing the revision.

## Contract choices

Duplicate titles get distinct readable slugs; changing a title changes its slug.
Article lists and feeds omit `body`, while single articles include it. Tags keep
their input order on an article; `/api/tags` lists tags currently used by articles
in alphabetical order. Empty profile bio and image values become `null`. Invalid
or missing tokens get a 401; duplicate usernames or email addresses get a 409.
Pagination counts the full filtered set and uses a default page size of 20.
Browser origins are allowed because this public API is intended for separate
frontends. Email domains are normalized on registration, login, and update.
An author may list a draft's comments (an empty list), but cannot add or delete
comments on it. A non-integer revision, including a boolean, is invalid. For
articles created before the draft migration, `publishedAt` is set to the time
the migration runs; their original publication time was not recorded.

This started from the product-free Django scaffold. The Conduit models, routes,
validation, authentication, migration, test, CORS support, and gate were added.
