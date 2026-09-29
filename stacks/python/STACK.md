# Python lane decision

Decision prepared 2026-09-30, before either implementation run: **Django +
Django Ninja**, PostgreSQL, Channels, Procrastinate, and Uvicorn. This is a
judgment about AgentMVC's relational application and its evolution goals;
no performance advantage has been measured yet.

| Candidate | Strong fit | Cost for this contract | Decision |
| --- | --- | --- | --- |
| Django + Ninja | Django associations, queries, migrations, constraints and password services; typed function endpoints with Pydantic | JSON projections are separate from persistence models; synchronous transactions need an explicit boundary in async socket code | Selected |
| Django REST Framework | Mature serializers, viewsets, permissions and the same Django persistence layer | Generic resource views fit ordinary CRUD, but lifecycle actions and the fixed envelopes still need explicit policy and serializer work | Credible alternate Python lane; no performance claim |
| FastAPI + SQLAlchemy + Alembic | Concise typed HTTP inputs, async I/O, flexible SQLAlchemy models and loading | Assemble migrations, persistence sessions, authentication policy, durable jobs and project conventions separately | Strong API toolkit; less integrated starting point for this Rails-like domain-density experiment |

[Django Ninja](https://django-ninja.dev/) integrates Django's ORM with typed
HTTP inputs and outputs. [DRF](https://www.django-rest-framework.org/) offers
a mature serializer/viewset model. [FastAPI's database guide](https://fastapi.tiangolo.com/tutorial/sql-databases/)
explicitly leaves the database library choice open. The relative glue costs
above are our design inference, not results from building all three variants.

[Procrastinate](https://procrastinate.readthedocs.io/en/stable/howto/django/configuration.html)
uses the existing PostgreSQL database and Django migrations. Its worker runs
as a second process in the same application container; no Redis or Celery
broker is needed. Domain writes and job enqueue must share a transaction,
or have a tested recovery path: an `on_commit` enqueue alone leaves a crash
window. The chosen Django connector can enlist in Django's current connection;
preflight must verify this against the pinned package.

[Channels](https://channels.readthedocs.io/en/stable/topics/channel_layers.html)
provides raw WebSocket consumers and ASGI routing. A channel layer is optional.
The scaffold does not install Redis or silently imply distributed room state.
The fixed one-instance contract permits process-local rooms; the agent must
record that limit. Extra Uvicorn workers require cross-process delivery and a
shared admission policy before their throughput can be reported as equivalent.
Django's [async documentation](https://docs.djangoproject.com/en/6.1/topics/async/)
still requires transactional ORM work to be a synchronous function; socket
code crosses once through `database_sync_to_async`, not once per row.

## Frozen dependency intent

| Component | Pin |
| --- | --- |
| CPython | 3.14.7 |
| Django | 6.1.1 |
| Django Ninja | 1.7.1 |
| Channels | 4.3.2 |
| Procrastinate | 3.10.0 |
| Psycopg | 3.3.6, binary and pool extras |
| Uvicorn | 0.54.0, standard extras |
| PyJWT | 2.15.1 |
| argon2-cffi | 25.1.0 |
| uv | 0.12.20 |

The direct dependencies are exact in `scaffold/pyproject.toml`; `uv.lock`
records the full transitive resolution and distribution hashes. The official
Python image is pinned by multi-platform digest in both Dockerfiles. Python's
[release list](https://www.python.org/downloads/) and Django's
[supported-version table](https://www.djangoproject.com/download/) were checked
before selecting currently supported releases. Package versions were also
confirmed directly through each project's PyPI metadata. The product-free container preflight passed health, generated migrations,
transactional job commit/rollback, worker-restart durability, raw UTF-8 sockets,
hot reload and a fresh production image. The proof is in
[`results/lanes/python/preflight.json`](../../results/lanes/python/preflight.json).
Coordinator isolation and fixture freeze are still required before launch.

## Scaffold boundary

The scaffold owns a health route, database settings, ASGI dispatch, a process
launcher, third-party queue tables and packaging. It supplies no product model,
endpoint, permission rule, article projection, input schema, export task, share
key, room, or token implementation. The agent owns those choices. The historical
eight steps and expert one-shot each start from this product-free base and must
remain separate paths. The shared one-shot prompt stays byte-identical.
