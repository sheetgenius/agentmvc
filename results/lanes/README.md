# Go and Python

Two new paths through the same Conduit product: build it in eight successive sessions, then build it again in one fresh expert session. The goal is readable, domain-rich code that uses each stack well, with correctness and production performance measured alongside size.

**Progress: 18/18 coding sessions independently verified.** Final snapshots, checks and effort records are linked below.

## Start with the code

| Lane | Latest verified sequential source | Owned backend | Expert one-shot |
| --- | --- | ---: | --- |
| Go | [8-live-editing](../../stacks/go/8-live-editing) | 14,203 tokens · 1,773 lines | [12,530](../one-shot-v2-go-expert/pilot-1/source) tokens · [pass](../one-shot-v2-go-expert/pilot-1/verification.json) |
| Python | [8-live-editing](../../stacks/python/8-live-editing) | 8,308 tokens · 1,118 lines | [8,718](../one-shot-v2-python-expert/pilot-1/source) tokens · [pass](../one-shot-v2-python-expert/pilot-1/verification.json) |

## Reviewed references

Each row selects the latest independently verified reference for that application. These repairs preserve earlier attempts and measured originals; their editing effort is not pooled with coding effort. Reviewer checks remain separately visible.

| Reference source | Owned backend | Reviewer checks |
| --- | ---: | --- |
| [Go · eight-step reference 1](go/8-live-editing/reference-1/source) | 14,249 tokens | [21/21 contract · 3/3 quality · favorites 48/48](go/8-live-editing/reference-1/reviewer-parity/results.json) · [shared 3/3 + 1/1](go/8-live-editing/reference-1/reviewer-parity/share-boundary.json) |
| [Go · one-shot reference 1](../one-shot-v2-go-expert/pilot-1/reference-1/source) | 12,846 tokens | [21/21 contract · 3/3 quality · favorites 48/48](../one-shot-v2-go-expert/pilot-1/reference-1/reviewer-parity/results.json) · [shared 3/3 + 1/1](../one-shot-v2-go-expert/pilot-1/reference-1/reviewer-parity/share-boundary.json) |
| [Python · eight-step reference 1](python/8-live-editing/reference-1/source) | 8,429 tokens | [21/21 contract · 3/3 quality · favorites 48/48](python/8-live-editing/reference-1/reviewer-parity/results.json) · [shared 3/3 + 1/1](python/8-live-editing/reference-1/reviewer-parity/share-boundary.json) |
| [Python · one-shot reference 2](../one-shot-v2-python-expert/pilot-1/reference-2/source) | 9,058 tokens | [21/21 contract · 3/3 quality · favorites 48/48](../one-shot-v2-python-expert/pilot-1/reference-2/reviewer-parity/results.json) · [shared 3/3 + 1/1](../one-shot-v2-python-expert/pilot-1/reference-2/reviewer-parity/share-boundary.json) |

### Repeated reference runtime

Two rounds; 16 concurrent users; 3-second warmup and 15-second samples; app and database each limited to 2 CPUs and 1 GiB. The HTTP fixture has 50 users and 500 articles. Ranges show both rounds. Source and image hashes must match the runtime manifest before metrics are shown; all nine HTTP workloads and 10/100/500-subscriber socket results are linked.

| Application | List req/s | Article req/s | SQL / list | Image MB | Cold start seconds | Runtime checks |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| [Go · eight-step reference 1](runtime/reference/go-8-live-editing-reference-1) | 2,798–3,012 | 4,019–4,075 | 5.00 | 16.1 | 0.29–0.30 | pass |
| [Python · eight-step reference 1](runtime/reference/python-8-live-editing-reference-1) | 525 | 511–513 | 2.00 | 260.6 | 1.50–1.59 | pass |
| [Go · one-shot reference 1](runtime/reference/go-one-shot-reference-1) | 1,907–1,984 | 5,298–5,454 | 2.00 | 16.6 | 0.31–0.34 | pass |
| [Python · one-shot reference 2](runtime/reference/python-one-shot-reference-2) | 374–376 | 372–374 | 3.00 | 373.8 | 1.59–1.66 | pass |

[Runtime manifest and all workloads](runtime/reference/summary.json). Each runtime label names the exact reference version measured, which may precede a newer verified reference.

**Python:** Django + Django Ninja, with Django associations, migrations and password services; Channels for raw WebSockets; Procrastinate for PostgreSQL jobs. [Why this stack](../../stacks/python/STACK.md).

