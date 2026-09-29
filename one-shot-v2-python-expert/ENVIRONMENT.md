# Python expert environment

Stack: CPython 3.14.7, Django 6.1.1, Django Ninja 1.7.1, Channels 4.3.2,
Procrastinate 3.10.0, Psycopg 3.3.6, Uvicorn 0.54.0 and PostgreSQL 17.
Serve port 4111 on `0.0.0.0`. The scaffold is product-free: a health route,
framework configuration, durable queue integration and production packaging.
`pyproject.toml` and `uv.lock` pin dependencies. You may add maintained packages.

Use `harness/db.sh start 4111` for a disposable PostgreSQL database.
`harness/python.sh start|logs|stop` controls the reloading Uvicorn server and
queue worker. `harness/python.sh run COMMAND...` runs bounded commands in the
prepared environment. Use `harness/python.sh run uv add PACKAGE` to add a
dependency and update the lock. Do not start a persistent server through `run`.
`harness/python.sh test` runs project tests. Use focused tests and requests in
the fast loop, then `harness/python.sh run ruff check .`,
`harness/python.sh run ruff format --check .`, and
`harness/python.sh run python manage.py check` before full gates.
Run `harness/check-all.sh 4111`, stop development, then run
`harness/check-production.sh 4111` against a fresh production database.

## Expert implementation notes

Use Django models, associations, QuerySets, constraints, generated migrations
and transactions as the application persistence path. Use Ninja routers,
typed schemas and the framework's error/auth hooks for HTTP; keep protocol
adaptation small and named. Use model methods or domain functions for
consequential transitions, and custom QuerySets for reusable data predicates.
Avoid hiding an important operation in an unrelated signal. An agent should
be able to find a rule's owner in `AGENTS.md` and change it once.

Use `select_related`, `prefetch_related`, `Exists`, and aggregates to load a
bounded page without a query per article. Apply visibility, filters, ordering,
count and pagination to a consistent query. Page before expanding many-to-many
associations. Inspect actual SQL and query counts; concise ORM expressions can
still perform unbounded work. Use parameterized SQL when it states a set
operation or atomic compare-and-swap more clearly.

Name visibility and edit authority in one place. Direct article reads allow an
author to see their own draft, while public lists and feeds exclude drafts.
Author and keyed updates should converge on one atomic content commit with
explicit input types. Check authentication, visibility/authority, revision and
editable fields in contract order. Do not leak field-validation details before
a denied capability check. Recheck the key under the lock or generation guard
that orders rotation and revocation. Database constraints enforce invariants
every writer must obey; model `save()` does not implicitly run `full_clean()`.

Use Pydantic strict fields and `extra="forbid"` where the contract needs them;
Python's `bool` is an `int` subclass and coercion is not always acceptable.
Distinguish omission from explicit JSON null using `model_fields_set` when
those mean different things. Avoid maintaining parallel hand-written field
extractors beside schemas. Where capability checks must precede validation,
put that ordering in the narrow endpoint boundary rather than weakening the
input model. Give the outgoing socket protocol one owner too.

Use Django `make_password`/`check_password` and the prepared Argon2 hasher;
use PyJWT with an explicitly allowed algorithm for the required `Token`
header. Password policy, token invalidation and share-key hashing each need one
owner. Do not rebuild password or signature algorithms. Rate-limit state must
apply to the intended identity and remain correct under concurrent requests.
Argon2 is memory-hard: bound concurrent password checks under the container
memory limit without weakening the configured hash or blocking socket I/O.

Channels `AsyncJsonWebsocketConsumer` and `URLRouter` speak the client's raw
WebSocket JSON protocol. A Redis channel layer is not available. A channel layer
is optional; one-process room state is permitted in this contract. Keep one
Uvicorn worker until delivery and room admission are shared across workers.
Document this limit. Admit atomically under the room cap, then send outside the
room lock; a slow client cannot hold up unrelated rooms. Cross from socket code
into a complete synchronous ORM transaction once with `database_sync_to_async`;
Django does not support async transaction blocks. Keep event-loop ownership
explicit when notifying sockets from synchronous HTTP handlers.

Procrastinate uses PostgreSQL, discovers app `tasks.py` modules and supplies its
schema through Django migrations. Its worker runs inside the application
container. Use an idempotent export task and make the export record and durable
job atomic, or provide and test recovery from the gap. The Django connector
supports the current Django connection; verify the chosen enqueue path with a
rollback test. A post-commit callback alone does not close the crash window.

The production image receives only `DATABASE_URL`, `SECRET_KEY_BASE` and `PORT`.
`bin/serve` applies migrations, then supervises Uvicorn and the queue worker.
Keep that order. The image installs locked runtime dependencies in a builder,
compiles Python bytecode, drops development dependencies and runs as a non-root
user. This is CPython with bytecode and native library wheels, not a claim of
native compilation of the application. Test the final image through the gate.

Write direct tests for visibility, password policy at both entrances, revision
conflicts, shared/author edit agreement, key rotation, atomic enqueue and room
admission. Replace the scaffold `AGENTS.md` with a concise rule map and commands.
Use explicit types at boundaries, enums for closed states, small named domain
operations and ordinary readable Python. Check unfamiliar APIs in the installed
source or official documentation before implementing against them.
