# Clojure

An eight-step build and an independent expert one-shot of the same Conduit backend. The selected stack combines Ring/Jetty, Reitit/Malli, next.jdbc/HoneySQL, Integrant, Migratus, Proletarian and Buddy, packaged as a JVM AOT uberjar.

**6/9 coding sessions independently verified.**

[Stack choice and Clojure guidance](../../../stacks/clojure/SELECTION.md) · [Conditions and method](METHODOLOGY.md) · [Shared expert prompt](../../../one-shot-v2-expert/PROMPT.md)

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
| [7 · Exports](../../../steps/7-add-background-job.md) | Pending |
| [8 · Live editing](../../../steps/8-live-editing.md) | Pending |

## Independent expert one-shot

Pending


## Evidence and limits

Backend size excludes dependencies, compiled output, tests and Markdown; tests/docs are recorded separately. Owned size uses the frozen prepared scaffold as its baseline. This focused library assembly is not a Rails-style integrated model framework.

AOT compiles application namespaces to JVM bytecode. JVM JIT warmup still matters; the common short performance windows do not establish fully warmed steady-state performance or a language ranking.

[Environment preflight and its actual verdict](preflight.json)

[Comprehension after 1-build: 12/12](comprehension/clojure-after-1-build)
