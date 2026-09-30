# AgentMVC handoff for Opus

Prepared 30 September 2026. This is a handoff from the agent that completed the Go, Python and Clojure tracks. It describes the published state and my recommendations for the next investigation. The latest benchmark evidence is anchored at commit `b898a940754b19bbdfbcc26fa445d3dd15b3f541`; this handoff adds documentation.

AgentMVC asks how a coding model, language, framework and build protocol affect the effort, correctness, source size and runtime of the same application. The product is RealWorld Conduit plus drafts, durable background exports and live shared editing through a fixed Lit client. My strongest recommendation is to explore **how a fresh agent changes a product rule across an existing application**. The repository now has enough working implementations and preserved evidence to make that question concrete.

## Published state

`main` is the canonical history. Before this document was added, it matched `origin/main` with a clean working tree. All five GitHub releases were published. The Go/Python and Clojure archive digests and downloaded bytes were checked against their manifests on 30 September.

| Track | Completed evidence | Starting point for further work |
| --- | --- | --- |
| Rails, Phoenix, Loco | Original eight-step study, with source, effort, gates, runtime and reader results | Historical study in [`stacks/`](../stacks/) and [findings](README.md) |
| Rails, Phoenix, AdonisJS | Expert one-shot originals and separately labeled reference revisions | [Current comparison and source links](../results/v2-expert-symmetry/README.md) |
| Go and Python | 18 measured coding sessions, four readers, four reviewed references, repeated original and reference runtime measurements | [Lane results](../results/lanes/README.md), [Go guide](../results/lanes/go/README.md), [Python guide](../results/lanes/python/README.md) |
| Clojure | Nine measured coding sessions, two readers, two reviewed references, repeated original and reference runtime measurements | [Track results](../results/lanes/clojure/README.md), [code guide](../results/lanes/clojure/CODE-GUIDE.md), [expert review](../results/lanes/clojure/EXPERT-REVIEW.md) |
| Other investigations | IHP builds and a separate guided diagnostic; Servant pilot; Ruby compiler feasibility probe | Their individual result pages retain their distinct conditions |

The [cohort index](../results/cohorts.json) contains 105 entries: 65 measured coding sessions, 12 readers, 11 references, 15 preflights and two diagnostics. All measured coding sessions record `gpt-6-sol` with `xhigh` reasoning. Clojure used Codex CLI 0.159.0; earlier coding runs used 0.157.1. No measured GPT-6.1 result is recorded. See [comparison rules](cohorts.md).

