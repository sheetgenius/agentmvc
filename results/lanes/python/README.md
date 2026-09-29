# Python: Django, Ninja, Channels and Procrastinate

Two independent builds and their repaired references show different tradeoffs within the same stack. Start with the source map below; the measured originals remain unchanged. References are separately labeled maintainer work.

| Implementation | Source | Owned / whole backend tokens | Test tokens | Measured agent effort |
|---|---|---:|---:|---|
| Eight-step final | [Application](../../../stacks/python/8-live-editing/), [rule map](../../../stacks/python/8-live-editing/README.md) | 8,308 / 9,014 | 236 | 70.2 min across all eight steps; 842,429 uncached + output tokens |
| Expert one-shot | [Application](../../one-shot-v2-python-expert/pilot-1/source/), [rule map](../../one-shot-v2-python-expert/pilot-1/source/AGENTS.md) | 8,718 / 9,684 | 944 | 12.2 min; 133,594 uncached + output tokens |
| Eight-step reference-1 | [Repaired application](8-live-editing/reference-1/source/) | 8,429 / 9,135 | 853 | Unscored maintainer work; no comparable effort figure |
| One-shot reference-2 | [Repaired application](../../one-shot-v2-python-expert/pilot-1/reference-2/source/) | 9,058 / 10,047 | 3,148 | Unscored maintainer work; failed reference-1 retained |

Sizes use `o200k_base` against the frozen product-free scaffold; tests and docs are separate. [Eight-step size](8-live-editing/size.json), [one-shot size](../../one-shot-v2-python-expert/pilot-1/size.json) and [effort](../../one-shot-v2-python-expert/pilot-1/run.json), [reference provenance](8-live-editing/reference-1/reference.json). Eight-step effort sums the eight `run.json` files here and includes repeated phase gates. The one-shot had all features in its initial prompt and a versioned PostgreSQL TCP-readiness adapter; its effort is a different condition, not an eight-step speedup estimate.

## Where to look in the code

| Concern | Eight-step and its reference | Expert one-shot |
|---|---|---|
| HTTP boundaries | Separate `accounts`, `articles`, `exports`, `sharing` Ninja routers; typed bodies and auth hooks | One `api.py`; Ninja routes and errors, with explicit JSON decoding, auth and pagination helpers |
| Rules | Model methods (`publish`, `set_title`, `Export.complete`) plus named helpers beside each domain router | `domain.py` owns typed inputs, visibility, password policy and one locked `commit_edit` for author and capability edits |
| Persistence | Django `AbstractUser`, many-to-many follows/favorites, PostgreSQL array tags; QuerySet annotations load viewer state | Django records with explicit Follow/Favorite/ArticleTag models; publication/revision/nonempty constraints and list indexes |
| Live delivery | Channels consumers **and group delivery**; current room counts are read when presence events are delivered | Channels JSON consumer plus a custom `Rooms` registry, lock, fanout and revision ordering |
| Durable work | Procrastinate task calls `Export.complete` under a row lock | Procrastinate task builds the snapshot under a row lock |

All versions use Django migrations, ORM transactions and password hashing, PyJWT, Uvicorn ASGI, and a PostgreSQL-backed Procrastinate worker beside the web process in one container. Queue insertion shares the export row's transaction. The fixed Lit client is unchanged.

## What the expert prompt changed

The one-shot is **410 owned tokens larger** than the measured eight-step result. Its clearest improvement is [one content-edit operation](../../one-shot-v2-python-expert/pilot-1/source/conduit/domain.py): author and shared updates use the same lock, revision check, write and post-commit broadcast. Its [five direct tests](../../one-shot-v2-python-expert/pilot-1/source/tests/test_rules.py) exercise visibility, revision conflicts, password policy, export/job rollback and the room cap. It also expresses more invariants as database constraints.

The cost is more plumbing owned by the application. Ninja no longer decodes most request bodies or provides route auth hooks; the app manually invokes Pydantic and authentication. Explicit relation models replace Django's many-to-many declarations, and custom socket fanout replaces Channels groups. Domain decisions are easier to find centrally, while `api.py` and `domain.py` are larger than the eight-step domain modules.

