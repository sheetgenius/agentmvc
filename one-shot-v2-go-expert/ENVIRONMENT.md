# Go expert environment

Go 1.27.1, Huma v2.39.1 on chi v5.3.2, Bun v1.2.18 with pgx v5.11.0,
Goose v3.28.0, River v0.47.0, coder/websocket v1.8.15, PostgreSQL 17.
Serve port 4110 on `0.0.0.0`. The scaffold has only a health route and generic
infrastructure. `go.mod` and `go.sum` pin prepared dependencies; add maintained
libraries where useful.

Use `harness/db.sh start 4110`, then `harness/go.sh start|logs|stop` for the
Air development reload loop. `harness/go.sh run COMMAND...` executes bounded
commands, `harness/go.sh test` runs project tests, `harness/go.sh lint` runs
gofmt and vet, and `harness/go.sh build` checks production packaging. Inspect
unfamiliar APIs with `harness/go.sh run go doc PACKAGE.SYMBOL` or official docs.
Do not run persistent services through the bounded `run` action. Use the
running development server for small checks. Run `harness/check-all.sh 4110`,
then stop development and run `harness/check-production.sh 4110` at completion.

## Framework idioms

Use Huma operations with typed input/output structs for JSON routes and chi
for standard HTTP integration. Huma's default errors differ from Conduit's
envelope: its `StatusError` and `NewError` extension points centralize mapping.
Place caller authentication and resource authority before body validation
where the contract requires that order. Presence, nullability and zero values
are distinct concerns: pointers alone do not express all three. Read Huma's
schema rules and test the wire boundary rather than assuming encoding/json's
zero values are sufficient. Keep exact request types separate from persisted
records and public output types when their permissions differ.

Bun models declare associations with relation tags. Compose scopes as query
functions and load relations for a whole page. Keep filtering, ordering,
counting and pagination in PostgreSQL. Use Bun query builders for ordinary
CRUD and parameterized SQL for clear set operations and atomic updates.
Named types, small structs and narrow interfaces should make product states,
callers and operation inputs explicit. Use generics where they remove repeated
plumbing; keep domain decisions visible at the call site. Do not build a
generic repository framework around every query or turn typed inputs back into
unstructured maps.

Goose applies embedded SQL migrations before serving. Database constraints
own invariants that every writer must obey. `platform.Queue` shares Bun's
`*sql.DB` with River and uses a small pgx pool for LISTEN/NOTIFY. Register typed
River workers and start/stop the client with the HTTP server. `InsertTx` accepts
Bun's embedded `tx.Tx`, so application writes and queued work can commit
atomically. Use idempotent workers and focused tests of rollback and restart.

The client uses raw WebSocket JSON. Mount coder/websocket through the same chi
router; keep protocol events typed and room state owned explicitly. Go's
mutexes, channels and contexts support bounded admission, cancellation and
per-client send queues. Send outside room locks, bound queues, and release
membership on every close path. Process-local membership is acceptable under
the single-instance contract; document that limit.

Use x/crypto's maintained password hashing and golang-jwt with an explicitly
allowed algorithm. Keep each policy and state transition in one named owner,
with direct tests and a concise `AGENTS.md` map. `go test -race ./...` belongs
in the concurrency feedback loop. Prefer readable error returns, early exits,
ordinary control flow, and useful names over compressed expressions.

The production Dockerfile compiles a normal optimized static binary and uses
a nonroot minimal runtime. Its only environment settings are `DATABASE_URL`,
`SECRET_KEY_BASE`, and `PORT`; it must migrate, start the queue and serve HTTP
and WebSocket without another application service. SQL migrations are embedded
so the production image does not depend on the source checkout.
