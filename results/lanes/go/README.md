# Go lane preparation

The [final preflight](preflight.json) passed before any measured Go agent was
launched. It proves the prepared Huma/chi/Bun/River toolchain, not Conduit
product parity or application performance.

- PostgreSQL migrations apply twice safely.
- Bun and River share a transaction: rolled-back work disappears, committed
  work persists before the worker starts and then executes.
- Tests pass with Go's race detector, including raw WebSocket Unicode echo
  and maintained password/JWT libraries.
- Development and the fresh native production image both serve HTTP and raw
  sockets and execute a queued job.
- A development edit reloads in 0.751 seconds in the warmed preflight.
- Production finishes an in-flight database-backed HTTP request after SIGTERM
  before closing its pool and exiting.

The 16.1 MB production image here contains only the scaffold plus disposable
infrastructure probes. It is not an implementation-size or throughput result.
The probe workers, routes and tables are created in `.work/go-track-preflight/`
and are absent from the frozen agent scaffold.

Attempts 1 and 2 caught an error in the maintainer's disposable echo probe:
it closed TCP immediately after writing, producing a host-client protocol
error. A normal WebSocket closing handshake fixed it. Attempt 3 proved those
paths but was superseded when review corrected server shutdown ordering.
The final pass includes that fix and rejects scaffold edits during preflight.
These preparation attempts are separate from measured implementation effort.

Exact versions, image IDs, source hashes, logs and individual checks are in
the JSON record. Stack choice and alternatives are documented in
[the selection note](../../../stacks/go/SELECTION.md).
