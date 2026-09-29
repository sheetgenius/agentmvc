# Conduit API

Run `harness/db.sh start 4110`, then `harness/go.sh start` for the reload loop.
`bin/dev` runs the same loop in the prepared Go environment. Production starts
`cmd/server` with `DATABASE_URL`, `SECRET_KEY_BASE`, and optional `PORT` (4110 by
default). The server applies embedded migrations on startup. `bin/check` starts
a fresh disposable PostgreSQL, runs all 13 official Hurl files, tests, gofmt and
go vet, and stops its services.

## Libraries

- chi routes HTTP requests and handles path parameters.
- Bun maps Conduit's data shapes to PostgreSQL; pgx supplies its driver.
- Goose applies the embedded, numbered SQL schema.
- golang-jwt/jwt signs and verifies `Token` credentials.
- x/crypto/bcrypt hashes passwords.

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

This implementation replaces the product-free scaffold's unused Huma health
adapter, River queue, WebSocket pin and placeholder migration. Chi serves the
single health route alongside the product routes, and the database contains
only Conduit tables.
