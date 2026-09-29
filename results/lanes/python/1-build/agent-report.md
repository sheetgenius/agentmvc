**Status:** DONE.

**Gate result:** The final `bin/check` exited **0**. All **13/13 Hurl files** passed; Ruff lint and formatter checks were clean; the Django check and local test passed.

**Libraries:**

- Django — models, authentication, migrations, and tests.
- Django Ninja — typed routes, schemas, and error hooks.
- PostgreSQL with psycopg — durable data and ordered tag arrays.
- PyJWT — signed `Token` authentication.
- django-cors-headers — browser CORS responses.
- Uvicorn — ASGI serving.
- Channels and Procrastinate — scaffolded socket and job wiring; the Conduit contract defines no product socket or job behavior.
- dj-database-url — database configuration; argon2-cffi — password hashing.
- Ruff — formatting and linting; pytest, pytest-django, and httpx — prepared test tools; Bandit and pip-audit — prepared security tools.

**Code map:**

- [conduit/models.py](/work/app/conduit/models.py) — users, follows, articles, favorites, tags, comments, and slug changes.
- [conduit/api.py](/work/app/conduit/api.py) — schemas, authentication, permissions, responses, and routes.
- [conduit/tests.py](/work/app/conduit/tests.py) — invalid-token test.
- [conduit/migrations/0001_initial.py](/work/app/conduit/migrations/0001_initial.py) — initial schema.
- [config/settings.py](/work/app/config/settings.py) — app, database, password, and CORS settings.
- [config/urls.py](/work/app/config/urls.py) — API mount.
- [bin/check](/work/app/bin/check) — full reviewer gate.
- [README.md](/work/app/README.md) — run guide, rule map, and contract choices.
- [pyproject.toml](/work/app/pyproject.toml) and [uv.lock](/work/app/uv.lock) — dependencies and lock.
- [conduit/__init__.py](/work/app/conduit/__init__.py) and [conduit/migrations/__init__.py](/work/app/conduit/migrations/__init__.py) — Python package markers.

**What you did toward the goal:** Built the API from the product-free scaffold. Pass 1 shared pagination logic and used Django identity validators. Pass 2 made email normalization and password updates consistent. Pass 3 moved product routes under one Ninja router and added the README rule map. Each pass ended with a green `bin/check`; I stopped at the requested three-pass limit.

**Spec decisions:** Duplicate titles receive distinct slugs, and title changes update the slug. Lists omit article bodies. Article tags retain input order; `/api/tags` lists currently used tags alphabetically. Empty bio and image values become `null`. Pagination counts the full filtered set. Email domains are normalized. CORS permits browser frontends.

**Run counts:** `bin/check`: **6** runs, including **4 green**. Narrower toolchain runs: **7**. Compile/build failures: **0**; one initial migration system-check failure.

**Friction log:**

- PostgreSQL `ArrayField` required `django.contrib.postgres` in installed apps.
- Django’s generated migration contained strings longer than Ruff’s line limit.
- Migration generation waited on the database before the disposable database had started.
- Local `git status` was unavailable because the host’s developer tools path was invalid.

**Agent-friendliness notes:** Django’s models and relationships and Ninja’s route decorators keep domain behavior easy to locate. The generated `AbstractUser` migration is much noisier than the application code.