Both implementations bound article-list query counts, but the one-shot prefetches relational tags and separately loads viewer sets; the eight-step uses array tags plus SQL annotations and defers article bodies. The one-shot still loads bodies for summaries. Signed comment rendering performs a follow lookup per comment in both measured originals; reference-1 annotates that lookup. These are source observations, not a measured final throughput ranking.

## What verification actually established

The four entries above passed independent development and fresh production gates: 17 HTTP acceptance files, 13 security files, the raw socket protocol, and four browser tests. [Eight-step](8-live-editing/verification.json), [one-shot](../../one-shot-v2-python-expert/pilot-1/verification.json), [eight-step reference](8-live-editing/reference-1/verification.json), [one-shot reference-2](../../one-shot-v2-python-expert/pilot-1/reference-2/verification.json).

Supplemental reviewer probes found gaps beyond those frozen gates:

- **Eight-step original:** malformed author-edit JSON was accepted; a favorites filter also narrowed the favorite count itself (38/48 supplemental favorite assertions). [Recorded findings](8-live-editing/reviewer-parity/results.json).
- **Eight-step reference-1:** explicit edit-envelope decoding repairs the malformed request; a semi-join separates favorite filtering from aggregation; comment follow state is annotated. The completed common, favorites and [shared-boundary probes](8-live-editing/reference-1/reviewer-parity/share-boundary.json) pass. [Results](8-live-editing/reference-1/reviewer-parity/results.json).
- **One-shot original:** common HTTP probes pass, but the same favorite-count defect remains (38/48). Inner shared fields are strict, while an extra outer-envelope field is silently accepted and the edit proceeds. [HTTP/favorites results](../../one-shot-v2-python-expert/pilot-1/reviewer-parity/results.json), [shared-boundary result](../../one-shot-v2-python-expert/pilot-1/reviewer-parity/share-boundary.json).

## Remaining limits and next work

All versions keep room presence and delivery in one process. Multiple Uvicorn workers or replicas require shared admission/presence and cross-process delivery. Development reloads the web process; job changes require a worker restart.

Source review also identified two one-shot defects: its login counter has no expiry and never resets after reaching 20 failures, even with a valid password; article deletion removes the share row without notifying admitted sockets. The separate [one-shot reference-1](../../one-shot-v2-python-expert/pilot-1/reference-1/source/) repairs those, favorite filtering, the shared envelope, and read-query costs. Its focused tests and independent development gate passed, but **production failed** a browser presence check after simultaneous joins. [Preserved verdict](../../one-shot-v2-python-expert/pilot-1/reference-1/verification.json). It is not a fully verified replacement.

[Reference-2](../../one-shot-v2-python-expert/pilot-1/reference-2/README.md) now passes independent development and production gates, plus every common, favorites and shared-boundary reviewer probe. It serializes each client's ready, presence, update and revocation sends, reads current membership at presence delivery, and refreshes the joining client too. Deterministic tests reproduced stale counts for delayed joins and overlapping leaves in reference-1; those now pass, alongside ready/update and revocation ordering regressions (16 direct tests total). It contains 9,058 owned backend tokens. Reference-1 and both measured originals are preserved.

The one-shot still holds one global room lock across a database lookup. That can couple unrelated rooms under slow queries; its latency impact is unmeasured. Runtime comparisons remain pending; the short step-4 tuning samples describe an earlier source version.

To try either measured app with the fixed editor, run from the repository root (Docker and Node required):

```sh
tools/lane_demo.sh python eight
# or: tools/lane_demo.sh python one-shot
# Reviewed references:
tools/lane_demo.sh python eight-reference
# or: tools/lane_demo.sh python one-shot-reference
```

The script prints an editing link; Ctrl-C removes the demo containers and temporary client. For the preserved progression, browse [all eight source snapshots](../../../stacks/python/) and their adjacent result directories here.
