# Go scaffold provenance

Prepared by the AgentMVC maintainer for the Go lane on 2026-09-30. There is no
canonical Huma application generator: this is a small, maintainer-authored
composition scaffold. Its entire content is visible in `scaffold/` and copied
to `.scaffold/` for the application-size baseline.

It supplies a typed health route, HTTP lifecycle, PostgreSQL connection pool,
embedded Goose migrations, River migration and connection factories, an Air
reload configuration, and a native release Dockerfile. It supplies no Conduit
model, endpoint, policy, token, password, export worker or live-room behavior.
The River queue factory has no registered worker in the scaffold; product
workers belong to the measured implementation.

The direct dependency versions were resolved through the official Go module
proxy, then verified by compilation. `go.mod` and `go.sum` record exact module
versions and content hashes. Preflight records the built toolchain image ID.
The native release has default Go compiler optimization enabled, `CGO_ENABLED=0`,
trimmed paths, stripped debug symbols, embedded SQL, and a nonroot distroless
runtime. No PGO profile or application-specific performance change is supplied.

All framework integration checks use a disposable copy of this product-free
scaffold. Probe workers, socket handlers and migrations are not copied into
the agent fixture. See `tools/go_track_preflight.py` and its result record.
