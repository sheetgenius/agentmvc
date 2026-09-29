# Go and Python

Two new paths through the same Conduit product: build it in eight successive sessions, then build it again in one fresh expert session. The goal is readable, domain-rich code that uses each stack well, with correctness and production performance measured alongside size.

**Progress: 7/18 coding sessions independently verified.** The full runs are still in progress; intermediate sizes below are not final-product comparisons.

## Start with the code

| Lane | Latest verified sequential source | Owned backend | Expert one-shot |
| --- | --- | ---: | --- |
| Go | [3-package](../../stacks/go/3-package) | 8,225 tokens · 1,015 lines | Pending |
| Python | [4-tune](../../stacks/python/4-tune) | 4,990 tokens · 692 lines | Pending |

**Python:** Django + Django Ninja, with Django associations, migrations and password services; Channels for raw WebSockets; Procrastinate for PostgreSQL jobs. [Why this stack](../../stacks/python/STACK.md).

**Go:** the prepared expert toolkit is Huma + chi, Bun, Goose and River. The sequential agent chose **chi + Bun** and removed Huma in step 1; that is a recorded implementation choice. The independent expert one-shot explicitly asks for Huma typed operations. [Why this toolkit](../../stacks/go/SELECTION.md).

The one-shots start from product-free scaffolds and use the [same expert-v2 prompt](../../one-shot-v2-expert/PROMPT.md) as the recent Rails, Phoenix and TypeScript builds. The sequential lanes use the original eight prompt files. Stack guidance and preparation are disclosed separately; these are distinct conditions, not pooled trials.

## The eight steps

Every source link is an immutable checkpoint. “Pass” means the coordinator reran the applicable frozen checks; production verification begins at step 3.

| Step | Go | Python |
| --- | --- | --- |
| [1 · Base API](../../steps/1-build.md) | [7,236](../../stacks/go/1-build) tokens · [pass](go/1-build/verification.json) | [4,003](../../stacks/python/1-build) tokens · [pass](python/1-build/verification.json) |
| [2 · Drafts](../../steps/2-add-drafts.md) | [8,214](../../stacks/go/2-add-drafts) tokens · [pass](go/2-add-drafts/verification.json) | [4,767](../../stacks/python/2-add-drafts) tokens · [pass](python/2-add-drafts/verification.json) |
| [3 · Production](../../steps/3-package.md) | [8,225](../../stacks/go/3-package) tokens · [pass](go/3-package/verification.json) | [4,767](../../stacks/python/3-package) tokens · [pass](python/3-package/verification.json) |
| [4 · Performance](../../steps/4-tune.md) | Pending | [4,990](../../stacks/python/4-tune) tokens · [pass](python/4-tune/verification.json) |
| [5 · Security](../../steps/5-harden.md) | Pending | Pending |
| [6 · Polish](../../steps/6-polish.md) | Pending | Pending |
| [7 · Exports](../../steps/7-add-background-job.md) | Pending | Pending |
| [8 · Live editing](../../steps/8-live-editing.md) | Pending | Pending |

Backend size excludes tests, docs, dependencies, lockfiles and the fixed client. Owned size is the change from the supplied scaffold. Each checkpoint also records whole-app size and tests/docs separately.

## Try a completed app

With Docker, Node.js and npm installed, these commands build a published step-8 source, create a fresh database, and open the fixed Lit editor. They become available when the corresponding step-8 checkpoint is published. Ctrl-C removes their containers.

```sh
tools/lane_demo.sh go
tools/lane_demo.sh python
# Or use the independently built expert app:
tools/lane_demo.sh python one-shot
```

## Evidence and limits

- [Go preflight](go/preflight.json) and [Python preflight](python/preflight.json): migrations, durable jobs, sockets, reload, production packaging and image identities.
- Each checkpoint directory contains its measured agent report, effort/failure counts, source inventory, actual isolation probe and independent verification.
- [Comprehension](comprehension/): fresh read-only agents answer the original twelve questions after steps 1 and 6. Scores require source-supported grading.
- Reviewer parity adds the same 21 contract and 3 quality HTTP probes used for the current references. Original failures remain visible; later repairs must be separate snapshots.
- Tuning feedback uses short 3-second samples. Final HTTP measurements use all nine workloads, 16 users and two 15-second rounds, with app and database each limited to 2 CPUs and 1 GiB. Socket measurements cover 10, 100 and 500 subscribers.
- Full transcripts and compressed raw streams belong in external release assets, with checked hashes and links recorded here when published. They are not committed to Git.

[Detailed method and reproduction commands](METHODOLOGY.md) · [Main comparison](../../README.md) · [Contributing](../../CONTRIBUTING.md)
