# Clojure expert review

## Scope and evidence

This review covers the **original measured outputs**. Later reference repairs are separate and do not replace these results.

| Output | Immutable source SHA-256 | Independent verification |
| --- | --- | --- |
| Sequential Step 8 (`stacks/clojure/8-live-editing`) | `0aebf25fee2220cdeab77162529da5e9605ffc60190f1c4560d2a6edf9bd9fc1` | Development and production exit 0; [record](8-live-editing/verification.json) |
| Fresh one-shot (`results/one-shot-v2-clojure-expert/pilot-1/source`) | `85416e19319c5e1aac46fc3ad2367e340868f5d3b0fcafda844ff9b2f9996118` | Development and production exit 0; [record](../../one-shot-v2-clojure-expert/pilot-1/verification.json) |

All 39 sequential and 33 one-shot source file hashes were checked against their snapshots. Step 7's export implementation was also reviewed and is unchanged in the sequential final. Source references below use **S** for the sequential final and **O** for the one-shot final; paths are under `src/conduit/` unless stated otherwise.

## Observed supplemental results

The same existing probes were used on both outputs, under two CPUs and 1 GiB. These supplement the frozen gates; quality diagnostics remain separate from contract assertions.

| Check | Sequential | One-shot |
| --- | --- | --- |
| Common HTTP contract | 19/21 | Incomplete: timeout; no retained per-case summary |
| Common HTTP quality | 2/3 | Incomplete |
| Favorites correctness | 48/48 | Setup registration returned 500; behavior cases did not run |
| Shared-edit boundary contract | 3/3 | 3/3 on a fresh instance |
| Extra outer share-envelope key, quality only | Accepted and mutated: 0/1 | Rejected without mutation: 1/1 |

Evidence: [sequential common/favorites](8-live-editing/reviewer-parity/results.json), [sequential share](8-live-editing/reviewer-parity/share-boundary.json), [one-shot common/favorites](../../one-shot-v2-clojure-expert/pilot-1/reviewer-parity/results.json), [one-shot share](../../one-shot-v2-clojure-expert/pilot-1/reviewer-parity/share-boundary.json).

### Required behavior defects observed in the sequential final

1. **Malformed article envelope mutates the article.** An authorized `PUT` with `{"article":[]}` returned 200 and advanced revision from 3 to 4; the expected response is 422. `S/articles.clj:97–117` lacks a map check and treats this input as an empty patch. Add the check after visibility/ownership, preserving their error precedence.
2. **An out-of-range comment ID produces 500.** The `huge_comment_id` probe expected the structured 404 response. `S/articles.clj:196–201` calls `Long/parseLong` without translating its exception. Use a checked parser and the normal comment-not-found path. The one-shot source already catches this exception (`O/articles.clj:200–206`), but its interrupted common run supplies no retained confirmation.

### Availability and quality failures observed

**One-shot heap exhaustion is the most serious observed operational issue.** The common HTTP run timed out. Its [runner log](../../one-shot-v2-clojure-expert/pilot-1/reviewer-parity/runner.log) records repeated `OutOfMemoryError: Java heap space` on login requests and later registration. Favorites setup then returned 500. `O/users.clj:69–84` checks its failure counter before expensive password verification and reserves no capacity; Argon2id work is also unbounded across requests. This is consistent with concurrent password work exhausting the configured heap, but no allocation profile or complete burst status distribution was retained. It is an observed availability failure under a quality probe, not a fabricated 0/21 contract score.

**Sequential login admission also races.** All 25 simultaneous bad logins returned 401; only the subsequent request returned 429. `S/users.clj:60–68` separates counter checking from incrementing. The frozen sequential rate-limit gate passed; the burst diagnostic did not.

**Sequential shared PUT ignores extra outer keys.** Its inner article shape is checked, but `S/http.clj:98` extracts that object before validation. The extra-envelope probe received 200 and changed the article. This remains quality-only, matching the probe's classification.

## Architecture and idiomatic library use

