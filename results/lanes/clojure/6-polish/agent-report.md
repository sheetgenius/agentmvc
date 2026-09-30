**Status:** DONE.

**Gate result:** The final `bin/check` and `bin/check-production` runs both exited 0. Each passed 15/15 Hurl acceptance files and 13/13 security checks. Lint reported 0 errors and 0 warnings; formatting and tests passed.

**Code map:**

- [README.md](/work/app/README.md) — setup, architecture, and product behavior.
- [.dockerignore](/work/app/.dockerignore) — production build exclusions.
- [.gitignore](/work/app/.gitignore) — local artifact exclusions.
- [Dockerfile](/work/app/Dockerfile) — production image.
- [deps.edn](/work/app/deps.edn) — runtime and tool dependencies.
- [build.clj](/work/app/build.clj) — uberjar and dependency inventory.
- [dev/dev.clj](/work/app/dev/dev.clj) — development reload loop.
- [articles.clj](/work/app/src/conduit/articles.clj) — articles, drafts, tags, comments, favorites, and feeds.
- [users.clj](/work/app/src/conduit/users.clj) — accounts, authentication, profiles, and follows.
- [http.clj](/work/app/src/conduit/http.clj) — routes and HTTP responses.
- [domain.clj](/work/app/src/conduit/domain.clj) — shared validation and authorization failures.
- [store.clj](/work/app/src/conduit/store.clj) — next.jdbc result mapping.
- [config.clj](/work/app/src/conduit/config.clj) — environment settings.
- [database.clj](/work/app/src/conduit/database.clj) — PostgreSQL pool.
- [migrations.clj](/work/app/src/conduit/migrations.clj) — migration startup.
- [system.clj](/work/app/src/conduit/system.clj) — Integrant lifecycle.
- [main.clj](/work/app/src/conduit/main.clj) — application entry point.
- [001-conduit.up.sql](/work/app/resources/migrations/001-conduit.up.sql) — core relational schema.
- [001-conduit.down.sql](/work/app/resources/migrations/001-conduit.down.sql) — core schema rollback.
- [002-drafts.up.sql](/work/app/resources/migrations/002-drafts.up.sql) — draft and revision columns.
- [002-drafts.down.sql](/work/app/resources/migrations/002-drafts.down.sql) — draft schema rollback.
- [http_test.clj](/work/app/test/conduit/http_test.clj) — route smoke test.
- [bin/check](/work/app/bin/check) — development gate.
- [bin/check-production](/work/app/bin/check-production) — container gate.
- [bin/dependency-scan](/work/app/bin/dependency-scan) — runtime advisory scan.
- [bin/dev](/work/app/bin/dev) — reloadable server.
- [bin/lint](/work/app/bin/lint) — lint and format checks.
- [bin/serve](/work/app/bin/serve) — steady server.

**What each pass changed:**

1. Kept database failures visible during authenticated lookup, made tag validation match JSON arrays, and simplified pagination parsing.
2. Put the profile response shape in one place for profile and article author responses.
3. Removed an empty clj-kondo configuration file so its default settings apply. The final read found no further change worth the churn. The README was then updated to describe the result.

**Run counts:** `bin/check`: 4 runs, including one formatter failure; `bin/check-production`: 3 runs, all green. Narrower runs: 1 Clojure parsing probe. Build failures hit: 0.

**Friction log:**

- `parse-long` rejects `nil`; the probe caught this, and pagination now guards absent values.
- cljfmt required one indentation adjustment after pass 2; the next check passed.
- `git status` was unavailable because the local Xcode command line tools path was invalid. It did not affect either gate.
- Exact authentication and validation error order limited route refactoring; the existing direct route definitions remained clearer.

**Agent-friendliness notes:** Small namespaces, data-shaped routes, and the Hurl gates made domain rules easy to locate and verify. The main reading cost is the boundary between Ring/Reitit middleware, result mapping, and SQL; keeping those adapters small helped.