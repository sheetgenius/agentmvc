**Status:** DONE.

**Gate result:** `bin/check` exited 0 with 16/16 Hurl files, formatter clean, and Clippy clean. `bin/check-production` exited 0 with 16/16 Hurl files and 13/13 security checks.

**Where the feature landed:**

- [README.md](../7-add-background-job/README.md) — documented export routes, snapshot rules, job operation, and spec choices.
- [Dockerfile](../7-add-background-job/Dockerfile) — starts the server and worker in one production container.
- [bin/check](../7-add-background-job/bin/check) — starts the development server with its worker.
- [development.yaml](../7-add-background-job/conduit/config/development.yaml) — configures Loco’s PostgreSQL queue.
- [production.yaml](../7-add-background-job/conduit/config/production.yaml) — configures the same queue in production.
- [migration/src/lib.rs](../7-add-background-job/conduit/migration/src/lib.rs) — registers the export migration.
- [m20260927_000004_exports.rs](../7-add-background-job/conduit/migration/src/m20260927_000004_exports.rs) — creates durable export records.
- [app.rs](../7-add-background-job/conduit/src/app.rs) — registers the routes and worker.
- [controllers/api.rs](../7-add-background-job/conduit/src/controllers/api.rs) — maps queue errors to the API error shape.
- [controllers/mod.rs](../7-add-background-job/conduit/src/controllers/mod.rs) — exposes the export controller.
- [controllers/exports.rs](../7-add-background-job/conduit/src/controllers/exports.rs) — implements authenticated create and read routes.
- [lib.rs](../7-add-background-job/conduit/src/lib.rs) — exposes the worker module.
- [models/mod.rs](../7-add-background-job/conduit/src/models/mod.rs) — exposes the export model.
- [models/exports.rs](../7-add-background-job/conduit/src/models/exports.rs) — builds and stores the article snapshot.
- [models/_entities/exports.rs](../7-add-background-job/conduit/src/models/_entities/exports.rs) — generated SeaORM export entity.
- [models/_entities/mod.rs](../7-add-background-job/conduit/src/models/_entities/mod.rs) — registers that entity.
- [models/_entities/users.rs](../7-add-background-job/conduit/src/models/_entities/users.rs) — generated user-to-exports relationship.
- [views/realworld.rs](../7-add-background-job/conduit/src/views/realworld.rs) — renders pending and completed exports.
- [workers/mod.rs](../7-add-background-job/conduit/src/workers/mod.rs) — exposes the export worker.
- [workers/export_articles.rs](../7-add-background-job/conduit/src/workers/export_articles.rs) — processes queued export IDs.

**The job system:** Loco `BackgroundWorker` with its durable PostgreSQL `BackgroundQueue`, using the app’s `DATABASE_URL`. Development and the single production container both run `--server-and-worker`; a queue reaper recovers jobs left processing after a crash.

**Passes:** Pass one removed an unused generated prelude, clarified an entity column name, and updated the README; both gates stayed green. Pass two found no worthwhile further change, so I stopped.

**Spec decisions:** IDs are database integers treated as opaque identifiers. “Oldest first” uses article ID order. A completed export with no articles contains `[]`. Status comes from `completedAt`; the snapshot is captured in a repeatable-read transaction when the job runs.

**Run counts:** `bin/check`: 2; `bin/check-production`: 2; narrower export Hurl runs: 1. One `cargo check` compile failure was fixed; production build failures: 0.

**Friction log:**

- The model generator required a migration injection marker absent from this app.
- The worker generator required a test module absent from this app.
- Manual wiring needed an `ActiveModelBehavior` implementation and an explicit `BackgroundWorker` trait import.
- SeaORM’s model re-export made the article column path awkward until it was named locally.

**Agent-friendliness notes:** Loco’s bundled recipe and built-in PostgreSQL queue made the job architecture clear. The generators’ assumptions about existing file markers made this app harder to extend, while Rust’s compiler and the Hurl gates caught wiring and behavior errors quickly.