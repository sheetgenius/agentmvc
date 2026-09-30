Built the Conduit backend and passed both complete gates.

[AGENTS.md](/work/app/AGENTS.md) maps the rule owners. The main ones are [rules.clj](/work/app/src/conduit/rules.clj) for visibility and revision policy, [articles.clj](/work/app/src/conduit/articles.clj) for article behavior and queries, [shares.clj](/work/app/src/conduit/shares.clj) for editing links and live rooms, and [exports.clj](/work/app/src/conduit/exports.clj) for durable snapshots. [002-conduit.up.sql](/work/app/resources/migrations/002-conduit.up.sql) enforces persistent constraints.

The running app uses immutable Clojure maps and transactions, Reitit/Malli/Muuntaja for HTTP, Ring/Jetty for WebSockets, Integrant for lifecycle, next.jdbc for PostgreSQL, Buddy for Argon2id passwords and JWTs, and Migratus plus Proletarian for schema and durable jobs.

- **Checks:** formatter and linter pass with no warnings; 3 tests and 12 assertions pass. Development and fresh-production gates each pass all 17 API/feature files, 13 security files, the live protocol check, and 4 browser tests.
- **Failure fixed:** the first development gate found that empty bio and image updates needed to become `null`. Normalization now lives in the user update rule; both complete gates passed afterward.
- **Measured source:** 726 owned nonblank, noncomment backend lines and 10,191 `o200k_base` tokens versus `.scaffold/`; whole backend: 920 lines and 12,679 tokens. Tests: 32 lines; agent documentation: 11 lines, measured separately.
- **Known limits:** presence and editing rooms are process local for the specified single-container deployment. List pages cap at 100 and request bodies at 1 MiB. The fixed tags and comments endpoints return whole collections, so their responses can grow with the database.