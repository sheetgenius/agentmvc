# Reading the Clojure backend

Two preserved implementations were built with `gpt-6-sol` at `xhigh` reasoning. Owned size is measured against the frozen product-free scaffold; tests and docs are separate.

| Implementation | Owned / whole backend tokens | Test tokens | Coding effort |
| --- | ---: | ---: | --- |
| [Eight-step final](../../../stacks/clojure/8-live-editing/) | 8,603 / 11,067 | 97 | 83.0 minutes across eight sessions; 787,220 uncached + output tokens |
| [Expert one-shot](../../one-shot-v2-clojure-expert/pilot-1/source/) | 9,312 / 12,235 | 403 | 14.6 minutes; 206,564 uncached + output tokens |

[Eight-step size](8-live-editing/size.json), [one-shot size](../../one-shot-v2-clojure-expert/pilot-1/size.json), [one-shot effort](../../one-shot-v2-clojure-expert/pilot-1/run.json). Eight-step effort sums its eight `run.json` files and includes repeated phase gates. The one-shot starts with every feature requested together; these are different build conditions, not a controlled speedup estimate.

Both originals passed independent development and production checks: [eight-step](8-live-editing/verification.json), source SHA-256 `0aebf25fee2220cdeab77162529da5e9605ffc60190f1c4560d2a6edf9bd9fc1`; [one-shot](../../one-shot-v2-clojure-expert/pilot-1/verification.json), source SHA-256 `85416e19319c5e1aac46fc3ad2367e340868f5d3b0fcafda844ff9b2f9996118`. The observations below come from their source; they do not establish a throughput ranking or comprehensive concurrency correctness.

## Eight-step source map

| Concern | Files and responsibility |
| --- | --- |
| HTTP boundary | [http.clj](../../../stacks/clojure/8-live-editing/src/conduit/http.clj): Reitit route data, Muuntaja JSON middleware, authentication wrappers, error responses and live notifications after writes |
| Accounts | [users.clj](../../../stacks/clojure/8-live-editing/src/conduit/users.clj): Buddy password hashing and signed tokens, password policy, account updates, follows and a Caffeine login-failure cache |
| Articles | [articles.clj](../../../stacks/clojure/8-live-editing/src/conduit/articles.clj): draft visibility, ownership, publication, content revisions, tags, comments, favorites and response projection |
| Capability editing | [shares.clj](../../../stacks/clojure/8-live-editing/src/conduit/shares.clj): key generation and hashing, share rotation/revocation, strict shared-edit fields and restricted response maps |
| Durable exports | [exports.clj](../../../stacks/clojure/8-live-editing/src/conduit/exports.clj): export ownership, transactional enqueue and immutable completed snapshots |
| Live rooms | [live.clj](../../../stacks/clojure/8-live-editing/src/conduit/live.clj): Ring WebSocket callbacks, subscription deadline, admission, presence, revision ordering and revocation |
| Infrastructure | [system.clj](../../../stacks/clojure/8-live-editing/src/conduit/system.clj): Integrant startup/shutdown for Hikari, Migratus, Proletarian, rooms and Jetty; [store.clj](../../../stacks/clojure/8-live-editing/src/conduit/store.clj): small next.jdbc wrappers |

## Eight-step library use

The final [dependency manifest](../../../stacks/clojure/8-live-editing/deps.edn) uses Ring/Jetty, Reitit and Muuntaja for HTTP. Validation is handwritten: route handlers extract maps, domain functions check their contents, and `ex-info` carries status and error data. **Malli is absent from this final source.** The prepared stack selection should not be read as proof of schema-driven validation in the measured application.

Persistence is explicit SQL through next.jdbc, with HoneySQL used for dynamic account and article updates. Migratus applies the [SQL migrations](../../../stacks/clojure/8-live-editing/resources/migrations/). The small [domain.clj](../../../stacks/clojure/8-live-editing/src/conduit/domain.clj) shares required-field, existence and ownership checks; most business rules live beside their database operations. Integrant provides lifecycle wiring, while Proletarian supplies the durable queue and worker. Jetty and the worker run in the same JVM. [tools.build](../../../stacks/clojure/8-live-editing/build.clj) produces an AOT uberjar for the non-root [production image](../../../stacks/clojure/8-live-editing/Dockerfile).

## Three eight-step reading paths

1. **Follow one content edit.** In `articles.clj`, `update!` checks ownership and optional client revision, then calls `update-row!`. That helper builds a HoneySQL update with `select-keys` and `cond->`, increments the revision, and matches the old revision in SQL. In `shares.clj`, `save!` locks the article, rechecks the capability, requires exactly `title`, `body` and `revision`, then calls the same helper. The two entry points share the write mechanism while retaining their different permissions and input contracts.

