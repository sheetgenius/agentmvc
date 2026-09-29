# Conduit backend rule map

This is a Django 6 app with Ninja HTTP routes, Channels sockets, PostgreSQL, and a Procrastinate worker. The fixed contract lives in `realworld_spec/`; never edit it or `security/` and `harness/`.

- `conduit/models.py`: durable state, unique relationships, state and nonempty constraints; migrations are in `conduit/migrations/`.
- `conduit/domain.py`: password policy, JWT validation, draft visibility, edit authority, revisioned content commit, share-key validation, serialization, and bounded article pages. Change shared product rules here.
- `conduit/api.py`: Ninja routes, HTTP error shapes, request validation order, export enqueue, and profile/article/comment operations.
- `conduit/live.py`: socket protocol, admission and presence, room cap, ordered edit delivery, and revocation. HTTP calls it after commit.
- `conduit/tasks.py`: idempotent export snapshot job. The export row and queued job are created in one DB transaction in `api.py`.
- `conduit/middleware.py`: CORS for the shared client. `config/asgi.py` routes raw WebSockets.
- `tests/test_rules.py`: focused domain and transaction tests; frozen Hurl, browser, and security checks are the acceptance gates.

For article visibility or editing changes, update the domain operation once, then verify both author and share entrances. For socket behavior, keep admission atomic and send outside the room lock. The room registry is process local; production runs one Uvicorn worker.

Presence reads current membership under each client's send lock, including the newly ready client. The same lock orders ready, updates and revocation; revoked clients receive no later updates. `tests/test_live_ordering.py` forces delayed ready and overlapping leave schedules.

Local loop:

```sh
harness/db.sh start 4111
harness/python.sh start
harness/python.sh run python manage.py migrate --noinput
harness/python.sh test
harness/python.sh run ruff check .
harness/python.sh run ruff format --check .
harness/python.sh run python manage.py check
harness/check-all.sh 4111
harness/python.sh stop
harness/check-production.sh 4111
```

The container starts migrations, Uvicorn, and the Procrastinate worker through `bin/serve`; it needs `DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT`.
