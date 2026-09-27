# Conduit API

Phoenix and Ecto implementation of the [RealWorld API](realworld_spec/docs/endpoints.md), including [article drafts and edit conflicts](realworld_spec/features/drafts/drafts.md). `bin/check` starts a fresh PostgreSQL, runs all 15 Hurl files, checks formatting and compiles with warnings treated as errors.

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

Point `DATABASE_URL` at a reachable PostgreSQL database. The container applies pending migrations before serving on the given port; keep `SECRET_KEY_BASE` stable across restarts. Put an HTTPS reverse proxy in front of the loopback port and prevent direct public access to the container. `bin/check-production` builds the image and verifies it against a fresh database, all 15 acceptance files and all 13 security checks.

## Libraries and code

- Phoenix routes requests and renders JSON; Bandit serves HTTP; Jason encodes JSON.
- Ecto SQL and Postgrex persist users, articles, comments, follows and favorites in PostgreSQL.
- Bcrypt hashes passwords; Joken signs and validates JWTs; CORSPlug handles browser preflights; Hammer limits login attempts.

`Conduit.Accounts` owns user lookup, credentials and follows; `Conduit.Content` owns article visibility, author permissions, revisions, comments, favorites and tags. Ecto schemas define data and validation. `ConduitWeb.Router` names the API, controllers handle request and response details, `Presenter` shapes JSON, and `Auth` and `FallbackController` handle shared authentication and errors.

## Security

Ecto changesets allowlist writable fields and validate their types. Controllers reject malformed JSON envelopes with 422 responses. Article pages accept at most 100 entries and ignore invalid or out-of-range pagination values. Phoenix adds secure response headers, including `X-Content-Type-Options: nosniff`. Hammer limits login attempts to 10 per email per minute, returning 429 and `Retry-After` when exceeded. Its ETS counters are local to one container; deployments with multiple replicas need a shared limiter or an ingress rate limit.

The production container serves HTTP on a private hop behind an HTTPS reverse proxy. The proxy must enforce HTTPS for public traffic and keep the container port private. Sobelow's `Config.HTTPS: HTTPS Not Enabled` finding applies to the container hop, so it is not an application HTTPS finding in that deployment. The baseline OSV scan reported no vulnerable lockfile packages.

## Performance

`perf/bench.sh` builds the production image and runs the fixed nine-scenario workload, writing measurements to `perf/latest/results.json`. Article pages fetch favorite counts and viewer relationships in page-wide queries. Single-article responses combine favorite count and viewer status in one aggregate, article fetches join their authors, and new articles and comments reuse the author already in hand. An index on `favorites.article_id` supports counts by article. Production logs warnings and errors without logging every request.

In the final benchmark, anonymous article lists ran at 3,480 requests/s versus 1,495 in the baseline, signed-in lists at 2,453 versus 790, and feeds at 2,407 versus 750. Their SQL statements per request fell from 23 to 4, 64 to 7, and 64 to 7 respectively. Single-article responses fell from 6 to 4 statements per request. Throughput varies across the short benchmark runs; the complete baseline and final results are in `perf/baseline/results.json` and `perf/latest/results.json`.

## Drafts and publishing

- `POST /api/articles` accepts `article.status` as `draft` or `published` (the default). Every article response includes `status`, `publishedAt` and `revision`.
- `GET /api/user/drafts` lists the signed-in author's drafts, newest first, with `limit` and `offset`. As with public article lists, entries omit `body`.
- `POST /api/articles/:slug/publish` publishes an author's draft, sets `publishedAt` and advances `revision`. Publishing an already published article leaves it unchanged.
- Drafts are visible by slug only to their author. Public lists, feeds, counts and tags include published articles only. Drafts cannot be commented on or favorited.
- `PUT /api/articles/:slug` accepts an optional integer `article.revision`. A matching value updates the article; a stale value returns `409` with the current article. Successful updates advance the revision even when the client omits it.

## Spec choices

Slugs are title based with a random suffix, so duplicate titles remain distinct. Tags are stored in article order; the global tag list is distinct and sorted. JWTs expire after two hours; malformed tokens return 401. Follow and favorite operations are idempotent, and self follow is allowed. Lists default to 20 articles at offset zero and omit article bodies. Deletes return 204; invalid comment IDs return 404. CORS allows any origin.

The draft feature leaves status changes out of article updates: publishing uses the publish route, and articles cannot be unpublished. An author's draft comment list is empty; adding a comment or favorite returns 422. `publishedAt` is set at creation for new published articles and at first publication for drafts; pre-feature articles inherit their creation time during migration. The Hurl suite settles behavior where the prose is ambiguous.
