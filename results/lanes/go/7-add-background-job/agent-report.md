**Status:** DONE.

**Gate result:** The final `bin/check` and `bin/check-production` runs both exited 0. Each passed 16/16 Hurl files and 13/13 security checks. Tests, gofmt, and go vet were clean.

**Where the feature landed:**

- [README.md](/work/app/README.md): documents routes, snapshots, job operation, and spec choices.
- [bin/check-production](/work/app/bin/check-production): requires all 16 acceptance files.
- [cmd/server/main.go](/work/app/cmd/server/main.go): starts and stops the worker with the server.
- [go.mod](/work/app/go.mod): adds River.
- [go.sum](/work/app/go.sum): records dependency checksums.
- [internal/conduit/http.go](/work/app/internal/conduit/http.go): registers authenticated export routes.
- [internal/conduit/models.go](/work/app/internal/conduit/models.go): defines export records and article snapshots.
- [internal/conduit/exports.go](/work/app/internal/conduit/exports.go): creates exports, enqueues jobs, and builds snapshots.
- [internal/platform/jobs.go](/work/app/internal/platform/jobs.go): migrates and starts River.
- [internal/platform/migrations/00005_exports.sql](/work/app/internal/platform/migrations/00005_exports.sql): stores export state and JSON snapshots.

**The job system:** River uses the app’s PostgreSQL database. Export creation and enqueue commit together. Four polling workers run in the development server and in the single production container; queued jobs survive restarts.

**Passes:** Pass 1 moved data shapes beside the other models and named the export states. Pass 2 separated job orchestration from snapshot assembly. Both ended with both checks green; I stopped at the two pass limit.

**Spec decisions:** The snapshot reflects data when the worker reads it. Articles sort by creation time, then ID; an empty export contains `[]`. Malformed IDs return 404. These choices are in the README.

**Run counts:** `bin/check`: 5 runs. `bin/check-production`: 4 runs. Narrower runs: one Hurl invocation and two Go test runs, including race detection. Compile and image build failures: 0.

**Friction log:**

- PostgreSQL rejected JSON bytes bound as `bytea`; binding JSON text fixed the job.
- The Hurl wrapper ran all files despite a file argument, making diagnosis slower.
- One production run hit a transient database connection refusal before readiness.
- One development run hit a database shutdown race in the harness.

**Agent-friendliness notes:** The project map and Bun models made the domain easy to locate. River’s transaction API required care when sharing Bun’s `database/sql` pool; its bundled migrations kept job schema setup small.