**Go:** the sequential implementation uses **chi + Bun** and removed Huma in step 1. The expert one-shot uses Huma for only `/api/tags` and `/health`; most product handlers use chi directly, alongside Bun, Goose and River. These are the observed implementations of the supplied Huma/chi guidance. [Why this toolkit](../../stacks/go/SELECTION.md).

The one-shots start from product-free scaffolds and use the [same expert-v2 prompt](../../one-shot-v2-expert/PROMPT.md) as the recent Rails, Phoenix and TypeScript builds. The sequential lanes use the original eight prompt files. Stack guidance and preparation are disclosed separately; these are distinct conditions, not pooled trials.

## The eight steps

Every source link is an immutable checkpoint. “Pass” means the coordinator reran the applicable frozen checks; production verification begins at step 3.

| Step | Go | Python |
| --- | --- | --- |
| [1 · Base API](../../steps/1-build.md) | [7,236](../../stacks/go/1-build) tokens · [pass](go/1-build/verification.json) | [4,003](../../stacks/python/1-build) tokens · [pass](python/1-build/verification.json) |
| [2 · Drafts](../../steps/2-add-drafts.md) | [8,214](../../stacks/go/2-add-drafts) tokens · [pass](go/2-add-drafts/verification.json) | [4,767](../../stacks/python/2-add-drafts) tokens · [pass](python/2-add-drafts/verification.json) |
| [3 · Production](../../steps/3-package.md) | [8,225](../../stacks/go/3-package) tokens · [pass](go/3-package/verification.json) | [4,767](../../stacks/python/3-package) tokens · [pass](python/3-package/verification.json) |
| [4 · Performance](../../steps/4-tune.md) | [9,086](../../stacks/go/4-tune) tokens · [pass](go/4-tune/verification.json) | [4,990](../../stacks/python/4-tune) tokens · [pass](python/4-tune/verification.json) |
| [5 · Security](../../steps/5-harden.md) | [9,537](../../stacks/go/5-harden) tokens · [pass](go/5-harden/verification.json) | [5,334](../../stacks/python/5-harden) tokens · [pass](python/5-harden/verification.json) |
| [6 · Polish](../../steps/6-polish.md) | [9,659](../../stacks/go/6-polish) tokens · [pass](go/6-polish/verification.json) | [5,493](../../stacks/python/6-polish) tokens · [pass](python/6-polish/verification.json) |
| [7 · Exports](../../steps/7-add-background-job.md) | [11,259](../../stacks/go/7-add-background-job) tokens · [pass](go/7-add-background-job/verification.json) | [6,193](../../stacks/python/7-add-background-job) tokens · [pass](python/7-add-background-job/verification.json) |
| [8 · Live editing](../../steps/8-live-editing.md) | [14,203](../../stacks/go/8-live-editing) tokens · [pass](go/8-live-editing/verification.json) | [8,308](../../stacks/python/8-live-editing) tokens · [pass](python/8-live-editing/verification.json) |

Backend size excludes tests, docs, dependencies, lockfiles and the fixed client. Owned size is the change from the supplied scaffold. Each checkpoint also records whole-app size and tests/docs separately.

## Full-product builds

Each row describes one exact source snapshot. The eight-step effort is the sum of its eight coding sessions; the one-shot starts from a fresh scaffold. Setup, independent checks and later reviewer work are outside these coding totals.

| Application | Owned / whole backend tokens | Coding minutes | Uncached + output tokens | Reviewer HTTP parity |
| --- | ---: | ---: | ---: | --- |
| [Go · eight steps](../../stacks/go/8-live-editing) | 14,203 / 15,746 | 71.0 | 722,152 | [21/21 contract · 3/3 quality · favorites 48/48](go/8-live-editing/reviewer-parity/results.json) · [shared 1/3 + 0/1](go/8-live-editing/reviewer-parity/share-boundary.json) · **not full reviewer parity** |
| [Go · expert one-shot](../one-shot-v2-go-expert/pilot-1/source) | 12,530 / 14,501 | 16.1 | 169,516 | [20/21 contract · 2/3 quality · favorites 48/48](../one-shot-v2-go-expert/pilot-1/reviewer-parity/results.json) · [shared 3/3 + 0/1](../one-shot-v2-go-expert/pilot-1/reviewer-parity/share-boundary.json) · **not full reviewer parity** |
| [Python · eight steps](../../stacks/python/8-live-editing) | 8,308 / 9,014 | 70.2 | 842,429 | [20/21 contract · 3/3 quality · favorites 38/48](python/8-live-editing/reviewer-parity/results.json) · [shared 3/3 + 1/1](python/8-live-editing/reviewer-parity/share-boundary.json) · **not full reviewer parity** |
| [Python · expert one-shot](../one-shot-v2-python-expert/pilot-1/source) | 8,718 / 9,684 | 12.2 | 133,594 | [21/21 contract · 3/3 quality · favorites 38/48](../one-shot-v2-python-expert/pilot-1/reviewer-parity/results.json) · [shared 3/3 + 0/1](../one-shot-v2-python-expert/pilot-1/reviewer-parity/share-boundary.json) · **not full reviewer parity** |

