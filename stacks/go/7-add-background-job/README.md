# Conduit API

Go 1.27 API using chi, Bun, pgx, Goose and PostgreSQL.

Run `harness/db.sh start 4110`, then `harness/go.sh start` for the reload loop.
`bin/dev` runs the same loop in the prepared Go environment. `bin/check` starts
a fresh disposable PostgreSQL, runs 16 acceptance and 13 security Hurl files,
then runs tests, gofmt and go vet.

## Production image

```sh
docker build -t conduit .
export DATABASE_URL='postgres://user:password@db-host:5432/conduit?sslmode=require'
export SECRET_KEY_BASE="$(openssl rand -hex 64)"
docker run --rm -p 4110:4110 -e DATABASE_URL -e SECRET_KEY_BASE -e PORT=4110 conduit
```

Use a PostgreSQL URL reachable from the container. The image contains the
server and migrations; startup prepares an empty database, then serves on
`0.0.0.0:$PORT`. Set `SECRET_KEY_BASE` to a long random secret. Run
`bin/check-production` to build the image and verify all 16 acceptance files
and 13 security files against the production container and a fresh database.

## Security

API responses set `X-Content-Type-Options: nosniff`. Ten failed logins for an
account within 15 minutes trigger HTTP 429 until the window expires. Successful
login clears the count. The count lives in PostgreSQL and is updated under a
row lock, so concurrent requests and multiple server processes share the limit.

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
- River stores and runs PostgreSQL-backed background jobs.
- golang-jwt/jwt signs and verifies `Token` credentials.
- x/crypto/bcrypt hashes passwords.

## Performance

Article and comment lists load tags, authors, follows, and favorites for a
whole page instead of querying for each item. Indexes support recent article
lists, tag filtering, favorite counts, and article comments. Article creation
inserts all tags in one statement and builds its response from the saved
article and tags. Run `perf/bench.sh` to measure the production image.

## Code

`internal/conduit/http.go` owns routing, authentication, JSON parsing and error
responses. `users.go`, `articles.go`, `comments.go`, and `exports.go` own endpoint
and worker rules.
`models.go` names database records and public response shapes; `views.go`
assembles responses with batch queries. `internal/platform` opens PostgreSQL,
applies the embedded schema, and starts River; `cmd/server` owns startup and
shutdown.

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

## Article exports

`POST /api/user/exports` requires a token and returns 202 with a new pending
export. `GET /api/user/exports/{id}` requires the same user's token and returns
the export, or 404 for another user's export or an unknown or malformed ID.
Pending exports have null `completedAt` and `articles`. Completed exports have
a completion time and an array of article snapshots, including drafts. Each
snapshot contains the article's slug, title, description, body, tags, status,
and comment count. Later edits and deletions do not change it.

River stores jobs in the same PostgreSQL database. The request inserts the
export and its job in one transaction; a worker reads the author's articles and
stores the snapshot in a repeatable-read transaction. River's own migrations
run at startup. `bin/dev` runs the worker alongside the server, and the
production container runs both in the same process with the existing three
environment variables. Queued jobs survive a server restart.

The snapshot reflects the data when the job reads it, not when the request is
accepted. Articles are ordered by creation time, then ID, oldest first. An
author with no articles receives an empty array after completion.
