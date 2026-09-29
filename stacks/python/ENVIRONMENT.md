# Python environment

Use the maintainer-supplied product-free Django scaffold with CPython 3.14.7,
Django 6.1.1, Django Ninja 1.7.1, PostgreSQL 17, Channels and Procrastinate.
The scaffold's `/health` route, database configuration, ASGI server and generic
queue integration are setup assistance. It does not implement the product or
pass the acceptance checks. `.scaffold/` is the read-only measurement baseline.

Serve port 4111 on `0.0.0.0`. `harness/db.sh start 4111` prepares a disposable
database. `harness/python.sh start|logs|stop` controls the reloading server.
`harness/python.sh run COMMAND...` runs a bounded command in the prepared
container; use `uv add PACKAGE` there to install a maintained dependency.
`harness/python.sh test` runs Django's project tests. The coordinator runs
Docker-backed checks; no Docker socket is available inside the workspace.

Use the normal Django model, association, QuerySet, migration and transaction
APIs. Use Ninja's typed routes, schemas, authentication and error hooks. Django
password hashers, PyJWT, Channels raw WebSocket consumers and Procrastinate's
PostgreSQL queue are prepared tools. The app starts as one Uvicorn process;
adding workers requires reviewing any process-local state. Transactional ORM
work remains synchronous; async callers can cross through one complete
`database_sync_to_async` operation. You may add maintained packages.

During development use focused requests and tests, then `ruff check .`,
`ruff format --check .`, `python manage.py check` and `python manage.py test`
through `harness/python.sh run`. `bin/check` runs the current step's reviewer
checks. For packaging steps, `bin/check-production` prepares a fresh database,
builds the production image and runs that step's checks. The production image
receives `DATABASE_URL`, `SECRET_KEY_BASE` and `PORT` only. Its launcher migrates
then starts the server and worker. Keep the dependency lock current.
