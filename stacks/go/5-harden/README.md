# Conduit API

Run `harness/db.sh start 4110`, then `harness/go.sh start` for the reload loop.
`bin/dev` runs the same loop in the prepared Go environment. `bin/check` starts
a fresh disposable PostgreSQL, runs all 15 Hurl files, tests, gofmt and
go vet, and stops its services.

## Production image

```sh
docker build -t conduit .
export DATABASE_URL='postgres://user:password@db-host:5432/conduit?sslmode=require'
export SECRET_KEY_BASE="$(openssl rand -hex 64)"
docker run --rm -p 4110:4110 -e DATABASE_URL -e SECRET_KEY_BASE -e PORT=4110 conduit
```

Use a PostgreSQL URL reachable from the container. The image contains the
server and migrations; startup prepares an empty database, then serves on
`0.0.0.0:$PORT`. `SECRET_KEY_BASE` must be 128 hex characters. Run
`bin/check-production` to build the image and verify all 15 acceptance files
and 13 security files against the production container and a fresh database.

## Security

API responses set `X-Content-Type-Options: nosniff`. Ten failed logins for an
account within 15 minutes trigger HTTP 429 until the window expires. Successful
login clears the count. The count lives in PostgreSQL and is updated under a
row lock, so concurrent requests and multiple server processes share the limit.

The dependency scan reports GO-2026-5932 for `golang.org/x/crypto`: its
unmaintained `openpgp` package has no fixed release. This app imports only
`x/crypto/bcrypt`, not `openpgp`, so the finding does not affect its password
hashing. Gosec reports no findings in the application packages.

## Drafts and revisions

`POST /api/articles` accepts `status: "draft"` or `"published"`; omitted status
means published. Responses include `status`, nullable `publishedAt`, and a
`revision` starting at 1. A draft's author can read, edit, and delete it at
`/api/articles/{slug}`. Other readers get 404 on the article and its related
routes. Article lists, feeds, counts, and tags exclude drafts for everyone.

`GET /api/user/drafts` lists the authenticated author's drafts, newest first,
with `limit` and `offset` and without article bodies.
`POST /api/articles/{slug}/publish` publishes the author's draft, records its
first publication time, and increments its revision. Publishing again leaves
it unchanged. Drafts cannot receive comments or favorites, including from
their author.

`PUT /api/articles/{slug}` accepts an optional integer `revision`. A matching
revision allows the edit and increments it. A stale revision returns 409 with
the current article; an invalid revision returns 422. Without a revision, the
update uses last write wins and still increments the stored revision. The
server checks authentication, visibility, ownership, revision, then fields.

## Libraries

- chi routes HTTP requests and handles path parameters.
- Bun maps Conduit's data shapes to PostgreSQL; pgx supplies its driver.
- Goose applies the embedded, numbered SQL schema.
- golang-jwt/jwt signs and verifies `Token` credentials.
- x/crypto/bcrypt hashes passwords.

## Performance

Article and comment lists load tags, authors, follows, and favorites for a
whole page instead of querying for each item. Indexes support recent article
lists, tag filtering, favorite counts, and article comments. Article creation
inserts tags without a preliminary delete and builds its response from the
saved article and tags.

The fixed 16-user production benchmark is in `perf/baseline/results.json` and
`perf/latest/results.json`. Article lists fell from 62–103 to 5–7 SQL
statements per request; article creation fell from 11 to 6. Run
`perf/bench.sh` to rebuild the image and measure the same workload.

## Code

`internal/conduit/http.go` owns routing, authentication, JSON and error shapes.
`users.go`, `articles.go`, and `comments.go` own endpoint rules. `models.go`
names records and responses. `internal/platform` opens PostgreSQL and applies
the schema; `cmd/server` owns process startup and shutdown.

## Spec choices

The acceptance suite takes precedence over the prose: duplicate user fields
return 409, list and feed articles omit `body`, empty `bio` and `image` become
null, and article tag order follows input order. Slugs are a normalized title
plus a random suffix so duplicate titles remain valid. Passwords need at least
eight characters; bearer tokens expire after 30 days. Unknown or invalid
credentials return 401. Article lists default to 20 items and offset zero.
On update, `status` is ignored: publishing has its own route and there is no
unpublishing. Publishing also refreshes `updatedAt`. Existing articles are
treated as published, with `publishedAt` set to their creation time when the
migration runs. An author can list a draft's comments; that list is empty
because drafts cannot receive comments.

This implementation replaces the product-free scaffold's unused Huma health
adapter, River queue, WebSocket pin and placeholder migration. Chi serves the
single health route alongside the product routes, and the database contains
only Conduit tables.
