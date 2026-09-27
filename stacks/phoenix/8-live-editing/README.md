# Conduit API

Phoenix and Ecto implementation of the [RealWorld API](realworld_spec/docs/endpoints.md), including [article drafts and edit conflicts](realworld_spec/features/drafts/drafts.md), [article exports](realworld_spec/features/exports/exports.md), and [shared live editing](realworld_spec/features/live-editing/live-editing.md). `bin/check` starts a fresh PostgreSQL and runs all 17 Hurl files, the live protocol and browser checks, formatting, and compilation with warnings treated as errors.

## Run

```sh
export HOST_UID=$(id -u) HOST_GID=$(id -g)
docker compose up -d --wait db
docker compose run --rm app sh -lc 'mix deps.get && mix ecto.create && mix ecto.migrate'
docker compose up app
```

The API listens on `http://localhost:4102/api`. Stop it with `docker compose down -v`.

## Production image

```sh
docker build -t conduit:prod .
docker run --name conduit -p 127.0.0.1:4102:4102 \
  -e DATABASE_URL='postgresql://user:password@database-host/conduit' \
  -e SECRET_KEY_BASE="$(openssl rand -hex 64)" \
  -e PORT=4102 conduit:prod
```

Point `DATABASE_URL` at a reachable PostgreSQL database. The container applies pending migrations before serving on the given port; keep `SECRET_KEY_BASE` stable across restarts. Put an HTTPS reverse proxy in front of the loopback port and prevent direct public access to the container. `bin/check-production` builds the image and verifies it against a fresh database, all 17 acceptance files, the live protocol and browser checks, formatting, compilation, and all 13 security checks.

## Libraries and code

- Phoenix routes requests and renders JSON; Bandit serves HTTP and WebSocket; Jason encodes JSON.
- Ecto SQL and Postgrex persist users, articles, comments, follows and favorites in PostgreSQL.
- Bcrypt hashes passwords; Joken signs and validates JWTs; CORSPlug handles browser preflights; Hammer limits login attempts.
- Oban stores and processes export jobs in the same PostgreSQL database.

`Conduit.Accounts` owns user lookup, credentials and follows; `Conduit.Content` owns article visibility, author permissions, revisions, comments, favorites and tags; `Conduit.Exports` owns export requests and snapshots; `Conduit.Shares` owns editing links and shared saves. Ecto schemas define data and validation. `ConduitWeb.Router` names the API, controllers handle request and response details, `Presenter` shapes article JSON, and `Auth` and `FallbackController` handle shared authentication and errors.

## Security

Ecto changesets allowlist writable fields and validate their types. Controllers reject malformed JSON envelopes with 422 responses. Article pages accept at most 100 entries and ignore invalid or out-of-range pagination values. Phoenix adds secure response headers, including `X-Content-Type-Options: nosniff`. Hammer limits login attempts to 10 per email per minute, returning 429 and `Retry-After` when exceeded. Its ETS counters are local to one container; deployments with multiple replicas need a shared limiter or an ingress rate limit.

The production container serves HTTP and WebSocket on a private hop behind an HTTPS reverse proxy. The proxy must enforce HTTPS for public traffic and keep the container port private. Sobelow's `Config.HTTPS: HTTPS Not Enabled` finding applies to the container hop, so it is not an application HTTPS finding in that deployment. The baseline OSV scan reported no vulnerable lockfile packages.

## Performance

`perf/bench.sh` builds the production image and runs the fixed nine-scenario workload, writing measurements to `perf/latest/results.json`. Article pages fetch favorite counts and viewer relationships in page-wide queries. Single-article responses combine favorite count and viewer status in one aggregate, article fetches join their authors, and new articles and comments reuse the author already in hand. An index on `favorites.article_id` supports counts by article. Production logs warnings and errors without logging every request.

In the final benchmark, anonymous article lists ran at 3,480 requests/s versus 1,495 in the baseline, signed-in lists at 2,453 versus 790, and feeds at 2,407 versus 750. Their SQL statements per request fell from 23 to 4, 64 to 7, and 64 to 7 respectively. Single-article responses fell from 6 to 4 statements per request. Throughput varies across the short benchmark runs; the complete baseline and final results are in `perf/baseline/results.json` and `perf/latest/results.json`.

