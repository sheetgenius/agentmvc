**Status:** DONE.

**Gate result:** All 13 Hurl files passed. Formatter and linter passed. Final `bin/check` exit code: 0.

**Libraries:** chi for routing; Bun and its PostgreSQL dialect for records and queries; pgx for the database driver; Goose for embedded migrations; golang-jwt/jwt for `Token` authentication; x/crypto/bcrypt for password hashes.

**Code map:**

- [cmd/server/main.go](/work/app/cmd/server/main.go): startup, health route, shutdown.
- [internal/conduit/http.go](/work/app/internal/conduit/http.go): routes, authentication, JSON parsing and errors.
- [internal/conduit/models.go](/work/app/internal/conduit/models.go): database records and response shapes.
- [internal/conduit/users.go](/work/app/internal/conduit/users.go): users, passwords, profiles and follows.
- [internal/conduit/articles.go](/work/app/internal/conduit/articles.go): articles, tags, favorites, feed and pagination.
- [internal/conduit/comments.go](/work/app/internal/conduit/comments.go): comments and ownership.
- [internal/conduit/users_test.go](/work/app/internal/conduit/users_test.go): long Unicode password policy.
- [internal/platform/database.go](/work/app/internal/platform/database.go): PostgreSQL pool.
- [internal/platform/migrations.go](/work/app/internal/platform/migrations.go): embedded Goose migrations.
- [internal/platform/migrations/00001_conduit.sql](/work/app/internal/platform/migrations/00001_conduit.sql): Conduit tables and relationships.
- [bin/check](/work/app/bin/check): fresh database and full acceptance gate through the supplied harness.
- [bin/dev](/work/app/bin/dev), [bin/lint](/work/app/bin/lint), [bin/serve](/work/app/bin/serve): development, lint and container entrypoints.
- [Dockerfile](/work/app/Dockerfile), [.air.toml](/work/app/.air.toml): release build and reload configuration.
- [go.mod](/work/app/go.mod), [go.sum](/work/app/go.sum): dependencies and checksums.
- [README.md](/work/app/README.md), [AGENTS.md](/work/app/AGENTS.md): run instructions, spec choices and rule map.

**What you did toward the goal:** Built the API from the prepared scaffold. Pass 1 removed unused Huma, River and WebSocket plumbing and the placeholder migration. Pass 2 centralized password policy, simplified nullable input handling and removed route wrappers. Pass 3 found no worthwhile further change; its full gate stayed green, so I stopped.

**Spec decisions:** Duplicate user fields return 409; article lists omit `body`; empty bio and image values become null; tag order follows input order. Slugs include a random suffix to allow duplicate titles. Passwords require eight characters, tokens expire after 30 days, and article lists default to limit 20 and offset zero.

**Run counts:** `bin/check`: 6 runs, the last 4 green. Narrower runs: 1 Go test run, 3 formatter runs and 1 dependency tidy. Compile or build failures: 0.

**Friction log:** Bun rejected inserts without a model; PostgreSQL’s microsecond timestamps initially differed from Go’s nanosecond response; several required statuses and response details appeared only in Hurl; the fixed Docker harness required `bin/check` to delegate service management.

**Agent-friendliness notes:** chi’s route table and Go’s explicit types make rule owners easy to find. Bun keeps records readable. The RealWorld error shape required a small shared HTTP layer, while the unused scaffold services obscured the domain until removed.