2. **Follow an export across the queue.** `exports/request!` inserts the export and calls `job/enqueue!` using the same transaction. `build!` reads articles, tags and comment counts in one SQL statement; `snapshot` turns ordered rows into maps using `partition-by` and `mapv`. The final update requires `completed_at IS NULL`, so a retry cannot replace an already completed snapshot. `system.clj` registers the job handler and retry schedule.

3. **Follow a socket subscription.** `live/listener` authenticates the share key, schedules closure of unsubscribed sockets after five seconds, enforces a 100-member cap, then sends `ready` and presence. Room members carry their last sent revision; `updated!` suppresses older updates. `revoked!` removes the room and closes its members. The corresponding handlers in `http.clj` call these functions after edits, publication, share rotation/revocation and article deletion.

## Eight-step tradeoffs

- **SQL is easy to inspect; projections need deliberate maintenance.** `article-page` and `present-many` use four queries for a nonempty listing and batch author/viewer details and tags. The list query still selects article bodies before omitting them from response maps. Comment rendering loads an author per comment and, for signed-in viewers, a follow lookup too.
- **Notification ownership sits at the HTTP boundary.** Domain write functions return data; handlers broadcast it. A future caller of those write functions must also arrange the corresponding live notification.
- **Rooms and login counters belong to one process.** Live rooms use one lock covering all rooms, including subscription database reads and socket sends. This makes ordering explicit but can couple unrelated rooms under slow I/O. Multiple JVMs would need shared admission/presence and delivery. The expiring login-failure cache is also local to each JVM.
- **Direct tests are sparse.** The preserved [test file](../../../stacks/clojure/8-live-editing/test/conduit/http_test.clj) checks only the health route. The independent benchmark gates supply the recorded feature verification; the source contains no direct regression tests for the edit, export or room logic above.

## What the independent one-shot changes

The one-shot is **709 owned backend tokens larger**. It keeps domain modules but combines live rooms with capability operations in [shares.clj](../../one-shot-v2-clojure-expert/pilot-1/source/src/conduit/shares.clj), and extracts [rules.clj](../../one-shot-v2-clojure-expert/pilot-1/source/src/conduit/rules.clj). Its [direct rule tests](../../one-shot-v2-clojure-expert/pilot-1/source/test/conduit/rules_test.clj) cover draft visibility, ownership, interactions and revision conflicts; exports and sockets still have no direct regression tests.

| Concern | One-shot implementation and tradeoff |
| --- | --- |
| Validation and libraries | [http.clj](../../one-shot-v2-clojure-expert/pilot-1/source/src/conduit/http.clj) wires Reitit/Malli coercion and Muuntaja. Its sole declared body schema checks that registration contains a `user` map; most validation remains handwritten. HoneySQL remains in `deps.edn` but is unused by the application source. |
| Domain boundary | HTTP calls `authored!` before edit, publish and delete. [articles/edit!](../../one-shot-v2-clojure-expert/pilot-1/source/src/conduit/articles.clj) shares a row lock and revision check between author and capability edits; its caller owns authorization. The eight-step entry points keep author ownership checks inside their write functions. |
| Read queries | Nonempty article listings use three queries, and comment listing joins author/follow data. Both originals still select article bodies for summary listings. These query shapes are source observations, not measured latency results. |
| Exports | [exports/snapshot!](../../one-shot-v2-clojure-expert/pilot-1/source/src/conduit/exports.clj) locks the pending export while reading articles and then tags in a transaction. Both originals enqueue transactionally and prevent replacement of completed exports. The one-shot's separate reads do not specify a stronger isolation level. |
| Live delivery | Each socket has a 256-message queue and a virtual-thread sender, moving socket sends outside the global room lock. Subscription database reads still hold that lock, and rooms remain process-local. The full-queue branch attempts to enqueue a close marker into the same full queue, so closure on overflow is not assured by that code. |

The one-shot validates the shared edit's outer envelope as well as its inner fields. Its live wiring has source-visible omissions: article deletion does not revoke admitted sockets, and publication does not broadcast the new revision. It also authorizes a shared request before the article transaction without rechecking the capability under that transaction's lock. These are review observations beyond the passing frozen gates; consult the [expert review](EXPERT-REVIEW.md) for separately recorded probes and their scope. Both measured originals remain preserved.

For measured history and conditions, see the [lane report](README.md) and [methodology](METHODOLOGY.md).
