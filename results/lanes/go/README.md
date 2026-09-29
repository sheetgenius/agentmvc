# Go: eight steps and an expert one-shot

Two independent paths reached the complete frozen Conduit gate: an eight-step
build with a fresh agent at each step, and a fresh expert one-shot from the
product-free scaffold. Both final artifacts passed independent development and
production checks: 17 API files, 13 security files, the raw WebSocket protocol,
and four browser tests. Additional reviewer probes and runtime measurements
are separate evidence; passing the frozen gate is not a claim of perfection.

## Start with the code

- [Eight-step final source](../../../stacks/go/8-live-editing/): chi handlers,
  Bun records and query builders, Goose migrations, River jobs, coder/websocket.
- [Expert one-shot source](../../one-shot-v2-go-expert/pilot-1/source/): chi
  handlers, mostly parameterized SQL through Bun's underlying connection,
  Goose, River, coder/websocket; typed Huma operations only for health and tags.
- [Original eight-step prompts](../../../steps/) and the
  [exact expert prompt](../../one-shot-v2-go-expert/pilot-1/frozen-prompt.md).
- Independent gates: [eight-step](8-live-editing/verification.json),
  [one-shot](../../one-shot-v2-go-expert/pilot-1/verification.json).

**Framework adherence is a limitation.** The prepared stack was
Huma/chi/Bun/River, and the expert guidance called for typed Huma operations.
Step 1 removed Huma; the one-shot used it for only two routes. Most request
decoding remains hand-written over `map[string]json.RawMessage` in both apps.
The one-shot also uses little of Bun's model/query API. These are measured
implementation choices, not evidence of what a fully idiomatic Huma/Bun app
can achieve. The original artifacts have been preserved.

## Original measured results

| Metric | Eight-step final | Expert one-shot |
|---|---:|---:|
| Owned backend tokens | 14,203 | 12,530 |
| Owned backend lines | 1,773 | 1,572 |
| Whole backend tokens | 15,746 | 14,501 |
| Test tokens, separate | 116 | 862 |
| Project documentation tokens, separate | 1,850 | 555 |
| Measured coding wall time | 71.0 min across 8 sessions | 16.1 min in 1 session |
| Uncached input + output tokens | 722,152 | 169,516 |
| Commands / nonzero exits | 328 / 25 | 80 / 5 |

Counts use the reviewer's historical `o200k_base` measurer against the frozen
scaffold, with tests and documentation reported separately. The agent's own
one-shot count used different file inclusion and is not the table's source.
Nonzero exits include failed searches, unavailable host Git tooling, and
infrastructure races as well as product/check failures. Eight-step effort
includes repeated onboarding, checks, tuning, and cleanup; it is not an
equal-budget comparison with one-shot effort. Both used `gpt-6-sol`, xhigh.

Raw counts: [eight-step size](8-live-editing/size.json),
[supplementary size](8-live-editing/supplementary-size.json),
[one-shot size](../../one-shot-v2-go-expert/pilot-1/size.json),
[supplementary size](../../one-shot-v2-go-expert/pilot-1/supplementary-size.json),
[one-shot effort](../../one-shot-v2-go-expert/pilot-1/run.json).

| Historical step | Owned tokens | Coding minutes | Independent gates |
|---|---:|---:|---|
| [1. Build](1-build/) | 7,236 | 12.5 | Development passed |
| [2. Drafts](2-add-drafts/) | 8,214 | 7.2 | Development passed |
| [3. Package](3-package/) | 8,225 | 3.5 | Development + production passed |
| [4. Tune](4-tune/) | 9,086 | 10.2 | Development + production passed |
| [5. Harden](5-harden/) | 9,537 | 6.9 | Development + production passed |
| [6. Polish](6-polish/) | 9,659 | 8.3 | Development + production passed |
| [7. Background exports](7-add-background-job/) | 11,259 | 11.1 | Development + production passed |
| [8. Live editing](8-live-editing/) | 14,203 | 11.3 | Development + production passed |

Each step directory contains the frozen prompt, scrubbed transcript, effort,
source identity, size, and independent verification. The one-shot is the
separate `expert-v2-tcp-readiness` condition, not a ninth incremental step.

## Where the rules landed

| Concern | Eight-step final | Expert one-shot |
|---|---|---|
| Visibility and ownership | `articles.go`: `visibleArticle`, `ownedArticle`; list predicates also live there | `articles.go`: `recordBySlug`, `own`, `published`; list predicates also live there |
| Content edits and revision conflicts | Separate author and shared update paths in `articles.go` and `shares.go`, each with a conditional database update | Both entrances call `saveArticle` in `articles.go`; boolean modes distinguish author/shared behavior |
| Publication | `publishArticle` in `articles.go`, conditional draft-to-published update | `publishArticle` in `articles.go`, conditional draft-to-published update |
| Login throttling | `users.go`: `authenticateCredentials`, persisted counters and a 15-minute window | `users.go`: process-local counter, no timed expiry; reset on success/restart |
| Lists and response assembly | `articles.go` filters; `views.go` batches related records per page | `articles.go` composes SQL projections and scans response records |
| Export durability | `exports.go`; export row and River job commit together; worker uses repeatable read | `exports.go`; export row and River job commit together; snapshot data comes from one SQL statement |
| Share authority and room membership | `shares.go` owns key checks; `live.go` owns per-room locks, admission, and delivery | `shares.go` owns key checks, a shared rooms mutex, admission, and delivery |
| Database invariants | Numbered Goose migrations | `00003_product.sql` and later numbered Goose migrations |