The current download releases are [Go and Python](https://github.com/sheetgenius/agentmvc/releases/tag/go-python-lanes-v1) and [Clojure](https://github.com/sheetgenius/agentmvc/releases/tag/clojure-lane-v1), with [Go/Python](../results/lanes/artifacts-v1.json) and [Clojure](../results/lanes/clojure/artifacts-v1.json) manifests. Older releases are [raw data v1](https://github.com/sheetgenius/agentmvc/releases/tag/raw-data-v1), [expert v2](https://github.com/sheetgenius/agentmvc/releases/tag/raw-data-v2-expert) and [expert symmetry](https://github.com/sheetgenius/agentmvc/releases/tag/raw-data-v2-expert-symmetry). Large scrubbed transcripts and raw measurements live in these archives; the repository holds their summaries and provenance.

The divergent [`clean-slate` branch](https://github.com/sheetgenius/agentmvc/tree/clean-slate) is also published, at `51e5f13`. Its four unique commits explore a ledger, runner tooling and a smaller documentation structure from an older baseline. It predates the completed Go/Python/Clojure evidence. Treat its ideas as material to inspect selectively; use `main` for the current experiment history.

## Findings that should shape the next work

Passing the frozen gates establishes their checked behavior. Supplemental review found defects in otherwise passing builds, and the repairs have their own source identities and results. For example, Python one-shot reference-1 failed production presence behavior; reference-2 is the accepted replacement, and the failed revision remains available.

Clojure makes this distinction especially clear. All nine coding sessions passed their required independent gates. Supplemental review found malformed sequential edits that mutated articles, oversized comment IDs returning 500, login admission races and loose shared envelopes. The original one-shot exhausted its heap during concurrent bad logins, leaving its common HTTP review incomplete. Both Clojure references pass development, production and supplemental probes. The ordinary nine-workload runtime suite passed for the originals too, but does not include that login burst. Read the [exact verdicts](../results/lanes/clojure/EXPERT-REVIEW.md) before summarizing correctness.

The strongest existing designs offer different things to study: Rails expresses much of this domain compactly through framework conventions; Phoenix uses supervision and PubSub; Python's sequential build delegates more boundary and delivery work to Ninja and Channels; Clojure's sequential build has explicit export and capability transaction coordination. These are useful examples, with the limitations recorded in their source guides. Their observed size and throughput do not establish a universal stack ranking.

## Recommended areas to explore

### Product evolution with a fresh agent

This is my highest priority. The existing reader questions score near the ceiling and mostly test locating established rules. A change that crosses HTTP, lists, counts, tags, exports, capabilities, sockets and old database rows should reveal much more about maintainability.

Start with the proposed [private published articles task](../one-shot-v2-expert/HANDOFF-DRAFT.md). Despite its filename, that file is an experimental product brief, separate from this operational handoff. It is still a draft. Specify the visibility matrix and error behavior, validate public and held-out checks against correct and deliberately broken implementations, then give fresh agents the same product request from explicitly selected accepted sources.

Measure correctness, time and tokens, files opened and changed, source delta, and whether a rule acquired one clear owner. Include dependencies and documentation in the maintenance cost. Choose deliberately whether the starting sources are measured originals or repaired references. The [workshop plan](semantic-density-workshop.md) also proposes organizations, workflow evolution and compatibility migrations.

### Framework use that earns its complexity

Explore what each framework can contribute to correct, changeable domain code. The Go track is an especially clear opportunity: the sequential agent removed Huma, and the one-shot uses typed Huma operations only for health and tags, with much hand-written decoding and mostly SQL through Bun. The [Go guide](../results/lanes/go/README.md) records this limitation. A fully typed Huma/Bun reference would answer a question the current builds leave open.

Python offers a useful internal comparison: the sequential app uses more Ninja schemas, auth hooks and Channels groups, while the expert one-shot centralizes edits but owns more decoding and socket plumbing. The measured Clojure one-shot included an unused HoneySQL dependency and a scaffold README. Study whether adopting a framework facility removes duplicated decisions and improves changes under the same contract. Record any rewrite as a new reference or condition, with its own evidence.

### Reliability under bounded resources

The Clojure login failure gives a concrete starting case: admission must bound expensive password work while preserving password-hash cost. Its repaired one-shot does this with a two-permit semaphore. Related questions include atomic login counters, capability revalidation during admission, export snapshot consistency, queue retries and socket sender cleanup.

Use declared fault conditions: concurrent bad logins, slow clients, full output queues, revoked capabilities, transient job failures and process restarts. Existing source reviews identify global room locks and lifecycle risks whose effects have not all been reproduced. Cross-instance presence, room caps and fanout remain a separate proposed experiment; current room registries are scoped to one process. Preserve the distinction between a reproduced failure and a source concern.

### Query cost and agent understanding at larger scale

A bounded SQL statement count can still hide excessive rows, wide projections or an expensive aggregate. Vary page size, catalog size and tag/favorite cardinality; inspect query plans and rows visited alongside throughput. Relate each query to the rule it implements so performance changes can be reviewed for correctness.

For agent understanding, add changes to existing invariants and trace decisions across entry points. The useful goal is correct behavior per unit of code that a fresh agent can find, change and verify. Token counts and the current twelve reader questions capture only part of that goal.

### Models and build protocols as explicit conditions

The user expressed interest in a fresh GPT-6.1 baseline after prompt assessment and project hygiene. The [baseline refresh assessment](baseline-refresh.md) identifies concrete step-5 and step-8 command-contract friction, including duplicated security work and nested development/production checks.

Prepare versioned inputs and a cohort-specific launch configuration before fresh runs. Changing model, prompts and harness together produces a combined new baseline. Isolating the model requires the same frozen inputs for both models; repetitions help expose run variability. Keep sequential and one-shot effort distinct, and give Opus's reviewer or planner role its own identity if it becomes part of an experiment.

I would make the minimum runner changes needed for fresh result roots, explicit settings and clear gate ownership, then use them for a concrete experiment. The existing freeze, verification, artifact and index tools already provide substantial infrastructure.

The [Ruby compiler probe](../results/ruby-compile/roundhouse-spinel-v2026.9.18/README.md) is a lower-priority avenue in my judgment. The pinned Roundhouse release failed strict compatibility, and there is no compiled Conduit throughput result. A future attempt needs product and deployment parity before a speed comparison.

## First useful deliverable

Read the [README](../README.md), [cohort rules](cohorts.md), [refresh assessment](baseline-refresh.md) and [workshop plan](semantic-density-workshop.md), then inspect the source guides for the stacks relevant to your chosen question. Produce one concrete experiment proposal: starting source identities, task, frozen checks, model and reasoning, repetitions, service budget and measurements. The publication and handoff work is complete; the future experiment still needs its scope selected.

For a quick repository check:

```sh
git status --short --branch
python3 tools/cohort_index.py --check
```

To inspect a reviewed app interactively, use `tools/lane_demo.sh clojure one-shot-reference`, `tools/lane_demo.sh python eight-reference` or the other conditions documented in the guides. These require Docker and Node.js and print a link for the shared editor.

Historical source, frozen inputs, failures and measured effort are the evidence base. New repairs and experiments belong in separately identified outputs. In particular, the Rails/Phoenix/Adonis current-reference diagnostic uses two 10-second rounds and two HTTP scenarios; the Go/Python/Clojure full runtime rounds use nine HTTP workloads and socket swarms. Keep those conditions attached to any comparison.
