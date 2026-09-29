# Project map

- `cmd/server/main.go`: HTTP composition, health route, graceful shutdown.
- `internal/platform/database.go`: Bun and pgx connection pool.
- `internal/platform/migrations.go`: Goose with embedded SQL and pinned River schema.
- `internal/platform/migrations/`: application SQL migrations; add monotonically numbered files.
- `internal/platform/queue.go`: River connection factory; register application workers and start/stop it with the server.
- `bin/dev`: Air reload loop. `bin/lint`: gofmt and go vet. `go test ./...`: project tests.
- `Dockerfile`: optimized, static release binary, embedded migrations, nonroot runtime.
- This scaffold has no product models, authentication, queue workers, or socket protocol.
- Replace this document with a map of product rule owners and focused tests as the application grows.
