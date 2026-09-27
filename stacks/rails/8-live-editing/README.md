# Conduit API

Rails 8.1 API implementation of the pinned RealWorld contract in `realworld_spec/`.

## Run

Ruby 3.3.2 and Docker are required. Install gems locally, start PostgreSQL, prepare the database, and start Puma:

```sh
bundle config set --local path vendor/bundle
bundle install
docker compose -p rails-fresh-dev up -d
export DATABASE_URL=postgres://postgres:conduit@127.0.0.1:55401/conduit_development
bin/rails db:prepare
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES bin/rails server -b 127.0.0.1 -p 4101
```

Run `bin/check` for a fresh database, all 17 Hurl files, the shared live editing protocol and browser checks, Omakase RuboCop, and the production image checks. It stops its servers and databases on exit. The macOS fork setting above lets Solid Queue's worker run under Puma on this toolchain. The browser harness runs in the official Playwright Linux image through `bin/check-live`, leaving the shared client and tests untouched.

## Production image

Build the image and run it against a reachable PostgreSQL database:

```sh
docker build -t conduit:production .
docker run --rm -p 4101:4101 \
  -e DATABASE_URL='postgres://USER:PASSWORD@HOST:5432/conduit' \
  -e SECRET_KEY_BASE="$(openssl rand -hex 64)" \
  -e PORT=4101 conduit:production
```

The container prepares the schema on startup, then serves HTTP, WebSockets, and Solid Queue workers through Puma on port 4101. It needs only `DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT`. `bin/check-production` builds the image, starts fresh PostgreSQL, runs all 17 acceptance files, the shared live editing protocol and browser checks, all 13 security checks, and RuboCop. It stops its containers on exit.

## Shared live editing

An article's author creates or rotates its editing link with `POST /api/articles/:slug/share` and revokes it with `DELETE /api/articles/:slug/share`. Creation returns a URL safe `id` and random `key`; the server stores only the key's SHA-256 digest. A link identifies its article by `article_id`, so title changes and new slugs do not break it. The author can share drafts and published articles. Other users follow the existing article visibility and ownership rules.

A link holder sends `X-Share-Key` to `GET` or `PUT /api/shares/:id/article`. The response contains only `slug`, `title`, `body`, and `revision`. PUT requires exactly a string title, string body, and integer revision. `Article#revise!` locks the article, checks the revision, validates the fields, and increments the revision once. A stale save returns 409 with the current shared article. An unknown, missing, or revoked ID and key pair returns 404 before any article data or validation error is exposed. The link gives no access to other article or account routes.

`/api/shares/:id/live` accepts a JSON WebSocket `subscribe` message with the key before disclosing article or presence data. An admitted socket receives `ready`; committed article revisions produce `updated`. `ShareRoom` keeps connected sockets and presence in memory for this one backend instance. Its mutex makes the 100 socket limit atomic and orders snapshots and broadcasts. The 101st valid subscriber gets `room_full` and can retry after a slot opens. Closing a socket updates presence; revoking or rotating a link sends `revoked` and closes its sockets. Broadcasts are queued on EventMachine after database commit. The shared Lit client keeps a dirty draft and its base revision on remote updates, then offers an explicit conflict resolution action after a stale save.

## Article exports

`POST /api/user/exports` requires a token and returns 202 with a pending export. `GET /api/user/exports/:id` requires a token and returns that user's export, or 404 for another user's or an unknown ID. Both return an `export` object with `id`, `status`, `createdAt`, `completedAt`, and `articles`. Pending exports have null `completedAt` and `articles`.

An Active Job builds each export through Solid Queue outside the request. Export creation and job enqueueing share one database transaction. The job records all of the author's articles, including drafts, oldest first, with each article's slug, title, description, body, ordered tags, status, and comment count. Completed exports are stored JSON snapshots; later article changes do not alter them. A repeated job leaves a completed snapshot intact.

Solid Queue stores jobs in the same PostgreSQL database as the app. `db:prepare` creates its tables. Its Puma plugin starts workers with the development server and inside the single production container; no separate service or environment variable is needed. The production recurring task clears finished queue records hourly.

