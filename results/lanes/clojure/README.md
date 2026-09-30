# Clojure

An eight-step build and an independent expert one-shot of the same Conduit backend. The prepared scaffold combines Ring/Jetty, Reitit/Malli, next.jdbc/HoneySQL, Integrant, Migratus, Proletarian and Buddy, packaged as a JVM AOT uberjar.

**9/9 coding sessions independently verified.**

[Stack choice and Clojure guidance](../../../stacks/clojure/SELECTION.md) · [Conditions and method](METHODOLOGY.md) · [Shared expert prompt](../../../one-shot-v2-expert/PROMPT.md)

The sequential final uses Reitit/Muuntaja and hand-written validation, with HoneySQL for partial updates. The one-shot connects Malli coercion but declares a schema only for the registration envelope; most validation is hand-written, and HoneySQL is declared but unused. [Code guide](CODE-GUIDE.md) · [Expert review and remaining limits](EXPERT-REVIEW.md)

Recorded coding agent: `gpt-6-sol` / `xhigh` / `codex-cli 0.159.0`. Attribution comes from the 9 run records; reviewer repairs have no measured coding-effort attribution.

## Eight-step history

Each checkpoint preserves its source, prompt, effort, failures and independent verdict. Production checks begin at step 3. Preparation and later reviewer work are outside coding effort.

| Step | Owned backend and independent checks |
| --- | --- |
| [1 · Base API](../../../steps/1-build.md) | [4,273](../../../stacks/clojure/1-build) tokens · [pass](1-build/verification.json) |
| [2 · Drafts](../../../steps/2-add-drafts.md) | [4,935](../../../stacks/clojure/2-add-drafts) tokens · [pass](2-add-drafts/verification.json) |
| [3 · Production](../../../steps/3-package.md) | [4,935](../../../stacks/clojure/3-package) tokens · [pass](3-package/verification.json) |
| [4 · Performance](../../../steps/4-tune.md) | [5,159](../../../stacks/clojure/4-tune) tokens · [pass](4-tune/verification.json) |
| [5 · Security](../../../steps/5-harden.md) | [5,372](../../../stacks/clojure/5-harden) tokens · [pass](5-harden/verification.json) |
| [6 · Polish](../../../steps/6-polish.md) | [5,352](../../../stacks/clojure/6-polish) tokens · [pass](6-polish/verification.json) |
| [7 · Exports](../../../steps/7-add-background-job.md) | [6,427](../../../stacks/clojure/7-add-background-job) tokens · [pass](7-add-background-job/verification.json) |
| [8 · Live editing](../../../steps/8-live-editing.md) | [8,603](../../../stacks/clojure/8-live-editing) tokens · [pass](8-live-editing/verification.json) |

## Independent expert one-shot

[9,312](../../one-shot-v2-clojure-expert/pilot-1/source) tokens · [pass](../../one-shot-v2-clojure-expert/pilot-1/verification.json)

## Full-product sources

| Original source | Owned / whole backend tokens | Coding minutes | Uncached + output tokens | Reviewer checks |
| --- | ---: | ---: | ---: | --- |
| [Eight-step final](../../../stacks/clojure/8-live-editing) | 8,603 / 11,067 | 83.0 | 787,220 | [19/21 contract · 2/3 quality · favorites 48/48](8-live-editing/reviewer-parity/results.json) · [shared 3/3 + 0/1](8-live-editing/reviewer-parity/share-boundary.json) · **not full reviewer parity** |
| [Expert one-shot](../../one-shot-v2-clojure-expert/pilot-1/source) | 9,312 / 12,235 | 14.6 | 206,564 | [HTTP review incomplete · favorites review incomplete](../../one-shot-v2-clojure-expert/pilot-1/reviewer-parity/results.json) · [shared 3/3 + 1/1](../../one-shot-v2-clojure-expert/pilot-1/reviewer-parity/share-boundary.json) · **not full reviewer parity** |

### Repeated original runtime

Two rounds; 16 concurrent users; 3-second warmup and 15-second samples; app and database each limited to 2 CPUs and 1 GiB. The HTTP fixture has 50 users and 500 articles. Ranges show both rounds. Source and image hashes must match the runtime manifest before metrics are shown; all nine HTTP workloads and 10/100/500-subscriber socket results are linked.

