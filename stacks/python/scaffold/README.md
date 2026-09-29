# Django + Ninja scaffold

Product-free Django application: one health route, PostgreSQL settings,
Channels ASGI routing, Procrastinate's durable queue, and production packaging.
`uv sync --locked` installs the dependencies. With `DATABASE_URL`,
`SECRET_KEY_BASE`, and `PORT` set, `uv run bin/dev` reloads on edits;
`uv run bin/serve` migrates the database and starts the server plus worker.
The container's default is one Uvicorn worker. Add product behavior and tests.
