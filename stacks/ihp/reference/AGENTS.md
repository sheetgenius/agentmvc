# Hoogle

When you need to find functions, look up type signatures, discover data structures, or read documentation for any Haskell package used in this project, use Hoogle. It indexes all packages from `flake.nix`, so it's the primary way to explore available APIs and read Hackage-style documentation without leaving the dev environment.

```bash
hoogle search "Text -> ByteString"   # Search by type signature, function name, or data type
# Hoogle web UI at http://localhost:8002 - browse and read full Hackage docs for all project packages
```

# SQL

Use `sqlQueryTyped [typedSql| ... |]` / `sqlExecTyped [typedSql| ... |]` for application SQL. Raw `sqlQuery` is disallowed for normal app queries because it bypasses Postgres type inference and can hide decoder mismatches like `count(*)` returning `int8`. Only use raw/unsafe SQL for narrow cases where typed SQL cannot work, and leave a comment explaining why.

# Migrations

When you create a migration in `Application/Migration/`, set the revision prefix from the **current Unix timestamp** — run `date +%s` and use that exact number, then add a description: `Application/Migration/$(date +%s)-<description>.sql`. **Never hand-pick or round the number** (e.g. taking the latest revision and bumping it to a round value). IHP records only the numeric revision in `schema_migrations`, so if two migrations share a revision — which happens easily when parallel branches both round to the same "nice" number — IHP runs ONE and silently SKIPS the other. The skipped migration's columns/tables never get created while the merged code expects them, so the next deploy fails every affected query with `column … does not exist`. A raw `date +%s` is second-precise and monotonic, so parallel branches always get distinct, correctly-ordered revisions. If a duplicate still slips through, repair it with an idempotent migration at a fresh unique revision that re-applies whichever side was skipped — don't renumber a migration that may already have run somewhere.

# Tests

Run the full project test suite with:

```bash
nix flake check --impure
```

Use this command as the canonical verification step before handing off changes that affect application behavior, SQL, generated code, Nix configuration, dependencies, or CI. For fast local iteration, focused GHCi checks are fine, but `nix flake check --impure` is the full project check.

# Conduit rule map

- `Main.hs` registers IHP's HTTP controller and WebSocket route. `Application/Controller/Api.hs` owns API routing, validation, authorization, JWTs, and article transitions. Keep a rule beside the endpoint that enforces it.
- `Application/Schema.sql` declares tables and JSON projections for IHP's generated types and typed SQL inference. Every schema change also needs a timestamped migration in `Application/Migration/`; deployed databases run migrations, not `Schema.sql`.
- `Application/Live.hs` owns room admission, the 100 editor limit, presence, update broadcasts, and revocation. HTTP article writes invoke its broadcast after the database mutation.
- `Application/Job/Export.hs` owns durable export snapshots. `WorkerMain.hs` registers that job with IHP's PostgreSQL job runner; the production entry point starts the worker alongside IHP's web server.
- `Application/TypedSql.hs` retains `typedSql` compile time inference while using Hasql's unprepared execution path. This works around stale prepared statement cache entries in IHP's pooled connections; keep application queries on this wrapper.

For the fixed acceptance contract, start the disposable database and app with `harness/db.sh start 4104` and `harness/ihp.sh start`, then run `harness/check-all.sh 4104`. `harness/check-production.sh 4104` verifies the fresh single container deployment. Run `harness/ihp.sh run stylish-haskell -i ...` on changed Haskell modules and `harness/ihp.sh run hlint ...` before handing off.