| Application | List req/s | Article req/s | SQL / list | Image MB | Cold start seconds | Runtime checks |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| [Eight-step final](runtime/measured/clojure-8-live-editing-1) | 2,150–2,162 | 9,286–9,493 | 4.00 | 364.2 | 1.49–1.72 | pass |
| [Expert one-shot](runtime/measured/clojure-one-shot-1) | 4,197–4,339 | 7,920–8,151 | 3.00 | 365.8 | 1.47 | pass |

[Runtime manifest and all workloads](runtime/measured/summary.json). Runtime success does not imply supplemental reviewer parity; see the parity column above.

The original sequential app failed two common contract cases (malformed owner updates and oversized comment IDs), plus the login-burst and outer shared-envelope quality diagnostics. The original one-shot HTTP review stopped during a concurrent login burst with repeated JVM heap exhaustion; its HTTP review is incomplete, and the following favorites setup failed. Its fresh shared-boundary checks passed. The nine repeated HTTP workloads do not include that login burst, so their passing runtime results do not resolve this failure. [Observed evidence and source review](EXPERT-REVIEW.md).


## Reviewed references

These independently checked repairs preserve their measured parents and earlier attempts. Their editing effort is unscored; supplemental review is shown separately.

| Source | Owned backend tokens | Reviewer checks |
| --- | ---: | --- |
| [Eight-step final · reference 1](8-live-editing/reference-1/source) | 8,634 | [21/21 contract · 3/3 quality · favorites 48/48](8-live-editing/reference-1/reviewer-parity/results.json) · [shared 3/3 + 1/1](8-live-editing/reference-1/reviewer-parity/share-boundary.json) |
| [Expert one-shot · reference 1](../../one-shot-v2-clojure-expert/pilot-1/reference-1/source) | 9,891 | [21/21 contract · 3/3 quality · favorites 48/48](../../one-shot-v2-clojure-expert/pilot-1/reference-1/reviewer-parity/results.json) · [shared 3/3 + 1/1](../../one-shot-v2-clojure-expert/pilot-1/reference-1/reviewer-parity/share-boundary.json) |

### Repeated reference runtime

Two rounds; 16 concurrent users; 3-second warmup and 15-second samples; app and database each limited to 2 CPUs and 1 GiB. The HTTP fixture has 50 users and 500 articles. Ranges show both rounds. Source and image hashes must match the runtime manifest before metrics are shown; all nine HTTP workloads and 10/100/500-subscriber socket results are linked.

| Application | List req/s | Article req/s | SQL / list | Image MB | Cold start seconds | Runtime checks |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| [Eight-step final · reference 1](runtime/reference/clojure-8-live-editing-reference-1) | 2,096–2,142 | 9,352–9,398 | 4.00 | 364.2 | 1.49–1.61 | pass |
| [Expert one-shot · reference 1](runtime/reference/clojure-one-shot-reference-1) | 4,243–4,303 | 7,886–8,165 | 3.00 | 365.8 | 1.46–1.49 | pass |

[Runtime manifest and all workloads](runtime/reference/summary.json). Each runtime label names the exact reference version measured, which may precede a newer verified reference.

## Evidence and limits

Backend size excludes dependencies, compiled output, tests and Markdown; tests/docs are recorded separately. Owned size uses the frozen prepared scaffold as its baseline. This focused library assembly is not a Rails-style integrated model framework.

AOT compiles application namespaces to JVM bytecode. JVM JIT warmup still matters; the common short performance windows do not establish fully warmed steady-state performance or a language ranking.

[Environment preflight and its actual verdict](preflight.json)

[Comprehension after 1-build: 12/12](comprehension/clojure-after-1-build)

[Comprehension after 6-polish: 12/12](comprehension/clojure-after-6-polish)

[Scrubbed transcripts and raw measurements](https://github.com/sheetgenius/agentmvc/releases/tag/clojure-lane-v1) · [Artifact hashes and provenance](artifacts-v1.json). Full evidence stays outside Git.

Try a measured final app from the repository root (Docker and Node.js required):

```sh
tools/lane_demo.sh clojure eight
tools/lane_demo.sh clojure one-shot
```

Use the separately reviewed references:

```sh
tools/lane_demo.sh clojure eight-reference
tools/lane_demo.sh clojure one-shot-reference
```