## Security

Rails `params.expect` checks the shape of request bodies and permits only the fields each endpoint accepts. User and comment string fields, article tags, revisions, and pagination values are checked before use; malformed input returns a client error. Article lists accept a limit of 0–1000 and an offset of 0–1,000,000. Passwords use `has_secure_password`, and authentication tokens are signed HS256 JWTs that expire after 30 days.

Rails' controller rate limiter allows 20 login attempts per five minutes for each IP address and email pair, returning 429 above that limit. It uses Rails' default file cache in the single production container; deployments with multiple app containers need a shared cache store for a shared limit. `bin/check-production` runs the security Hurl suite against the built image after the acceptance suite.

## Drafts and revisions

`POST /api/articles` accepts `status: "draft"` or `"published"`; omitted status means published. Every article response includes `status`, `publishedAt` (null for drafts), and `revision` (initially 1). A published article receives its publication time once.

Drafts appear only in their author's `GET /api/articles/:slug` response and `GET /api/user/drafts` list. The drafts list requires a token, orders newest first, supports `limit` and `offset`, and omits article bodies. Public lists, feeds, counts, and tags include published articles only. Other users see a draft as a 404. The author can read the draft's empty comments list, but cannot create comments or favorite the draft (422).

The author publishes with `POST /api/articles/:slug/publish`. Publishing a draft sets `publishedAt` and increments `revision`; publishing it again leaves both unchanged. Other users receive 403 for a published article and 404 for a draft. Authentication is required.

`PUT /api/articles/:slug` accepts an optional integer `revision`. A matching revision, or an omitted revision, applies the update and increments the revision. A stale revision returns 409 with the current article; an invalid revision returns 422. Authentication, visibility, and ownership are checked before the revision. Article status cannot be changed through this route.

## Libraries and code

Rails provides routing, controllers, validations, associations, migrations, jobs, and JSON views. `pg` connects Active Record to PostgreSQL; `puma` serves HTTP and WebSockets; `faye-websocket` handles WebSocket frames through Rack; `bootsnap` speeds boot; `bcrypt` backs `has_secure_password`; `jwt` signs authentication tokens; `jbuilder` renders the contract's JSON shapes; `rack-cors` handles cross-origin requests; `solid_queue` persists and runs jobs; `rubocop-rails-omakase` checks the default Rails style.

`Article` owns publication, locked revisions, tag replacement, the shared article shape, and article query scopes. `ArticleShare` owns link creation and key authentication. `ShareRoom` owns live admission, presence, and revision ordering; `ShareSocket` maps the JSON socket protocol to Faye. `Export` owns snapshot creation and completion; `BuildExportJob` calls it. `User` owns password hashing, tokens, and follows; the other models name the relationships and validations. `ApplicationController` handles token authentication and common errors. Controllers in `app/controllers/api` validate requests and select responses; Jbuilder views in `app/views/api` define the original JSON shapes. Migrations in `db/migrate` define the PostgreSQL schema.

## Performance

Article lists preload authors, tags, and favorites for each page. Signed-in lists load the viewer's followed users once, while single-article responses use a targeted follow lookup. Comment lists preload their authors. The JSON views use loaded associations for favorite status and counts, avoiding queries for every article.

The reproducible production benchmark is `BUILDX_CONFIG="$PWD/tmp/buildx" perf/bench.sh`; its measurements are in `perf/`.

## Spec choices

Article slugs use the title plus a random suffix so duplicate titles remain distinct; changing a title changes its slug. Tokens expire after 30 days. Tags keep their article order; `/api/tags` lists tags attached to a currently published article, so draft-only and orphaned tags are omitted. Email and username uniqueness are case sensitive. Article lists default to 20 entries and omit `body`. Empty `bio` and `image` values become `null`. Duplicate email or username returns 409, as the Hurl suite requires. For protected comment and favorite routes without a token, authentication takes precedence over article visibility, matching the original suite.

An export includes articles present when its job runs, not when it is requested; articles with the same creation time are ordered by ID. `status` derives from `completedAt`. A finished export remains unchanged if the job is repeated.
