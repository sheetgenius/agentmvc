# Go expert one-shot

This new lane uses the shared v2 expert prompt, full Conduit contract, fixed
Lit client and acceptance harness. The implementation is produced in a fresh
isolated measured session; the historical eight-step Go lane is a separate
sequence of sessions and artifacts.

The maintainer-prepared Huma/chi/Bun/River scaffold is product-free. Its exact
provenance, selected versions, and alternatives are in `stacks/go/`. Preflight
must prove the database, transactional queue, raw sockets, reload loop and
native production image before freeze and agent launch. Any frozen-input
change requires refreezing and a fresh workspace.

The measured agent receives a fresh Codex home, memory disabled, no subagents,
no interactive approvals, read-only inputs and no host Docker socket. The
reviewer reruns development and production gates independently, then the same
supplemental correctness and repeated runtime probes as the other lanes.