Both keep live rooms in one process. The one-shot's common save function is
useful consolidation, but mode flags and map-shaped inputs leave decisions
that typed request records could express more clearly. Its smaller source
count also accompanies a weaker login-throttle lifecycle. The eight-step
`AGENTS.md` was not extended to map the later export/live modules; the
one-shot's rule map includes them, but its README still describes the original
health-only scaffold. These documentation gaps belong to the results.

### Additional reviewer findings

The original one-shot passed 20/21 common contract checks, 2/3 quality checks,
and 48/48 favorite checks. An explicit `revision: null` returned 409 instead
of 422; 25 concurrent bad logins all received 401 before the next request
received 429. Its separate shared-link probe passed 3/3 contract checks but
failed the strict-envelope quality check: an extra outer key was accepted and
the edit mutated the article. See the raw
[common results](../../one-shot-v2-go-expert/pilot-1/reviewer-parity/results.json)
and [share-boundary results](../../one-shot-v2-go-expert/pilot-1/reviewer-parity/share-boundary.json).
Any fixes are unscored reference work; the measured source and table above
remain unchanged.

## Conditions and caveats

### Reviewed reference repairs

The [eight-step reference](8-live-editing/reference-1/README.md) has 14,249 owned
tokens. It corrects shared stale-revision and envelope handling, and omits
article bodies from list queries. The [one-shot reference](../../one-shot-v2-go-expert/pilot-1/reference-1/README.md)
has 12,846 owned tokens. It repairs null revisions, shared envelopes and atomic,
expiring login admission. Both pass independent development/production gates
and all supplemental common, favorites and shared-boundary probes.

These are unscored revisions with explicit parent sources. The one-shot's
limited Huma/Bun adoption remains visible. Its global room lock also spans
database work for unrelated articles; the effect on throughput is not isolated
by the current workload. For a live editor, use `tools/lane_demo.sh go eight-reference`
or `tools/lane_demo.sh go one-shot-reference` from the repository root.

### Preparation and measurement

The scaffold supplied the native release Dockerfile, fast Air loop, and
infrastructure helpers. Step 1 therefore used the disclosed prepared-scaffold
condition, and step 3 reviewed existing packaging. Frozen inputs, fresh Codex
homes, isolation, and approval-free operation are recorded per session.

The eight-step frozen checker sometimes accepted PostgreSQL's temporary Unix
socket server before TCP was ready. Original failures remain recorded. The
[step-3 diagnosis](3-package/verification-attempts/README.md) explains the
independent retry on unchanged application source. The expert one-shot used a
versioned TCP-readiness adapter, proven in its
[readiness preflight](../../one-shot-v2-go-expert/pilot-1/readiness-preflight.json);
its [run record](../../one-shot-v2-go-expert/pilot-1/run.json) identifies both
the inherited fixture and effective condition hashes. This infrastructure
change is another reason not to pool effort blindly.

The step-4 tuning measurements were short feedback runs, not repeated final
performance evidence. They demonstrated bounded list SQL after batching
(62 to 5 anonymous, 103 to 7 signed-in); use subsequent reviewer runtime
results for throughput comparisons. No performance ceiling is inferred from
these two implementations.

## Environment preflight

The [final preflight](preflight.json) passed before any measured Go agent was
launched. It proves the prepared Huma/chi/Bun/River toolchain, not Conduit
product parity or application performance.

- PostgreSQL migrations apply twice safely.
- Bun and River share a transaction: rolled-back work disappears, committed
  work persists before the worker starts and then executes.
- Tests pass with Go's race detector, including raw WebSocket Unicode echo
  and maintained password/JWT libraries.
- Development and the fresh native production image both serve HTTP and raw
  sockets and execute a queued job.
- A development edit reloads in 0.751 seconds in the warmed preflight.
- Production finishes an in-flight database-backed HTTP request after SIGTERM
  before closing its pool and exiting.

The 16.1 MB production image here contains only the scaffold plus disposable
infrastructure probes. It is not an implementation-size or throughput result.
The probe workers, routes and tables are created in `.work/go-track-preflight/`
and are absent from the frozen agent scaffold.

Attempts 1 and 2 caught an error in the maintainer's disposable echo probe:
it closed TCP immediately after writing, producing a host-client protocol
error. A normal WebSocket closing handshake fixed it. Attempt 3 proved those
paths but was superseded when review corrected server shutdown ordering.
The final pass includes that fix and rejects scaffold edits during preflight.
These preparation attempts are separate from measured implementation effort.

Exact versions, image IDs, source hashes, logs and individual checks are in
the JSON record. Stack choice and alternatives are documented in
[the selection note](../../../stacks/go/SELECTION.md).
