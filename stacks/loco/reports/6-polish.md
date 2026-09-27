**Status:** DONE. The mastery pass stopped after three passes, and [README.md](../6-polish/README.md) now describes the finished code.

**Gate result:** Final `bin/check`: 15/15 Hurl acceptance files; formatting and Clippy passed; exit code 0. Final `bin/check-production`: 15/15 acceptance files and 13/13 security checks; exit code 0.

**Code map:**

- .dockerignore — excludes local artifacts from image builds.
- [Dockerfile](../6-polish/Dockerfile) — builds and starts the production image.
- ENVIRONMENT.md — records stack and sandbox details.
- [README.md](../6-polish/README.md) — run instructions and domain guide.
- [bin/check](../6-polish/bin/check) — development acceptance and lint gate.
- [bin/check-production](../6-polish/bin/check-production) — production acceptance and security gate.
- [compose.yaml](../6-polish/compose.yaml) — local PostgreSQL service.
- [conduit/.cargo/config.toml](../6-polish/conduit/.cargo/config.toml) — Loco Cargo alias.
- [conduit/.gitignore](../6-polish/conduit/.gitignore) — local Rust and config ignores.
- [conduit/Cargo.lock](../6-polish/conduit/Cargo.lock) — pinned dependencies.
- [conduit/Cargo.toml](../6-polish/conduit/Cargo.toml) — application dependencies and binary.
- [development.yaml](../6-polish/conduit/config/development.yaml) — development settings.
- [production.yaml](../6-polish/conduit/config/production.yaml) — production settings.
- [migration/Cargo.toml](../6-polish/conduit/migration/Cargo.toml) — migration crate dependencies.
- [migration/src/lib.rs](../6-polish/conduit/migration/src/lib.rs) — migration registry.
- [m20260927_000001_conduit.rs](../6-polish/conduit/migration/src/m20260927_000001_conduit.rs) — core tables and unique relationships.
- [m20260927_000002_drafts.rs](../6-polish/conduit/migration/src/m20260927_000002_drafts.rs) — draft and revision columns.
- [m20260927_000003_tags_index.rs](../6-polish/conduit/migration/src/m20260927_000003_tags_index.rs) — JSONB tags and GIN index.
- [app.rs](../6-polish/conduit/src/app.rs) — Loco hooks and routes.
- [bin/main.rs](../6-polish/conduit/src/bin/main.rs) — CLI entry point.
- [controllers/api.rs](../6-polish/conduit/src/controllers/api.rs) — viewer extraction and API errors.
- [controllers/articles.rs](../6-polish/conduit/src/controllers/articles.rs) — article routes, access, and validation.
- [controllers/comments.rs](../6-polish/conduit/src/controllers/comments.rs) — comment routes.
- [controllers/mod.rs](../6-polish/conduit/src/controllers/mod.rs) — controller modules.
- [controllers/profiles.rs](../6-polish/conduit/src/controllers/profiles.rs) — profile and follow routes.
- [controllers/users.rs](../6-polish/conduit/src/controllers/users.rs) — registration, login, and account routes.
- [src/lib.rs](../6-polish/conduit/src/lib.rs) — application modules.
- [_entities/articles.rs](../6-polish/conduit/src/models/_entities/articles.rs) — article row and relationships.
- [_entities/comments.rs](../6-polish/conduit/src/models/_entities/comments.rs) — comment row and relationships.
- [_entities/favorites.rs](../6-polish/conduit/src/models/_entities/favorites.rs) — favorite row and relationships.
- [_entities/follows.rs](../6-polish/conduit/src/models/_entities/follows.rs) — follow row and relationships.
- [_entities/mod.rs](../6-polish/conduit/src/models/_entities/mod.rs) — generated entity modules.
- [_entities/users.rs](../6-polish/conduit/src/models/_entities/users.rs) — user row and relationships.
- [models/articles.rs](../6-polish/conduit/src/models/articles.rs) — article queries, pagination, and publishing.
- [models/comments.rs](../6-polish/conduit/src/models/comments.rs) — comment persistence.
- [models/favorites.rs](../6-polish/conduit/src/models/favorites.rs) — favorite state and counts.
- [models/follows.rs](../6-polish/conduit/src/models/follows.rs) — follow state.
- [models/mod.rs](../6-polish/conduit/src/models/mod.rs) — model modules.
- [models/users.rs](../6-polish/conduit/src/models/users.rs) — user lookup, passwords, and tokens.
- [views/mod.rs](../6-polish/conduit/src/views/mod.rs) — view module.
- [views/realworld.rs](../6-polish/conduit/src/views/realworld.rs) — response shapes and related-data loading.

**What each pass changed:**

- Pass 1 moved author and favorited filtering into SeaORM queries, centralized page defaults, and removed an unused generated prelude.
- Pass 2 put counting and pagination in one model method and removed a redundant profile lookup.
- Pass 3 put publishing on the article model and shared the locked ownership lookup used by update and publish. Stopped at the three-pass limit.

**Run counts:** `bin/check` 3; `bin/check-production` 3; narrower Cargo format/check runs 3. Build failures hit: 0. One inspection command used the wrong relative path and failed before Cargo ran.

**Friction log:**

- The first file inventory included `conduit/target`, producing excessive output; subsequent reads targeted source paths.
- SeaORM’s generated entity layer adds files to read, though its row and relationship definitions are useful.
- Loco requires empty hook implementations and explicit database settings, limiting how much framework plumbing can be removed.
- RealWorld’s exact error shapes and draft access rules constrained otherwise simple type and handler changes.

**Agent-friendliness notes:** Resource routes, model methods, and the SeaORM query builder make the domain easy to locate. The two executable gates made small refactors safe to verify. Generated entity boilerplate and Loco’s required hooks remain the main reading overhead.