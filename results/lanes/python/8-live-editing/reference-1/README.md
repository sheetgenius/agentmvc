# Python eight-step reference 1

A small, **unscored maintainer repair** of the [measured step-8 source](../../../../../stacks/python/8-live-editing/). The original implementation, transcript, failures and measurements are preserved.

## Changes

- Reject malformed owner-update envelopes after authentication, visibility and ownership checks; retain revision-before-field validation.
- Filter favorited articles through a membership subquery so the global favorite count stays correct.
- Reuse a following annotation for comment authors, removing the signed-in per-comment lookup. A direct regression compares 1 and 20 comments.

## Verification

The exact [source](source/) passes independent [development and fresh production gates](verification.json), [21 common contract + 3 quality checks and 48 favorite-filter checks](reviewer-parity/results.json), and [3 shared-edit contract + 1 quality check](reviewer-parity/share-boundary.json). [Size](size.json) uses the original product-free scaffold baseline; tests/docs are [separate](supplementary-size.json).

[Source identity](source-snapshot.json) · [Parent and repair condition](reference.json). Runtime results will be recorded separately under `results/lanes/runtime/reference/`; no speed improvement is claimed before those measurements.
