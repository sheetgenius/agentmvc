**Status:** DONE.

**Gate result:** `bin/check` and `bin/check-production` both exited 0. Each passed 16/16 Hurl files and 13/13 security checks. The development gate also passed Ruff formatting, linting, Django’s system check, and 3 project tests; the production gate does not run those checks.

**Where the feature landed:**

- [conduit/models.py](/work/app/conduit/models.py): Added exports and their stored article snapshots.
- [conduit/tasks.py](/work/app/conduit/tasks.py): Added the export job.
- [conduit/exports.py](/work/app/conduit/exports.py): Added authenticated create and read routes.
- [conduit/migrations/0004_export.py](/work/app/conduit/migrations/0004_export.py): Created the export table.
- [conduit/api.py](/work/app/conduit/api.py): Registered the export routes.
- [config/settings.py](/work/app/config/settings.py): Enabled Procrastinate’s Django app.
- [bin/dev](/work/app/bin/dev): Starts the shared web and worker launcher with web reload.
- [bin/serve](/work/app/bin/serve): Starts both processes and handles shutdown signals.
- [bin/check-production](/work/app/bin/check-production): Requires all 16 acceptance files.
- [pyproject.toml](/work/app/pyproject.toml): Added Procrastinate.
- [uv.lock](/work/app/uv.lock): Locked its dependencies.
- [README.md](/work/app/README.md): Documented routes, rules, jobs, and contract choices.

**The job system:** Procrastinate uses the app’s PostgreSQL database. Its [Django integration](https://procrastinate.readthedocs.io/en/stable/howto/django/basic_usage.html) supplies migrations and task discovery. Both launchers migrate, then run Uvicorn and `manage.py procrastinate worker`; production runs both in one container.

**Passes:** Pass 1 clarified the launcher documentation. Pass 2 added signal forwarding and worker shutdown handling, and updated the README code map. Both checks passed after each pass; work stopped at the two-pass limit.

**Spec decisions:** Export IDs are integers. Status is derived from completion time. The job snapshots articles when it runs, orders equal creation times by ID, and leaves an empty article set as `[]`.

**Run counts:** `bin/check`: 3; `bin/check-production`: 3; narrower tool and validation runs: 6. Compile and image-build failures: 0.

**Friction log:**

- Procrastinate was named in the environment but absent from the dependency file, so it needed adding and locking.
- A migration command waited on an unavailable development database before reporting its result.
- The production gate still counted 15 acceptance files.
- Running two processes in one container required explicit signal and child-process handling.
- Host Git failed through `xcrun`; the container mount was not a Git repository, so file inspection was used.

**Agent-friendliness notes:** Django’s model and migration conventions, Ninja’s route modules, and Procrastinate’s task discovery kept the domain code compact. The main tracing cost was following startup and gate behavior across the shell launchers and check harness.