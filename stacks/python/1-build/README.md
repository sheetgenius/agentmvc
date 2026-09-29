# Conduit API

Run `harness/db.sh start 4111`, then `harness/python.sh start`. The API listens on
port 4111. `bin/check` starts a fresh database and server, runs all 13 official
Hurl files plus Ruff and Django tests, and stops its services.

## Stack

- Django: users, models, relationships, migrations, password hashing, and tests.
- Django Ninja: typed HTTP routes, request schemas, and error hooks.
- PostgreSQL and psycopg: durable data and ordered tag arrays.
- PyJWT: signed `Token` authentication with a 30-day expiry.
- django-cors-headers: browser preflight and cross-origin headers.
- Uvicorn and Channels: ASGI serving and WebSocket wiring supplied by the scaffold.
- Procrastinate: PostgreSQL job wiring supplied by the scaffold; this API has no background jobs.
- dj-database-url: database configuration from `DATABASE_URL`.
- argon2-cffi: Argon2 password hashes.
- Ruff: formatting and linting. Pytest, pytest-django, and httpx support local tests;
  Bandit and pip-audit support the prepared security checks.

## Code map

`conduit/models.py` describes users, follows, articles, favorites, tags, and comments.
`conduit/api.py` holds the HTTP contract: inputs, permissions, response shapes, and
routes. `conduit/tests.py` covers invalid tokens. `config/settings.py` and
`config/urls.py` install the app and mount the API. `bin/check` runs the prepared
development gate. The initial migration records the schema.

The rule map is small: `Article.set_title` owns slug changes; `validate_identity`
and `password` own account validation; `viewer` and `owned` own access checks;
`article_page` owns list counts and pagination; the `*_data` functions own
response shapes. The route functions connect those rules to the HTTP contract.

## Contract choices

Duplicate titles get distinct readable slugs; changing a title changes its slug.
Article lists and feeds omit `body`, while single articles include it. Tags keep
their input order on an article; `/api/tags` lists tags currently used by articles
in alphabetical order. Empty profile bio and image values become `null`. Invalid
or missing tokens get a 401; duplicate usernames or email addresses get a 409.
Pagination counts the full filtered set and uses a default page size of 20.
Browser origins are allowed because this public API is intended for separate
frontends. Email domains are normalized on registration, login, and update.

This started from the product-free Django scaffold. The Conduit models, routes,
validation, authentication, migration, test, CORS support, and gate were added.