### Repeated production runtime

Two rounds; 16 concurrent users; 3-second warmup and 15-second samples; app and database each limited to 2 CPUs and 1 GiB. The HTTP fixture has 50 users and 500 articles. Ranges show both rounds. Source and image hashes must match the runtime manifest before metrics are shown; all nine HTTP workloads and 10/100/500-subscriber socket results are linked.

| Application | List req/s | Article req/s | SQL / list | Image MB | Cold start seconds | Runtime checks |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| [Go · eight steps](runtime/measured/go-8-live-editing-1) | 2,626–2,877 | 3,975 | 5.00 | 16.1 | 0.30–0.36 | pass |
| [Python · eight steps](runtime/measured/python-8-live-editing-1) | 523–524 | 506–510 | 2.00 | 260.6 | 1.61–1.62 | pass |
| [Go · expert one-shot](runtime/measured/go-one-shot-1) | 1,897–1,908 | 5,361–5,464 | 2.00 | 16.6 | 0.28–0.30 | pass |
| [Python · expert one-shot](runtime/measured/python-one-shot-1) | 371–374 | 367–373 | 3.00 | 373.7 | 1.61–1.69 | pass |

[Runtime manifest and all workloads](runtime/measured/summary.json). Runtime success does not imply supplemental reviewer parity; see the parity column above.

## Try a completed app

From the repository root, use Docker, Node.js 22.12+ (or 20.19+ on the 20.x line), npm, curl and OpenSSL. These commands work from a fresh clone once the corresponding source checkpoint is published. The script installs client dependencies, builds the backend, creates a fresh database, and prints an editor link to open in several tabs. Ctrl-C cleans up the demo.

```sh
tools/lane_demo.sh go
tools/lane_demo.sh python
# Or use the independently built expert app:
tools/lane_demo.sh python one-shot
# Reviewed repairs require passed independent and reviewer checks:
tools/lane_demo.sh python eight-reference
tools/lane_demo.sh python one-shot-reference
```

Set `DEMO_BACKEND_PORT` and `DEMO_FRONTEND_PORT` to override the localhost ports.

## Evidence and limits

- [Go preflight](go/preflight.json) and [Python preflight](python/preflight.json): migrations, durable jobs, sockets, reload, production packaging and image identities.
- Each checkpoint directory contains its measured agent report, effort/failure counts, source inventory, actual isolation probe and independent verification.
- [Comprehension](comprehension/): fresh read-only agents answer the original twelve questions after steps 1 and 6. Scores require source-supported grading.
- Reviewer parity adds the same 21 contract and 3 quality HTTP probes used for the current references. Original failures remain visible; later repairs must be separate snapshots.
- A [source review](REVIEW-NOTES.md) prompted a separate 48-case favorite-count diagnostic, applied equally to every final Go/Python app. It does not change the frozen coding requirements.
- The later [expert review](EXPERT-REVIEW.md) adds three shared-edit contract cases and one envelope-quality case, recorded separately for each final app. References must also pass these checks.
- Tuning feedback uses short 3-second samples. Final HTTP measurements use all nine workloads, 16 users and two 15-second rounds, with app and database each limited to 2 CPUs and 1 GiB. Socket measurements cover 10, 100 and 500 subscribers.
- Full transcripts and compressed raw streams belong in external release assets, with checked hashes and links recorded here when published. They are not committed to Git.

[Detailed method and reproduction commands](METHODOLOGY.md) · [Main comparison](../../README.md) · [Contributing](../../CONTRIBUTING.md)
