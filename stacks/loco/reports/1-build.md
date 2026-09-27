**Status:** DONE.

**Gate result:** The final `bin/check` exited 0. All 13 Hurl files passed; the formatter and Clippy were clean.

**Libraries:** Loco handles boot, routing, configuration, and CLI commands; SeaORM handles PostgreSQL models and queries; sea-orm-migration defines the schema; Axum supplies HTTP extractors and responses; Serde and serde_json handle JSON; Tokio and async-trait support async execution; Chrono handles timestamps; UUID and slug create article URLs and public user IDs. `migration` is the local schema crate.

**Code map:** Paths below are relative to this directory.

- [README.md](../1-build/README.md) — running, structure, dependencies, and spec choices.
- [bin/check](../1-build/bin/check) — fresh database and full acceptance gate.
- [compose.yaml](../1-build/compose.yaml) — PostgreSQL service.
- [conduit/Cargo.toml](../1-build/conduit/Cargo.toml) — app dependencies.
- [conduit/Cargo.lock](../1-build/conduit/Cargo.lock) — pinned dependency resolution.
- [conduit/.cargo/config.toml](../1-build/conduit/.cargo/config.toml) — `cargo loco` alias.
- [conduit/.gitignore](../1-build/conduit/.gitignore) — local build exclusions.
- [development.yaml](../1-build/conduit/config/development.yaml) — development settings.
- [production.yaml](../1-build/conduit/config/production.yaml) — production settings.
- [migration/Cargo.toml](../1-build/conduit/migration/Cargo.toml) — migration dependencies.
- [migration/src/lib.rs](../1-build/conduit/migration/src/lib.rs) — migration registration.
- [m20260927_000001_conduit.rs](../1-build/conduit/migration/src/m20260927_000001_conduit.rs) — domain tables and constraints.
- [src/app.rs](../1-build/conduit/src/app.rs) — Loco hooks and routes.
- [src/bin/main.rs](../1-build/conduit/src/bin/main.rs) — CLI entry point.
- [src/lib.rs](../1-build/conduit/src/lib.rs) — app modules.
- [controllers/api.rs](../1-build/conduit/src/controllers/api.rs) — Token authentication and RealWorld errors.
- [controllers/articles.rs](../1-build/conduit/src/controllers/articles.rs) — article, feed, favorite, and tag endpoints.
- [controllers/comments.rs](../1-build/conduit/src/controllers/comments.rs) — comment endpoints.
- [controllers/mod.rs](../1-build/conduit/src/controllers/mod.rs) — controller modules.
- [controllers/profiles.rs](../1-build/conduit/src/controllers/profiles.rs) — profile and follow endpoints.
- [controllers/users.rs](../1-build/conduit/src/controllers/users.rs) — registration, login, and user endpoints.
- [models/articles.rs](../1-build/conduit/src/models/articles.rs) — article creation, filters, tags, and slugs.
- [models/comments.rs](../1-build/conduit/src/models/comments.rs) — comment operations.
- [models/favorites.rs](../1-build/conduit/src/models/favorites.rs) — favorite state and counts.
- [models/follows.rs](../1-build/conduit/src/models/follows.rs) — follow state.
- [models/mod.rs](../1-build/conduit/src/models/mod.rs) — model modules.
- [models/users.rs](../1-build/conduit/src/models/users.rs) — user lookup, password hashing, and tokens.
- [views/mod.rs](../1-build/conduit/src/views/mod.rs) — view module.
- [views/realworld.rs](../1-build/conduit/src/views/realworld.rs) — API response shapes.
- [models/_entities/articles.rs](../1-build/conduit/src/models/_entities/articles.rs) — generated article entity.
- [models/_entities/comments.rs](../1-build/conduit/src/models/_entities/comments.rs) — generated comment entity.
- [models/_entities/favorites.rs](../1-build/conduit/src/models/_entities/favorites.rs) — generated favorite entity.
- [models/_entities/follows.rs](../1-build/conduit/src/models/_entities/follows.rs) — generated follow entity.
- [models/_entities/users.rs](../1-build/conduit/src/models/_entities/users.rs) — generated user entity.
- [models/_entities/mod.rs](../1-build/conduit/src/models/_entities/mod.rs) — generated entity modules.
- [models/_entities/prelude.rs](../1-build/conduit/src/models/_entities/prelude.rs) — generated entity aliases.

**What you did toward the goal:** Built the app from the snapshotted Loco starter. Pass 1 removed unused starter features, used domain names, and added database relationships and uniqueness constraints. Pass 2 moved most filtering and pagination into SeaORM and let foreign keys cascade article deletion. Pass 3 made follow and favorite writes idempotent through database conflict handling. Each pass ended with a green `bin/check`; I stopped at the requested three-pass limit.

**Spec decisions:** The suite’s `Token` header and error shapes take precedence over Loco defaults. Slugs use a title plus UUID; lists default to limit 20 and offset 0 and omit article bodies. Empty bio and image strings become null. Password updates require eight characters; registration requires a nonblank password. Tags remain article JSON lists, so tag filtering and tag discovery scan matching articles.

**Run counts:** Five `bin/check` runs, four fully green; zero narrower Hurl runs; six standalone Cargo checks and two standalone Clippy attempts. Five compile or build failures occurred before fixes.

**Friction log:** The generator placed the app in `conduit/`; Loco’s column type is `BigInteger`, not `BigInt`; SeaORM entity generation required a live schema; RealWorld’s Token authentication and error format differed from Loco’s defaults; obsolete starter tests initially broke `clippy --all-targets`.

**Agent-friendliness notes:** Loco’s layout and generated SeaORM entities make tables and relationships easy to locate. Rust’s explicit route wiring and trait imports add reading and compile work. The JSON tag representation keeps the domain small but leaves tag queries as the main scaling limitation.