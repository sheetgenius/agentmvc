# Conduit API

This is an unscored reviewer revision of the preserved eight-step build. It rejects non-object article updates and extra shared-envelope fields, maps oversized comment IDs to `404`, and reserves login admission atomically before password work.

Set `DATABASE_URL` (a PostgreSQL URL), `SECRET_KEY_BASE`, and optionally `PORT` (default 4112). Run `bin/dev` for reload on save, or `bin/serve` for a steady server. `bin/check` runs the development gate and then the production gate. `bin/check-production` runs lint and formatting, builds the image, and checks it. Each gate uses a fresh database and runs all 17 acceptance files (237 requests), the live protocol check, four browser tests, and all 13 security files (52 requests); the development gate also runs the Clojure unit test.

## Production image

```sh
docker build -t conduit-api .
docker run --rm -p 4112:4112 \
  -e DATABASE_URL='postgresql://conduit:password@db.example:5432/conduit' \
  -e SECRET_KEY_BASE="$(openssl rand -hex 64)" \
  -e PORT=4112 conduit-api
```

Use a PostgreSQL host reachable from the container. The database must exist; the app creates its schema before serving requests. The image contains the application and migrations, so it needs no bind mount.

## Libraries

- Clojure is the application language. Ring and Jetty serve HTTP and WebSockets; Reitit routes HTTP, with its middleware and Muuntaja handling parameters and JSON.
- Integrant owns startup and shutdown. next.jdbc handles queries, HoneySQL builds partial updates, HikariCP pools PostgreSQL connections, the PostgreSQL driver connects, Migratus runs the schema, and Proletarian runs durable PostgreSQL jobs.
- Buddy hashers stores password hashes; Buddy sign issues and verifies JWTs. Pinned Bouncy Castle overrides Buddy's older transitive versions. SLF4J Simple logs.
- Caffeine bounds the five-minute failed-login counter to 10,000 email addresses.
- Development uses integrant.repl and tools.namespace. Cognitect test runner, clj-kondo, cljfmt, and tools.build are development and build tools.

## Security

JWT signatures and expiry are checked before account lookup; database errors still surface as server errors. User and article writes select client-owned fields, and SQL values are bound as parameters. Malformed JSON receives a JSON `400` response; API responses include `X-Content-Type-Options: nosniff`. The login counter admits up to ten attempts for an email address in its five-minute window, reserving each slot before password verification. Successful authentication resets the counter. It is local to each app process and resets on restart.

`bin/dependency-scan` checks the resolved runtime Maven inventory with OSV-Scanner. No dedicated Clojure security static analyzer is supplied. `bin/check` runs clj-kondo and cljfmt with their default settings.

## Code

`http.clj` names the routes and wraps JSON errors, CORS, and authentication. `users.clj` owns accounts, login, profiles, follows, and the shared profile response shape used by article and comment authors. `articles.clj` owns articles, tags, comments, favorites, feeds, and the shared article row update rule. `shares.clj` owns editing links, key checks, and shared saves. `live.clj` owns WebSocket admission, presence, and broadcasts. `exports.clj` owns export creation, snapshots, and responses. `domain.clj` holds shared validation and authorization failures; `store.clj` sets the next.jdbc result shape and timestamp format. `system.clj`, `config.clj`, `database.clj`, `migrations.clj`, and `main.clj` start the service and worker. `resources/migrations/` defines the relational and queue schema.

## Performance

Article presentation fetches author, follow, and favorite details for a whole page in one query, then fetches its ordered tags in another. List pages use four SQL statements anonymously or five with authentication, including the count query. The queries read current PostgreSQL data on every request.

## Drafts and revisions

`POST /api/articles` accepts `article.status` as `draft` or `published` (the default). Every article response includes `status`, `publishedAt`, and `revision`. Drafts have no publication time and are visible only to their author; other readers receive `404`. Protected routes still require authentication first. Public lists, feeds, and tags contain published articles only. `GET /api/user/drafts` lists the authenticated author's drafts, newest first, with the same limit and offset pagination as the article list and without bodies.

