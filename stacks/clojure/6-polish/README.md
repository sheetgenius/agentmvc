# Conduit API

Set `DATABASE_URL` (a PostgreSQL URL), `SECRET_KEY_BASE`, and optionally `PORT` (default 4112). Run `bin/dev` for reload on save, or `bin/serve` for a steady server. `bin/check` runs a fresh database, all 15 acceptance files, all 13 security files, lint, formatting, and tests. `bin/check-production` builds the image and runs both Hurl suites against its container.

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

- Clojure is the application language. Ring and Jetty serve HTTP; Reitit routes it, with its middleware and Muuntaja handling parameters and JSON.
- Integrant owns startup and shutdown. next.jdbc handles queries, HoneySQL builds partial updates, HikariCP pools PostgreSQL connections, the PostgreSQL driver connects, and Migratus runs the schema.
- Buddy hashers stores password hashes; Buddy sign issues and verifies JWTs. Pinned Bouncy Castle overrides Buddy's older transitive versions. SLF4J Simple logs.
- Caffeine bounds the five-minute failed-login counter to 10,000 email addresses.
- Development uses integrant.repl and tools.namespace. Cognitect test runner, clj-kondo, cljfmt, and tools.build are development and build tools.

## Security

JWT signatures and expiry are checked before account lookup; database errors still surface as server errors. User and article writes select client-owned fields, and SQL values are bound as parameters. Malformed JSON receives a JSON `400` response; API responses include `X-Content-Type-Options: nosniff`. Ten failed login attempts for an email address trigger `429` for five minutes. The counter is local to each app process and resets on restart.

`bin/dependency-scan` checks the resolved runtime Maven inventory with OSV-Scanner. No dedicated Clojure security static analyzer is supplied. `bin/check` runs clj-kondo and cljfmt with their default settings.

## Code

`http.clj` names the routes and wraps JSON errors, CORS, and authentication. `users.clj` owns accounts, login, profiles, follows, and the shared profile response shape used by article and comment authors. `articles.clj` owns articles, tags, comments, favorites, and feeds. `domain.clj` holds shared validation and authorization failures; `store.clj` sets the next.jdbc result shape. `system.clj`, `config.clj`, `database.clj`, `migrations.clj`, and `main.clj` start the service. `resources/migrations/` defines the relational schema.

## Performance

Article presentation fetches author, follow, and favorite details for a whole page in one query, then fetches its ordered tags in another. List pages use four SQL statements anonymously or five with authentication, including the count query. The queries read current PostgreSQL data on every request.

## Drafts and revisions

`POST /api/articles` accepts `article.status` as `draft` or `published` (the default). Every article response includes `status`, `publishedAt`, and `revision`. Drafts have no publication time and are visible only to their author; other readers receive `404`. Protected routes still require authentication first. Public lists, feeds, and tags contain published articles only. `GET /api/user/drafts` lists the authenticated author's drafts, newest first, with the same limit and offset pagination as the article list and without bodies.

`POST /api/articles/:slug/publish` lets the author publish a draft, setting its first publication time and incrementing its revision. Repeating it on a published article changes nothing. `PUT /api/articles/:slug` accepts an optional integer `article.revision`; a stale value returns `409` with the current article, while an omitted value updates normally. Every successful update increments the revision. Drafts cannot receive comments or favorites. Authentication, visibility, ownership, revision, then field validation determine which update error takes precedence.

## Spec choices

Slugs use a readable title prefix and a short random suffix so duplicate titles work. Article lists omit `body`; single articles include it. Counts precede pagination (default limit 20, offset 0). Tags exist while an article uses them, preserving each article's tag order; article and tag changes commit together. A supplied `tagList` must be an array of strings. Empty `bio` and `image` become null. JWTs identify the stable user ID and expire after 30 days. Passwords require at least 8 characters without composition rules. Errors follow the suite's field-specific `errors` object and status codes.

Publication is one way: there is no unpublish route and `status` on update is ignored. An update with no changed fields still increments the revision. Deleting a favorite from a draft is rejected like adding one; reading its empty comments list is allowed for its author. Existing articles gain published status, revision 1, and their creation time as `publishedAt` when the migration runs.

The scaffold's unused durable queue, queue tables, and Malli dependencies were removed so the files describe this product.
