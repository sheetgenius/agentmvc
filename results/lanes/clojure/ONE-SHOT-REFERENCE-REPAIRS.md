# One-shot Clojure reference repairs

**Status: published; focused tests, full independent gates and supplemental probes passed. Repeated runtime in progress.** This is an unscored reference. Nothing here changes the measured original or credits it with repaired behavior.

- Original snapshot: `85416e19319c5e1aac46fc3ad2367e340868f5d3b0fcafda844ff9b2f9996118`.
- Published reference: [source](../../one-shot-v2-clojure-expert/pilot-1/reference-1/source/), snapshot `897da5082836db4126c1e91260b23bfc574bedc2bf15c3b890600daba7621f79`.
- Original evidence and findings: [EXPERT-REVIEW.md](EXPERT-REVIEW.md).

## Changes

Paths are relative to the published reference.

| File | Change | Evidence motivating it |
| --- | --- | --- |
| `src/conduit/users.clj` | Fair `Semaphore(2)` bounds all password derive/verify operations; release is in `finally`. Atomically reserve an email's attempt before expensive work, retaining the 20-attempt/minute threshold and existing Argon2id parameters. Expired counters are removed during admission. Token parsing catches only credential failures; database lookup failures propagate. | Repeated heap exhaustion and failed registration after the original common HTTP probe are observed. Unbounded concurrent hashing is the source-supported likely cause; the allocation profile was not measured. Database-error masking was source-inferred. |
| `src/conduit/articles.clj` | Extract the existing edit rule into `edit-locked!`, used by ordinary and shared edits after acquiring their transaction's article lock. | Supports a single update authority with atomic capability revalidation. |
| `src/conduit/shares.clj` | Shared save locks the article and checks that the authorized share/hash is still active before mutation. Rotation, revocation, and deletion use that same article lock. Notify/close rooms only after transactions finish. Guaranteed overflow disconnect and explicit sender shutdown replace the failed close-marker offer and idle-thread leak. | These were concrete source-inferred races/lifecycle defects; original probes did not reproduce them. |
| `src/conduit/http.clj` | Reuse `notify-article!` after author edits and publishing; article deletion uses coordinated share cleanup. | Source showed missing publish notification and deleted rooms retaining sockets. |
| `src/conduit/exports.clj` | Build the stored export inside Repeatable Read, preserving one view across article/comment and tag queries. | Source-inferred mixed-snapshot risk under default Read Committed. |
| `src/conduit/queue.clj` | Configure three retries with 1, 5, and 30 second delays. | Proletarian's default is no retry; transient handler failures otherwise leave pending exports without active jobs. |
| `test/conduit/reference_test.clj` | Tests bounded password work and permit release, 25 simultaneous login reservations, database-error propagation after JWT validation, idle sender shutdown, and queue overflow while a send is blocked. | Targets resource admission, error boundaries, and lifecycle behavior directly. |
| `test/conduit/reference_integration_test.clj` | Real PostgreSQL tests for revocation while a save waits on the article lock, concurrent article/tag mutation during export, transient worker failure, and actual publish/delete HTTP handlers notifying existing members. | Targets transaction and event boundaries rather than merely asserting the chosen implementation. |
| `README.md` | Replace the stale scaffold description with actual application/run/test instructions, the rule map, and the unscored reference changes. | The original README incorrectly described a health-only application; documentation repair was explicitly requested. |

## Verification and current limits

No Clojure process, Docker command, build, or workload was launched during the coordinator's original runtime measurements. Execution began only after its explicit timing-clear message. Every attempt is retained with scrubbed stdout and JSON under [reference reviewer-tests](../../one-shot-v2-clojure-expert/pilot-1/reference-1/reviewer-tests/).

| Attempt | Result |
| --- | --- |
| 1 | Host coordinator import failed before any application command: system Python lacked `tiktoken`. Switched to the existing repository virtual environment. |
| 2–3 | Formatting passed; initial lint reported two suspicious lock-expression warnings. Replaced repeated queue expressions with named queue locals. |
| 4–5 | Formatting and default lint passed; lint has no errors or warnings. |
| 6–9 | Started a disposable PostgreSQL, ran all tests, and stopped the database. **12 tests, 52 assertions, zero failures/errors.** |

The [successful test attempt](../../one-shot-v2-clojure-expert/pilot-1/reference-1/reviewer-tests/attempt-8.json) finished at `2026-09-30T03:24:55.965468+00:00`; [stdout](../../one-shot-v2-clojure-expert/pilot-1/reference-1/reviewer-tests/attempt-8.log) includes the injected job failure, retry, and successful completion. The source fingerprint before and after both lint and tests was `897da5082836db4126c1e91260b23bfc574bedc2bf15c3b890600daba7621f79`.

The nine new tests cover the repaired boundaries; the existing three tests also pass. The database tests observed a save actually waiting on a PostgreSQL lock before revocation committed, forced a concurrent article/tag edit between export reads, exercised the real Proletarian worker through a transient exception, and called the actual publish/delete HTTP handlers. Queue tests blocked a sender and filled its output queue, then verified closure, room release, and thread termination.

The published snapshot passed both [independent development and production gates](../../one-shot-v2-clojure-expert/pilot-1/reference-1/verification.json). The unchanged [HTTP and favorites probes](../../one-shot-v2-clojure-expert/pilot-1/reference-1/reviewer-parity/results.json) passed 21/21 contract cases, 3/3 quality cases and 48/48 favorites cases, including the concurrent login burst. The [shared-boundary probes](../../one-shot-v2-clojure-expert/pilot-1/reference-1/reviewer-parity/share-boundary.json) passed 3/3 contract cases and 1/1 quality diagnostic. All verdicts bind to the reference source hash above. Integration tests require `DATABASE_URL`; the broker points the test container at the separate `agentmvc_test` database, and the fixture migrates it.

The original one-shot common probe is incomplete, not a measured zero contract score. Later passing reference checks must be recorded with the reference source hash, never substituted for that original result. No comparable agent-effort claim is made for these repairs.