- **Both are recognizable Clojure applications.** Ordinary functions and maps, parameterized SQL, next.jdbc transactions, Ring/Reitit/Muuntaja, Integrant, Buddy, Migratus, and Proletarian carry the implementation. Neither invents a macro framework or hides business logic in database triggers. Explicit SQL is reasonable here; an ORM rewrite is not a review requirement.
- **Sequential exports are particularly clear.** `S/exports.clj:16–20` creates the export and job in one transaction. One SQL statement reads article fields, tags, and comment counts; a conditional completion update prevents redelivery replacing a finished snapshot (`40–50`). Its worker configures three delayed retries and starts before HTTP (`S/system.clj:14–22,33–48`). These match Proletarian's transactional enqueue and at-least-once model. [Proletarian 1.0.115 documentation](https://cljdoc.org/d/msolli/proletarian/1.0.115/doc/readme).
- **Sequential capability mutations coordinate correctly.** Share save, rotation, and revocation take the article lock; save rechecks the key after acquiring it (`S/shares.clj:32–47,66–81`). Both outputs generate strong random keys and store hashes, expose only the four shared article fields, and suppress older socket revisions.
- **One-shot improves several boundaries and query paths.** It checks object envelopes, serializes ordinary article edits with a row lock, catches duplicate-registration SQLSTATE 23505, joins comment authors instead of querying per comment, and supplies article/tag/favorite/comment indexes. Both compute favorite totals separately from favorite-based membership filters. The sequential favorites probe confirms that distinction; it does not measure scaling.
- **Malli is used narrowly in one-shot.** `O/http.clj:54,205–212` wires coercion and declares one registration envelope schema, `[:map [:user map?]]`. Most field and domain validation remains handwritten. The sequential output uses manual validation throughout.

## Concrete source-inferred risks, not reproduced by these probes

| Output | Risk and evidence | Suggested repair/proof |
| --- | --- | --- |
| One-shot | Shared authorization occurs in middleware, before `articles/edit!` acquires its row lock; `shares/edit!` never rechecks the capability (`http.clj:167–169`, `shares.clj:93–105`). A request can wait, be revoked, then mutate. | Coordinate capability recheck, rotation, and save in one transaction; prove a blocked save cannot cross revocation. |
| One-shot | Export fields/counts and tags are read in separate statements (`exports.clj:30–44`). Under default Read Committed, a concurrent edit can produce old article data with new tags. | Use one coherent snapshot and test a concurrent article/tag edit. PostgreSQL gives each Read Committed statement a new snapshot. [Isolation documentation](https://www.postgresql.org/docs/17/transaction-iso.html). |
| One-shot | The worker supplies no retry strategy (`queue.clj:5–12`); Proletarian's default is no retries. A handler exception can leave an export pending after its job is archived. | Configure a bounded retry policy and prove recovery after a transient handler failure. This is an operational concern beyond the frozen happy path. |
| One-shot | When the 256-message socket queue is full, both the message offer and subsequent close-marker offer may fail (`shares.clj:37–39`). Broadcast has already advanced the revision. Also, ordinary close removes membership without ending a sender blocked in `take` (`44–66,149`). | Guarantee overflow disconnection and sender termination; test a full queue and an idle disconnect. |
| One-shot | Publishing increments revision but its HTTP route never broadcasts (`http.clj:102–105`); deletion removes the share row without closing its room (`98–101`). | Notify revision changes and release deleted-article rooms; prove existing subscribers receive the intended event. Deletion cleanup is a lifecycle concern, not a separately scored probe here. |
| Sequential | One global live lock covers subscription database reads and synchronous socket sends (`live.clj:7–25,60–98`). A slow operation can delay unrelated rooms and the five-second unauthenticated-close task. | Isolate per-room coordination and bound output work while retaining ordering. No slow-client failure was reproduced. [Ring synchronous/async send API](https://ring-clojure.github.io/ring/ring.websocket.html). |

Other source risks are narrower: sequential favorite counts lack an article-leading index; concurrent duplicate registration can expose a SQL exception; omitted-revision edits still use compare-and-swap. One-shot token handling catches database lookup failures as authentication failures (`users.clj:17–23`). These are not additional measured failures.

## Maintainability and conclusion

The sequential final has the more complete product README and stronger export/capability transaction coordination. One-shot has useful boundary and index improvements, but its socket lifecycle and password-work admission need attention. One-shot also retains an unused HoneySQL dependency, and its README still describes a health-only scaffold; those are cleanup issues, not contract failures.

Both outputs passed the frozen development and production gates. The supplemental evidence exposes defects those gates missed, especially the one-shot availability failure. These two runs do not establish a general language or model ranking. Any repaired reference must retain a distinct source snapshot and its own verification evidence; repairs cannot be credited to the measured originals.
