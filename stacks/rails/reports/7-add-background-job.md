**Status:** DONE.

**Gate result:** Final `bin/check`: 16/16 Hurl files, formatter and linter clean (48 files, no RuboCop offenses), exit 0. Final `bin/check-production`: 16/16 Hurl files and 13/13 security checks, exit 0.

**Where the feature landed:**

- [Gemfile](../7-add-background-job/Gemfile) — added Solid Queue.
- [Gemfile.lock](../7-add-background-job/Gemfile.lock) — locked the job dependency.
- [README.md](../7-add-background-job/README.md) — documented routes, snapshots, job operation, and spec choices.
- [app/controllers/api/exports_controller.rb](../7-add-background-job/app/controllers/api/exports_controller.rb) — added authenticated create and show actions; creation and enqueueing share a transaction.
- [app/jobs/application_job.rb](../7-add-background-job/app/jobs/application_job.rb) — added the Rails job base class.
- [app/jobs/build_export_job.rb](../7-add-background-job/app/jobs/build_export_job.rb) — runs export creation outside the request.
- [app/models/export.rb](../7-add-background-job/app/models/export.rb) — builds and preserves article snapshots.
- [app/models/user.rb](../7-add-background-job/app/models/user.rb) — added the exports association.
- [app/views/api/exports/show.json.jbuilder](../7-add-background-job/app/views/api/exports/show.json.jbuilder) — renders the export response.
- [bin/check](../7-add-background-job/bin/check) — applies the macOS fork setting needed by its worker process.
- [config/application.rb](../7-add-background-job/config/application.rb) — enabled Active Job with Solid Queue.
- [config/puma.rb](../7-add-background-job/config/puma.rb) — starts workers alongside Puma.
- [config/queue.yml](../7-add-background-job/config/queue.yml) — configures Solid Queue workers.
- [config/recurring.yml](../7-add-background-job/config/recurring.yml) — clears finished queue records in production.
- [config/routes.rb](../7-add-background-job/config/routes.rb) — added the two export routes.
- [db/migrate/20260927000002_create_exports.rb](../7-add-background-job/db/migrate/20260927000002_create_exports.rb) — stores export ownership, snapshot, and completion time.
- [db/migrate/20260927000003_create_solid_queue_tables.rb](../7-add-background-job/db/migrate/20260927000003_create_solid_queue_tables.rb) — creates durable queue tables in the app database.
- [db/schema.rb](../7-add-background-job/db/schema.rb) — records the prepared PostgreSQL schema.

**The job system:** Rails Active Job uses [Solid Queue](https://guides.rubyonrails.org/active_job_basics.html) in the app’s PostgreSQL database. The Puma plugin runs workers with the development server and in the single production container; production still needs only `DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT`.

**Passes:** Pass 1 made completed snapshots safe from a repeated job and cleaned the generated migration and documentation. Pass 2 made export creation and job enqueueing atomic. Both checks ended green after each pass; the two-pass limit was reached.

**Spec decisions:** Articles are captured when the job runs, including drafts. Equal creation times sort by article ID. `status` derives from completion time. A completed snapshot stays unchanged on a repeated job.

**Run counts:** `bin/check` 4 runs; `bin/check-production` 3 runs; 2 narrower verification runs. Compile or build failures: 0.

**Friction log:**

- The Solid Queue generator initially failed because this app requires `DATABASE_URL` even for generator startup; rerunning with that variable worked.
- macOS Objective-C fork safety crashed the worker under Puma; a setting scoped to `bin/check` resolved it.
- Solid Queue generated a separate database schema; using the app’s PostgreSQL database required converting it into a migration.
- Standalone RuboCop tried to write outside the workspace; the gate’s workspace-local cache ran clean.

**Agent-friendliness notes:** Rails associations, Active Job, routes, and Jbuilder kept the product rules in recognizable places. The queue generator’s database assumption and the macOS worker crash required the most environment-specific investigation.