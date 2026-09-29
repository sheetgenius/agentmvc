# Go one-shot reference 1

This is an **unscored maintainer repair** of the [measured one-shot](../source/).
The measured source, effort and failures remain unchanged.

The [reference source](source/) has 12,846 owned backend tokens (+316):

- Explicit null revisions return 422 before a revision comparison.
- Shared edits reject extra outer-envelope fields after checking link authority.
- Login attempts reserve capacity atomically, with a 15-minute expiry; concurrent
  requests cannot all pass a separate read-then-increment check.

Focused tests cover revision types, shared envelopes, concurrent admission,
expiry and reset. Formatting, linting and fresh-database race tests passed.
[Independent development and production gates](verification.json), the
[common and favorites probes](reviewer-parity/results.json), and the
[shared-edit boundary probe](reviewer-parity/share-boundary.json) all pass.

The app still uses typed Huma operations only for health and tags, with manual
JSON decoding and mostly raw SQL for product routes. Its login limiter and
live rooms remain process-local. This repair does not establish what a fuller
Huma/Bun implementation could achieve.

[Source identity](source-snapshot.json) · [Size](size.json) ·
[Parent and condition](reference.json) · [Lane comparison](../../../lanes/README.md)

Repeated runtime measurements are separate from these correctness checks.
