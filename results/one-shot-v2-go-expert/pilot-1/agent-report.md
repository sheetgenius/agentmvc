Built the Conduit backend with the RealWorld API, drafts, revision conflicts, durable exports, editing links, and live editing.

The main rule owners are [users.go](/work/app/internal/conduit/users.go), [articles.go](/work/app/internal/conduit/articles.go), [interactions.go](/work/app/internal/conduit/interactions.go), [shares.go](/work/app/internal/conduit/shares.go), and [exports.go](/work/app/internal/conduit/exports.go). Database invariants live in [00003_product.sql](/work/app/internal/platform/migrations/00003_product.sql); the extension map and commands are in [AGENTS.md](/work/app/AGENTS.md).

The running app uses Go structs, contexts, mutexes, and channels; chi and a typed Huma tags route; Bun and pgx with parameterized SQL for atomic updates; Goose migrations; River jobs; coder/websocket; bcrypt; and HS256 JWTs. I fixed a Bun parameter mismatch and a filtered article count query during development.

**Checks:** formatter/linter, focused tests under `go test -race ./...`, the complete development gate, and the fresh database production gate all passed. Each complete gate passed 17 API files, 13 security files, the live protocol check, and four browser tests.

Measured against `.scaffold/`, owned executable backend source is **1,572 nonblank, noncomment lines / 13,433 `o200k_base` tokens**; the whole backend is **1,767 lines / 15,269 tokens**. Tests and project docs were measured separately.

Known limits: room presence and login rate limiting are process local. The current login failure counter resets on a successful login or process restart, with no timed expiry.