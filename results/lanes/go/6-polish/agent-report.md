**Status:** DONE.

**Gate result:** Final `bin/check` and `bin/check-production` both exited 0. Each passed 15/15 acceptance files and 13/13 security checks. Tests, gofmt and go vet passed; production build passed.

**Code map:**

- [AGENTS.md](/work/app/AGENTS.md) — maintainer project map.
- [README.md](/work/app/README.md) — setup, behavior and code guide.
- [go.mod](/work/app/go.mod) — module and dependency versions.
- [go.sum](/work/app/go.sum) — dependency checksums.
- [Dockerfile](/work/app/Dockerfile) — production image.
- [.air.toml](/work/app/.air.toml) — development reload settings.
- [.dockerignore](/work/app/.dockerignore) — image context exclusions.
- [.gitignore](/work/app/.gitignore) — generated file exclusions.
- [bin/check](/work/app/bin/check) — development gate.
- [bin/check-production](/work/app/bin/check-production) — production gate.
- [bin/dev](/work/app/bin/dev) — reload loop.
- [bin/lint](/work/app/bin/lint) — formatting and vet checks.
- [bin/serve](/work/app/bin/serve) — packaged server entrypoint.
- [cmd/server/main.go](/work/app/cmd/server/main.go) — health route, startup and shutdown.
- [internal/platform/database.go](/work/app/internal/platform/database.go) — PostgreSQL connection.
- [internal/platform/migrations.go](/work/app/internal/platform/migrations.go) — embedded Goose runner.
- [00001_conduit.sql](/work/app/internal/platform/migrations/00001_conduit.sql) — core schema.
- [00002_drafts.sql](/work/app/internal/platform/migrations/00002_drafts.sql) — draft and revision columns.
- [00003_read_indexes.sql](/work/app/internal/platform/migrations/00003_read_indexes.sql) — read indexes.
- [00004_login_limits.sql](/work/app/internal/platform/migrations/00004_login_limits.sql) — login attempt columns.
- [internal/conduit/http.go](/work/app/internal/conduit/http.go) — routes, authentication, parsing and errors.
- [internal/conduit/users.go](/work/app/internal/conduit/users.go) — users, login and follows.
- [internal/conduit/articles.go](/work/app/internal/conduit/articles.go) — articles, tags, favorites and lists.
- [internal/conduit/comments.go](/work/app/internal/conduit/comments.go) — comment rules.
- [internal/conduit/models.go](/work/app/internal/conduit/models.go) — records and response shapes.
- [internal/conduit/views.go](/work/app/internal/conduit/views.go) — batched response assembly.
- [internal/conduit/users_test.go](/work/app/internal/conduit/users_test.go) — multibyte password check.

**What each pass changed:**

1. Separated records from response assembly, named article list scopes, and batched tag inserts.
2. Added a typed user response and isolated credential checking and profile lookup rules.
3. Moved user response assembly alongside the other views, updated the project map, then updated the README. Stopped at the three pass limit.

**Run counts:** `bin/check`: 3; `bin/check-production`: 3; narrower runs: 1 test and 2 gofmt; build failures: 0.

**Friction log:**

- `git status` was unavailable because the host’s active Xcode command line tools path is invalid.
- Response assembly was mixed into `models.go`, making records and projections slower to read.
- Login rate limiting uses a row lock; extracting it required preserving the transaction and rejection behavior.
- The README contained an exact signing secret requirement that the code does not enforce.

**Agent-friendliness notes:** Go’s explicit types, gofmt and the fixed Hurl gates made changes easy to verify. Bun kept database access compact; assembling the API’s nested response shapes still requires explicit code.