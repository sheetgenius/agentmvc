# Go eight-step reference 1

A small, **unscored maintainer repair** of the [measured step-8 source](../../../../../stacks/go/8-live-editing/). The original implementation, transcript, failures and measurements are preserved.

## Changes

- Treat shared integer revisions zero/negative as stale (409), while missing/null/noninteger revisions remain invalid (422).
- Reject extra outer-envelope fields on shared edits. This is a supplemental quality requirement.
- Omit article bodies from list/feed/draft database projections; response contracts stay unchanged.

## Verification

The exact [source](source/) passes independent [development and fresh production gates](verification.json), [21 common contract + 3 quality checks and 48 favorite-filter checks](reviewer-parity/results.json), and [3 shared-edit contract + 1 quality check](reviewer-parity/share-boundary.json). [Size](size.json) uses the original product-free scaffold baseline; tests/docs are [separate](supplementary-size.json).

[Source identity](source-snapshot.json) · [Parent and repair condition](reference.json). Runtime results will be recorded separately under `results/lanes/runtime/reference/`; no speed improvement is claimed before those measurements.
