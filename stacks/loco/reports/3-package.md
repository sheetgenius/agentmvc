**Status:** DONE.

**Gate result:** Final runs of `bin/check` and `bin/check-production` both exited 0. Each passed 15/15 Hurl files; `bin/check` also passed formatting and Clippy.

**What you added:**

- [Dockerfile](../3-package/Dockerfile): builds a release binary and packages a production runtime image.
- .dockerignore: excludes local artifacts from the build context.
- [bin/check-production](../3-package/bin/check-production): builds the image, tests it with fresh PostgreSQL, and cleans up.
- [production.yaml](../3-package/conduit/config/production.yaml): uses the three-variable runtime contract.
- [README.md](../3-package/README.md): documents building and running the image.

**Production choices:** Loco’s Axum server binds `0.0.0.0:$PORT`; Tokio supplies its default multi-thread runtime, with a 10-connection database pool. Loco writes info-level JSON logs to stdout. The container runs Loco migrations before starting the server. Rust 1.95 on Bookworm builds the binary; a smaller Debian Bookworm image runs it as a non-root user.

**Run counts:** `bin/check`: 2; `bin/check-production`: 3; narrower runs: 5; build failures hit: 1.

**Friction log:** Buildx initially tried to write outside the writable workspace; its config now uses a temporary workspace directory. The first release build had a cold Cargo cache and took 97 seconds. Production config originally required `HOST` and `JWT_SECRET`, which were outside the container contract.

**Agent-friendliness notes:** Loco’s CLI migration command and declarative environment config kept packaging out of application code. Its required `server.host` setting needed a value even though this API serves no absolute URLs.