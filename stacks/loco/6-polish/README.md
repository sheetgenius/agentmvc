# Conduit API

RealWorld's JSON API on Loco 1.2, SeaORM 2, Axum, and PostgreSQL. The server listens on port 4103.

## Run and check

Start PostgreSQL with `docker compose up -d --wait`, then run `cd conduit && cargo loco start`.

`bin/check` starts a fresh database and runs all 15 Hurl acceptance files, `cargo fmt --all -- --check`, and Clippy with warnings denied. `bin/check-production` builds the production image and runs the same acceptance files plus 13 security checks against the container.

## Read the code

- `conduit/src/app.rs` registers the Loco routes; `conduit/src/bin/main.rs` starts its CLI.
- `conduit/src/controllers/` handles HTTP extraction, authentication, validation, and RealWorld errors. Each resource has its own route file; `api.rs` holds the shared viewer extractors and error shape.
- `conduit/src/models/` holds user credentials, article queries and publishing, comments, follows, and favorites. `_entities/` contains the SeaORM row types and relationships generated from the schema.
- `conduit/src/views/realworld.rs` defines response shapes and loads the authors, favorite counts, and viewer relationships they need.
- `conduit/migration/src/` defines the schema and its draft and tag-index migrations. `conduit/config/` contains development and production settings.

## Domain rules

Articles start published unless `article.status` is `draft`. Drafts appear only in their author's `/api/user/drafts` list, never in public lists, feeds, counts, or tags. The author can read, edit, and delete a draft; other readers receive `404`. Comments and favorites cannot be added to drafts.

Publishing is an author-only transition through `POST /api/articles/:slug/publish`. It sets `publishedAt` and increments `revision`; publishing an already published article leaves it unchanged. Updates increment the revision and may include an expected revision. A stale revision returns `409` with the current article.

Article slugs combine the title with a UUID. Lists default to 20 articles at offset 0, count matches before pagination, and omit bodies. Author and favorited filters use username subqueries, so unknown usernames yield empty lists. Tags are a JSON list; a PostgreSQL GIN index supports tagged article queries. List responses load related data in batches.

User passwords are hashed. Registration requires a nonblank password; updates require at least eight characters. Empty bio and image strings become null. Loco signs tokens with HMAC-SHA512 and supplies secure response headers. Login attempts are limited to 20 per minute per case-insensitive email within each server process; deployments with multiple replicas need a shared limit at the edge.

## Production image

The image runs migrations before starting the server. Supply a PostgreSQL URL reachable from the container and a 128-character hexadecimal `SECRET_KEY_BASE`:

```sh
docker build -t conduit:production .
docker run --rm -p 4103:4103 \
  -e DATABASE_URL='postgres://user:password@database-host:5432/conduit' \
  -e SECRET_KEY_BASE="$(openssl rand -hex 64)" \
  -e PORT=4103 \
  conduit:production
```