`POST /api/articles/:slug/publish` lets the author publish a draft, setting its first publication time and incrementing its revision. Repeating it on a published article changes nothing. `PUT /api/articles/:slug` accepts an optional integer `article.revision`; a stale value returns `409` with the current article, while an omitted value updates normally. Every successful update increments the revision. Drafts cannot receive comments or favorites. Authentication, visibility, ownership, revision, then field validation determine which update error takes precedence.

## Article exports

`POST /api/user/exports` requires a token and no body. It returns `202` with a new pending export (`completedAt` and `articles` are null). `GET /api/user/exports/:id` requires a token and returns that user's export. Missing, malformed, and other users' IDs return the same `404` export error. A finished export has status `done`, a completion time, and every article the author had when the job ran, drafts included and oldest first. Each article contains `slug`, `title`, `description`, `body`, `tagList`, `status`, and `commentsCount`. The stored snapshot does not change when the source articles do.

Proletarian queues the export in PostgreSQL in the same transaction that creates its row. Integrant starts one polling worker after migrations and before HTTP serves requests. `bin/dev`, `bin/serve`, and the production image all run that worker in the web process; the production container needs only its existing three environment variables. Queued jobs survive restarts, and handler failures get three delayed retries. The worker uses a single query to read a consistent snapshot, then stores it as JSONB. A repeated job leaves a completed snapshot alone.

## Shared live editing

An author creates or rotates an article editing link with `POST /api/articles/:slug/share` and revokes it with `DELETE` on the same route. The returned URL-safe ID identifies the article across slug changes. The 32-byte random key is returned only at creation; PostgreSQL stores its SHA-256 hash. Rotation and revocation remove the active link and close its sockets. A missing or wrong key has the same `404` result on shared HTTP routes.

`GET /api/shares/:id/article` returns only `slug`, `title`, `body`, and `revision`. `PUT` requires exactly `title`, `body`, and an integer `revision` inside `article`; it can change no other fields. A successful save increments the article revision once, and a stale save returns `409` with the current shared article. The shared route locks the article row before checking the active link again and saving by article ID. This keeps link rotation, revocation, and concurrent saves in a consistent lock order. Standard author edits and publishing also notify an active editing room after commit.

`/api/shares/:id/live` uses Ring's Jetty WebSocket support on the same server. The first message must be `subscribe` with the key; an idle unauthenticated socket closes after five seconds. A room admits up to 100 authorized sockets, counting tabs separately. The in-memory room lock makes admission, its `ready` snapshot, presence changes, and update delivery ordered for this single backend instance. Each socket tracks its last sent revision, so a save racing with subscription appears in `ready` or a later `updated` message, never as an older revision. A full room sends `room_full` without admitting the socket; after a close, Retry can join and reads the latest article. The frozen client owns local draft preservation and conflict presentation.

## Spec choices

Slugs use a readable title prefix and a short random suffix so duplicate titles work. Article lists omit `body`; single articles include it. Counts precede pagination (default limit 20, offset 0). Tags exist while an article uses them, preserving each article's tag order; article and tag changes commit together. A supplied `tagList` must be an array of strings. Empty `bio` and `image` become null. JWTs identify the stable user ID and expire after 30 days. Passwords require at least 8 characters without composition rules. Errors follow the suite's field-specific `errors` object and status codes.

Publication is one way: there is no unpublish route and `status` on update is ignored. An update with no changed fields still increments the revision. Deleting a favorite from a draft is rejected like adding one; reading its empty comments list is allowed for its author. Existing articles gain published status, revision 1, and their creation time as `publishedAt` when the migration runs.

An export ID is a numeric database ID. An author with no articles receives an empty array once its job finishes. The snapshot is taken when the job reads the articles, which can be later than the request. Exports are private to their author and are removed if that user is deleted. The queue's archived jobs retain completion history. The unused Malli dependencies from the scaffold remain removed.
