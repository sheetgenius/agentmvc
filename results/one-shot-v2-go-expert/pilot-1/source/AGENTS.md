# Conduit rule map

- `internal/conduit/users.go` owns registration, login, password changes, profile and follow behavior. `app.go` owns JWT validation, request field decoding, and Conduit errors.
- `internal/conduit/articles.go` owns draft visibility, article state and publication, revision checks, slug changes, list filters, and article response assembly. Both author and link edits call `saveArticle`.
- `internal/conduit/interactions.go` owns favorites and comments. These call `recordBySlug` for the same draft visibility rule and `published` for draft write restrictions.
- `internal/conduit/shares.go` owns key hashing and validation, link rotation and revocation, room admission, presence, and WebSocket delivery. Edits enter through `saveArticle`.
- `internal/conduit/exports.go` owns export snapshots and the River worker. `POST /api/user/exports` inserts the export and job in one transaction.
- `internal/platform/migrations/00003_product.sql` owns uniqueness, references, status constraints, and indexes. Add later schema changes as numbered Goose files.
- `internal/conduit/articles_test.go` exercises draft visibility, concurrent revision conflict, and idempotent publication against PostgreSQL.

`cmd/server/main.go` wires chi, Huma's typed public tags and health operations, the product router, River, and graceful shutdown. Chi handles protocol routes with custom auth and errors; Bun handles the tags query and database/transaction connection, while parameterized SQL handles atomic domain operations. `internal/platform/` owns connection, migration, and queue setup. The live room is process local, as the one instance contract permits.

Development: `harness/db.sh start 4110`, `harness/go.sh start`, then `harness/go.sh logs|test|lint|build`. Run `harness/check-all.sh 4110` against Air. Stop Air with `harness/go.sh stop` before `harness/check-production.sh 4110`. The production image embeds migrations and runs web and River with PostgreSQL using `DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT`.
