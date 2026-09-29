**Status:** DONE

**Gate result:** `bin/check` exited 0: 15/15 Hurl files, Ruff lint and format, Django check and test passed. `bin/check-production` exited 0: 15/15 Hurl files passed. The production gate does not run lint.

**What you added:**

- [Dockerfile](/work/app/Dockerfile): copies only runtime code into the production image.
- [.dockerignore](/work/app/.dockerignore): excludes application tests from the image.
- [bin/check-production](/work/app/bin/check-production): invokes the supplied build, fresh PostgreSQL, Hurl, and cleanup gate.
- [README.md](/work/app/README.md): documents how to build and run the image.

**Production choices:** Uvicorn serves ASGI with one server process; one Procrastinate worker runs alongside it, with the existing psycopg pool capped at 10 connections per process. Uvicorn and Django log to container output. The launcher applies Django migrations before serving. The two-stage image uses pinned Python 3.14.7 slim Bookworm, locked production dependencies, and a nonroot user.

**Run counts:** `bin/check`: 2; `bin/check-production`: 3; narrower runs: 0; Docker build failures: 0. One built image failed at startup before the copy paths were fixed.

**Friction log:**

- Docker flattened a multi-source `COPY`, leaving Django unable to import `config`.
- The workspace has no Docker socket, so the production script uses the supplied coordinator gate.
- The original image copied the whole source tree; identifying runtime files took an image review.

**Agent-friendliness notes:** Django’s settings and migrations and the existing launcher made the runtime contract easy to trace. The coordinator gate exposed clear results, though its container lifecycle was not directly inspectable.