**Status:** DONE.

**Gate result:** `bin/check` exited 0: 15/15 Hurl files, lint with 0 errors and 0 warnings, formatting clean, and tests passing. `bin/check-production` exited 0: image built and 15/15 Hurl files passed.

**What you added:**

- [bin/check-production](/work/app/bin/check-production): added the production check entry point using the supplied Docker harness.
- [Dockerfile](/work/app/Dockerfile): removed the fixed runtime CPU cap.
- [README.md](/work/app/README.md): added image build and run instructions.

**Production choices:** Jetty serves HTTP on `0.0.0.0:$PORT`; it uses its default thread pool and the existing 10-connection database pool, while the JVM follows the container’s CPU limit. SLF4J Simple writes logs to stderr. Migratus prepares the schema before HTTP starts. A pinned Temurin 25 JDK builds the jar; a pinned JRE image runs it as a nonroot user.

**Run counts:** `bin/check`: 2; `bin/check-production`: 2; narrower runs: 0; build failures: 0.

**Friction log:**

- Docker is available only through the supplied harness, which owns container cleanup.
- The existing Dockerfile needed a full production run to confirm its packaged migrations and runtime contract.
- Host `git` failed because the macOS developer tools path is invalid; file review used direct inspection.

**Agent-friendliness notes:** The AOT jar, Integrant startup, and packaged Migratus migrations made the runtime contract clear. The harness hides Docker lifecycle details, so its gate output is essential for verifying production behavior.