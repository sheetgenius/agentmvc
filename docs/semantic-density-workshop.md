# Workshop: agent fit for large application codebases

## The question

> If agents do most of the writing and reading, which language and framework help them build, change, and operate a large, complex application most effectively?

AgentMVC should answer this as a familiar application development question. Rails, Phoenix, and Loco are the first stack packages under study. A result describes the language, framework, libraries, toolchain, model, and task together; it is not a property of a language in isolation.

**Usable semantic domain density** means the amount of correct product behavior and explicit domain invariants expressed per line and source token, while a fresh agent can still locate, change, and verify a rule with bounded context. The agents may use any libraries and write project docs. We report the docs and dependency choices as part of the cost of maintaining the app.

## What the current study establishes

The [eight-step history](../README.md) measures source growth, acceptance, effort, runtime, security, and fresh-reader questions. The [first one-shot run](../results/one-shot/README.md) adds a full-contract build from an untouched scaffold. The [semantic-density run](../results/one-shot-semantic-density/README.md) repeats that build with the large-codebase goal and framework use made explicit.

These are useful measurements of a small, recognizable web app. They cannot by themselves establish fitness at three million lines. The current comprehension questions score near the ceiling in all three stacks. The shared Lit client also fixes a raw WebSocket protocol, which can make a framework's native real-time client harder to use. The single-container production gate measures a useful deployment profile but not a scaled, multi-instance service. Those boundaries should be visible whenever the results are summarized.

The present prompt names Rails as an example of domain-rich compression. That expresses the intended goal but may also prime agents differently across stacks. A later confirmatory prompt should state the principle without naming any candidate framework. Keep the present run as a clearly labeled baseline rather than silently changing its frozen wording.

The workshop audit found a [source-size erratum](../results/one-shot/errata.md): a Phoenix toolchain alias exclusion also hid the real domain directory. Future publications should list every counted and excluded application path and check that known domain owners appear in the counted set before deriving ratios.

The starting scaffolds also differ in what they provide, including Loco's generated agent guidance and authentication code. Preserve authentic scaffolds in the baseline and report those differences. For a later confirmatory run, decide in advance whether the question is about each stack's out-of-box agent experience or each stack with comparable version-matched guidance; those are different comparisons. Record every added library and the behavior it replaces or supplies.

## Next experiment: agent handoffs and product evolution

Keep the current one-shot as the **common API baseline**. After its results are published, run fresh agents through a small number of pre-specified changes. Each change begins from the previous accepted implementation, with a new Codex home and no private context from the builder. All stacks receive the same product-level request and acceptance behavior. The task text may name the existing public product concepts but should not prescribe files or an implementation pattern.

1. **Organizations and roles.** Add workspaces, membership roles, and article visibility rules. Exercise list/feed filtering, direct reads, editing links, exports, and authorization across the existing entrances. This measures whether one policy has a clear owner as the feature crosses domain boundaries.
2. **An evolving workflow.** Add review and scheduled publication, with durable state transitions, cancellation, and an audit trail. Change an existing rule rather than only adding endpoints. This exercises the framework's jobs and persistence conventions and the language's expression of lifecycle invariants.
3. **A compatibility change.** Move an existing permission or revision rule to a new model while preserving previously issued links and old rows through a migration. Test old and new data together. This measures how safely an agent can evolve a live schema and contract.
4. **A two-instance incident.** Start two app instances against the same database, restart one during activity, and check presence, room caps, revocation, and job idempotency. Allow a small, identical service budget when a stack needs an external broker. Report the added operational pieces.

These are proposed phases, not yet frozen fixtures. Before any scored run, write the contract, public and held-out checks, reference behavior, allowed services, stopping rule, and measurement plan. Validate the checks against a reference implementation and deliberate broken variants. A failed phase remains a result; do not silently repair an agent's code before measuring the next phase.

The first phase should have an explicit policy matrix before implementation. At minimum, tests should cover an anonymous visitor, a team viewer, an editor, the article author, and a removed member against list counts, direct article reads, updates, comments, exports, and editing-link creation. Existing personal articles and drafts must remain compatible. A former member must not recover private data through a filtered list or an old export request. The exact semantics of an already issued bearer editing link need a deliberate decision in the contract; leaving that ambiguous would measure agent guesswork instead of stack fitness.

