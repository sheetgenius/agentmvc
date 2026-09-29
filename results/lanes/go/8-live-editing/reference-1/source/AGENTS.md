# Project map

- `internal/conduit/http.go`: routes, Token authentication, request parsing, error responses.
- `internal/conduit/users.go`: registration, login, profile updates and follows.
- `internal/conduit/articles.go`: articles, tags, favorites, feed and pagination.
- `internal/conduit/comments.go`: comment creation, listing and ownership checks.
- `internal/conduit/models.go`: PostgreSQL records and public response shapes.
- `internal/conduit/views.go`: assemble user, profile, article and comment responses in batches.
- `internal/platform/migrations/00001_conduit.sql`: schema and foreign keys; business rules live in Go.
- `internal/platform/database.go`, `migrations.go`: PostgreSQL pool and embedded Goose migrations.
- `cmd/server/main.go`: health route, startup and graceful shutdown.
- `bin/check`: fresh database, complete Hurl suite, tests and lint through the fixed harness.