## Drafts and publishing

- `POST /api/articles` accepts `article.status` as `draft` or `published` (the default). Every article response includes `status`, `publishedAt` and `revision`.
- `GET /api/user/drafts` lists the signed-in author's drafts, newest first, with `limit` and `offset`. As with public article lists, entries omit `body`.
- `POST /api/articles/:slug/publish` publishes an author's draft, sets `publishedAt` and advances `revision`. Publishing an already published article leaves it unchanged.
- Drafts are visible by slug only to their author. Public lists, feeds, counts and tags include published articles only. Drafts cannot be commented on or favorited.
- `PUT /api/articles/:slug` accepts an optional integer `article.revision`. A matching value updates the article; a stale value returns `409` with the current article. Successful updates advance the revision even when the client omits it.

## Article exports

- `POST /api/user/exports` requires a token and no body. It creates a pending export and returns `202` with an ID, creation time, and null `completedAt` and `articles`.
- `GET /api/user/exports/:id` requires a token and returns only that user's export. Missing, malformed, and other users' IDs return `404`.
- Oban's `exports` queue runs two jobs at a time. Each job snapshots all of the author's articles, drafts included, oldest first, with slug, title, description, body, tags, status and comment count. Completion changes the status to `done` and records `completedAt`. Later article and comment changes do not alter the snapshot.
- The export row and Oban job are created in one database transaction. Development's `mix phx.server` and the production release both start Oban alongside Phoenix, so the same container serves requests and processes durable PostgreSQL jobs. Jobs queued before an app restart remain available when it starts again.

## Shared live editing

- An author creates or rotates an article link with `POST /api/articles/:slug/share` and revokes it with `DELETE` on the same path. Creation returns a new opaque ID and key. The database stores the key's SHA-256 hash, and a unique article ID allows one active link. Rotation and revocation close the old link's sockets.
- A holder supplies `X-Share-Key` to `GET` or `PUT /api/shares/:id/article`. The shared representation contains only `slug`, `title`, `body`, and `revision`. PUT requires those two text fields and the base revision. A stale save returns `409` with the current shared article. The stable share ID survives title and slug changes.
- `/api/shares/:id/live` upgrades to a JSON WebSocket. Its first message must be `{"type":"subscribe","key":"..."}`. Admission sends `ready` with the current article and presence count. Committed edits send `updated`; joins and leaves send `presence`. Invalid or revoked links close with `invalid_link` or `revoked`. The 101st authorized socket receives `room_full` and can retry after a slot opens.
- `Conduit.LiveRooms` keeps socket membership and the 100-connection cap in one in-memory GenServer. It serializes admission with broadcasts, monitors sockets for disconnects, and discards older revisions in each socket. Article data and revision checks remain in PostgreSQL and Ecto. The design assumes one backend instance.
- Both check scripts run the frozen frontend's protocol and Playwright tests in a Linux Playwright container through `bin/check-live`. The container shares the host network and copies the frontend into a temporary directory, so the source under `realworld_spec/` stays read-only.

## Spec choices

Slugs are title based with a random suffix, so duplicate titles remain distinct. Tags are stored in article order; the global tag list is distinct and sorted. JWTs expire after two hours; malformed tokens return 401. Follow and favorite operations are idempotent, and self follow is allowed. Lists default to 20 articles at offset zero and omit article bodies. Deletes return 204; invalid comment IDs return 404. CORS allows any origin.

The draft feature leaves status changes out of article updates: publishing uses the publish route, and articles cannot be unpublished. An author's draft comment list is empty; adding a comment or favorite returns 422. `publishedAt` is set at creation for new published articles and at first publication for drafts; pre-feature articles inherit their creation time during migration. The Hurl suite settles behavior where the prose is ambiguous.

Exports use integer IDs and snapshot the articles and counts when the job runs, not when the request arrives. If the author is deleted before a queued job runs, its export is deleted with the author and the job completes without a snapshot.
