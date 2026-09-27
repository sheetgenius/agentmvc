# Conduit API

RealWorld's JSON API on Loco 1.2, SeaORM 2, Axum, and PostgreSQL. The server listens on port 4103.

## Run and check

Start PostgreSQL with `docker compose up -d --wait`, then run `cd conduit && cargo loco start --server-and-worker`.

`bin/check` starts a fresh database and runs all 17 Hurl acceptance files, the shared live-editing protocol check, 3 Playwright browser checks, `cargo fmt --all -- --check`, and Clippy with warnings denied. `bin/check-production` builds the production image and runs those checks plus 13 security checks against the container. Each gate removes its database and app when finished. The browser checks run in a separate Playwright image through `bin/check-live`; the frozen client and tests are copied into that temporary harness.

## Read the code

- `conduit/src/app.rs` registers the Loco routes; `conduit/src/bin/main.rs` starts its CLI.
- `conduit/src/controllers/` handles HTTP extraction, authentication, validation, and RealWorld errors. Each resource has its own route file; `api.rs` holds the shared viewer extractors and error shape.
- `conduit/src/models/` holds user credentials, article queries and publishing, comments, follows, favorites, and export snapshots. `_entities/` contains the SeaORM row types and relationships generated from the schema.
- `conduit/src/models/article_shares.rs` owns editing-link storage and key verification; `live_rooms.rs` owns in-memory presence and socket admission. `conduit/src/controllers/shares.rs` exposes the shared HTTP and WebSocket contract.
- `conduit/src/views/realworld.rs` defines response shapes and loads the authors, favorite counts, and viewer relationships they need.
- `conduit/src/workers/` contains the export job. `conduit/migration/src/` defines the schema; `conduit/config/` contains development and production settings.

## Domain rules

Articles start published unless `article.status` is `draft`. Drafts appear only in their author's `/api/user/drafts` list, never in public lists, feeds, counts, or tags. The author can read, edit, and delete a draft; other readers receive `404`. Comments and favorites cannot be added to drafts.

Publishing is an author-only transition through `POST /api/articles/:slug/publish`. It sets `publishedAt` and increments `revision`; publishing an already published article leaves it unchanged. Updates increment the revision and may include an expected revision. A stale revision returns `409` with the current article.

Article slugs combine the title with a UUID. Lists default to 20 articles at offset 0, count matches before pagination, and omit bodies. Author and favorited filters use username subqueries, so unknown usernames yield empty lists. Tags are a JSON list; a PostgreSQL GIN index supports tagged article queries. List responses load related data in batches.

User passwords are hashed. Registration requires a nonblank password; updates require at least eight characters. Empty bio and image strings become null. Loco signs tokens with HMAC-SHA512 and supplies secure response headers. Login attempts are limited to 20 per minute per case-insensitive email within each server process; deployments with multiple replicas need a shared limit at the edge.

## Article exports

`POST /api/user/exports` requires a token and takes no body. It returns `202` with a new export whose status is `pending`, and whose `completedAt` and `articles` are null. `GET /api/user/exports/:id` requires a token and returns that user's export. Another user's ID, an unknown ID, or a malformed ID returns `404` with `export: ["not found"]`. Missing authentication returns the usual `401` token error.

The background job captures every article the user authored, drafts included, oldest first, with its slug, title, description, body, tag list, status, and comment count. Once stored, the JSON snapshot does not change when articles or comments change. `done` means `completedAt` is set; a user with no articles gets an empty array. Export IDs are database integers and are treated as opaque API identifiers. Oldest first means article creation order (ID order); the snapshot is taken when the job runs, using one repeatable-read transaction.

Loco's `BackgroundWorker` queues export IDs in PostgreSQL using the same `DATABASE_URL` as the app. Development and production both use `BackgroundQueue`; start the server with `--server-and-worker` to process jobs in the same process. The queue tables are set up at boot, and a reaper returns jobs left in processing after a worker crash to the queue. The production image starts one server-and-worker process after migrations, with no additional service or environment variable.

## Shared article editing

The author creates or rotates an editing link with `POST /api/articles/:slug/share` and revokes it with `DELETE /api/articles/:slug/share`. The response gives a stable share ID and a random key once. The database stores only its SHA-256 hash, with one active link per article ID. Rotation invalidates the prior link; a title edit can change the slug without changing which article the share ID identifies. These link-management routes use the same author and draft visibility rules as article mutations.

A link holder sends `X-Share-Key` to `GET` or `PUT /api/shares/:id/article`. The shared response contains only slug, title, body, and revision. The `PUT` requires title, body, and the base revision, accepts no other fields, and locks the article row before applying a change. A stale base revision returns `409` with the current shared article; a successful save increments revision once. The key is verified before validation or article data is returned. The existing author-only article update and publish routes also notify live editors after commit.

`/api/shares/:id/live` is a WebSocket that requires a first `subscribe` message carrying the key. Admission reads the current article while holding the room lock, so an edit concurrent with subscription appears in `ready` or a later `updated` message. Per-socket revision filtering prevents an older update from following a newer one; a lagging socket reloads the latest article. The room counts admitted sockets in memory and caps them at 100, returning `room_full` to the next valid subscriber. Revocation sends `revoked` and closes active sockets. Presence is per connection and lasts only for this backend process; the production image serves HTTP and WebSockets together with PostgreSQL as its only service.

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