## What to measure at each handoff

| Dimension | Observable result |
| --- | --- |
| Correctness | Public and held-out acceptance, regressions, migration from old data, production boot |
| Agent effort | Completion rate, elapsed time, uncached and total input, output tokens, check attempts, human interventions |
| Navigation | Time to first correct behavior owner, files opened, source tokens read, mistaken owners, search steps |
| Change cost | Files and owned source changed, new source lines/tokens, duplicated rules, test and doc changes |
| Framework and language use | Which behaviors the framework or libraries supply; where custom domain logic lives; use of native idioms in the running app |
| Operations | Build and image size, startup, runtime and SQL work, memory, multi-instance behavior, extra services |
| Agent guidance | Size and usefulness of project docs and whether a fresh agent actually uses them |

Record raw events and gate output. Have reviewers explain any judgment about rule ownership or framework use with file-level evidence. Repeat the highest-value handoff tasks across independent agents; a single run per stack cannot separate a stack effect from agent variance. Publish the distribution rather than only the best run. Keep the current frozen prompt, client, fixture hashes, and historical eight-step results intact.

Separate application failures from environment friction in the failure ledger. The final gate should use its own port so a still-running development server cannot make a correct production image appear broken. The published effort remains the observed effort, with setup costs named rather than silently subtracted.

Report tests, project docs, generated source, dependency manifests, and operational configuration beside the narrower application-source count. Track when an agent has to inspect framework or library code to understand an implicit rule. A short application can still be expensive to evolve if behavior lives behind undocumented defaults; a longer one can be cheap to change if its owner is obvious. The existing comprehension results already include misses caused by behavior hidden in dependencies.

For the current baseline, add a file-level **domain signal map** to the ordinary size count. Locate each behavior named in the contract, identify its canonical owner, and label the surrounding application code as domain decision, transport/persistence adapter, or operational glue. Report concrete examples and ambiguous cases rather than a deceptively precise single percentage. Review framework use at the actual production entry point: routing, data access/migrations, durable jobs, real-time delivery, and authorization. A framework dependency in a manifest does not establish that the running service uses it. Record where native language constructs make the remaining domain rules clearer or more compact.

## Separate framework-native application track

The common API baseline intentionally holds the client fixed. A separate track should specify user-visible browser journeys and accessibility requirements, while letting each agent choose its framework's native UI and real-time path: for example, Rails' [integrated web features](https://guides.rubyonrails.org/v8.0/), Phoenix's [LiveView and Channels](https://phoenix.hexdocs.pm/channels.html), and Loco's [controllers and workers](https://loco.rs/docs/). Count all application-owned client and server source, dependencies, build and deployment steps, and test the same journeys. Do not combine these totals with the fixed-client API results.

## How to present the answer

Publish a profile for each stack: domain source and docs, agent change success and effort, correctness under evolution, runtime and operational cost, and concrete examples of where the framework removed plumbing or where the language clarified a rule. Show cases where the rankings differ. Readers can then apply their own priorities to the question instead of inheriting a single weighted score.

AgentMVC should stay generic. The scenarios are common web-app concerns: users, teams, permissions, lifecycle, jobs, real-time collaboration, data migration, and deployment. BitterClip motivates the scale and task shapes, but its proprietary product rules or code do not become the benchmark fixture.

Do not pad a small app with generated files to claim a three-million-line test. Growth should come from meaningful, connected domains and repeated changes. Until an organically large implementation exists in each stack, describe the evidence as change-cost and navigation proxies, with an explicit limit on extrapolation.

The measurement split draws on two useful research patterns: [RepoBench](https://arxiv.org/abs/2306.03091) separates retrieval of cross-file context from writing code, while [SWE-bench Pro](https://arxiv.org/abs/2509.16941) focuses on longer, multi-file software changes with verified outcomes. AgentMVC adds a controlled, same-product comparison across language and framework stacks. Their reported scores are not directly comparable to ours.
