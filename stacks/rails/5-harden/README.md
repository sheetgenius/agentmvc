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
bin/rails server -b 127.0.0.1 -p 4101
```

Run `bin/check` for a fresh database, all 15 Hurl files, and Omakase RuboCop. It stops its server and database on exit.

## Production image

Build the image and run it against a reachable PostgreSQL database:

```sh
docker build -t conduit:production .
docker run --rm -p 4101:4101 \
  -e DATABASE_URL='postgres://USER:PASSWORD@HOST:5432/conduit' \
  -e SECRET_KEY_BASE="$(openssl rand -hex 64)" \
  -e PORT=4101 conduit:production
```

The container prepares the schema on startup, then serves the API on port 4101. `bin/check-production` builds the image, starts fresh PostgreSQL, runs all 15 acceptance files and all 13 security checks, and stops its containers on exit.

## Security

Rails `params.expect` checks the shape of request bodies and permits only the fields each endpoint accepts. User and comment string fields, article tags, revisions, and pagination values are checked before use; malformed input returns a client error. Article lists accept a limit of 0–1000 and an offset of 0–1,000,000. Passwords use `has_secure_password`, and authentication tokens are signed HS256 JWTs that expire after 30 days.

Rails' controller rate limiter allows 20 login attempts per five minutes for each IP address and email pair, returning 429 above that limit. It uses Rails' default file cache in the single production container; deployments with multiple app containers need a shared cache store for a shared limit. `bin/check-production` runs the security Hurl suite against the built image after the acceptance suite. The baseline OSV-Scanner lockfile scan found no vulnerable packages, and Brakeman reported no findings.

## Drafts and revisions

`POST /api/articles` accepts `status: "draft"` or `"published"`; omitted status means published. Every article response includes `status`, `publishedAt` (null for drafts), and `revision` (initially 1). A published article receives its publication time once.

Drafts appear only in their author's `GET /api/articles/:slug` response and `GET /api/user/drafts` list. The drafts list requires a token, orders newest first, supports `limit` and `offset`, and omits article bodies. Public lists, feeds, counts, and tags include published articles only. Other users see a draft as a 404. The author can read the draft's empty comments list, but cannot create comments or favorite the draft (422).

The author publishes with `POST /api/articles/:slug/publish`. Publishing a draft sets `publishedAt` and increments `revision`; publishing it again leaves both unchanged. Other users receive 403 for a published article and 404 for a draft. Authentication is required.

`PUT /api/articles/:slug` accepts an optional integer `revision`. A matching revision, or an omitted revision, applies the update and increments the revision. A stale revision returns 409 with the current article; an invalid revision returns 422. Authentication, visibility, and ownership are checked before the revision. Article status cannot be changed through this route.

## Libraries and code

Rails provides routing, controllers, validations, associations, migrations, and JSON views. `pg` connects Active Record to PostgreSQL; `puma` serves HTTP; `bootsnap` speeds boot; `bcrypt` backs `has_secure_password`; `jwt` signs authentication tokens; `jbuilder` renders the contract's JSON shapes; `rack-cors` handles cross-origin requests; `rubocop-rails-omakase` checks the default Rails style.

Models in `app/models` hold the domain relationships and validations. `ApplicationController` handles token authentication and common errors; controllers in `app/controllers/api` handle endpoint flow. Jbuilder views in `app/views/api` define responses. `db/migrate` defines the schema, and `bin/check` is the acceptance gate. The unused deployment, CI, and generated framework files were removed after generating the scaffold.

## Performance

Article lists preload authors, tags, and favorites for each page. Signed-in lists load the viewer's followed users once, while single-article responses use a targeted follow lookup. Comment lists preload their authors. The JSON views use loaded associations for favorite status and counts, avoiding queries for every article.

Under the fixed 16-user production benchmark (`BUILDX_CONFIG="$PWD/tmp/buildx" perf/bench.sh`), anonymous article lists went from 89.6 to 251.6 requests/s and 44.89 to 6 SQL statements/request; signed-in lists went from 62.4 to 203.0 requests/s and 66.96 to 8 statements/request. Feed requests went from 62.4 to 185.9 requests/s and 67 to 8 statements/request. Comment lists fell from 3.97 to 3 statements/request. The full baseline and latest measurements are in `perf/baseline/results.json` and `perf/latest/results.json`. Low-query endpoints were slower in the latest run, including the unchanged tags endpoint, so throughput comparisons across runs should be read with that variation in mind.

## Spec choices

Article slugs use the title plus a random suffix so duplicate titles remain distinct; changing a title changes its slug. Tokens expire after 30 days. Tags keep their article order; `/api/tags` lists tags attached to a currently published article, so draft-only and orphaned tags are omitted. Email and username uniqueness are case sensitive. Article lists default to 20 entries and omit `body`. Empty `bio` and `image` values become `null`. Duplicate email or username returns 409, as the Hurl suite requires. For protected comment and favorite routes without a token, authentication takes precedence over article visibility, matching the original suite.
