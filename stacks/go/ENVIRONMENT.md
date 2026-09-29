# Go environment

- Stack: Go 1.27.1, Huma v2.39.1 on chi v5.3.2, Bun v1.2.18 with pgx v5.11.0,
  Goose v3.28.0, River v0.47.0, coder/websocket v1.8.15, PostgreSQL 17.
- Port: 4110, listening on `0.0.0.0`.
- The prepared scaffold is a maintainer-authored, product-free API foundation.
  It has only `GET /health`, database and migration plumbing, a queue factory,
  and native release packaging. `go.mod`/`go.sum` pin dependencies.
- This is the prepared-scaffold condition. At step 1, implement the base
  product from the supplied contract: the scaffold does not already satisfy
  it. The original step prompt's reference to an existing implementation
  describes the historical study; this lane begins from the disclosed
  foundation. `.scaffold/` is its untouched, frozen size baseline.
- Use `harness/db.sh start 4110` for disposable PostgreSQL.
  `harness/go.sh start|logs|stop` manages the Air reload loop.
  `harness/go.sh run COMMAND...` runs bounded toolchain commands in the app.
  Use `harness/go.sh test`, `harness/go.sh lint`, and the supplied step checks.
- `go test ./...`, `go vet ./...`, and `gofmt` are available. Run
  `go test -race ./...` for concurrency changes. `go doc PACKAGE.SYMBOL`
  reads the exact installed API. Dependencies may be added with `go get`.
- Security tools are gosec 2.29.0 (`gosec -fmt=json ./...`) and govulncheck
  1.8.0 (`govulncheck -json ./...`). Report their findings without suppressing
  genuine application issues; distinguish dependencies from owned code.
- `bin/dev` is the foreground development entrypoint. Production builds an
  optimized static binary from `cmd/server` and embeds migrations. The only
  production settings are `DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT`.
- The orchestrator owns Docker and starts the disposable databases and gate
  containers. Do not start persistent services through `harness/go.sh run`.
- Frozen spec, client and harness inputs are read-only. Work freely in your
  application directory; parent and sibling workdirs are not accessible.
