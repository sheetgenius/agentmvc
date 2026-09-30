# Experiment v3: a two-instance contract and practitioner briefs

Status: proposal. Nothing here is frozen or has run. It turns the open questions from the completed tracks into one experiment with three parts, in this order:

1. **Harden the topology.** A new contract version requires two app instances on one PostgreSQL.
2. **Test practitioner briefs.** On that contract, run every stack with and without a short brief written by someone who knows the stack.
3. **Hand off to a fresh agent.** Give a product change to fresh agents, starting from the apps built in step 2.

## Why these questions

- **Single-process deployments shape today's numbers.** The current contract lets presence, room caps and login throttles live in process memory. Rails ran one Puma worker and AdonisJS one Node process for that reason, while Phoenix's BEAM used both CPUs inside one process. Throughput comparisons partly measure that topology.
- **Guidance is an uncontrolled variable.** The expert environment files differ in length and structure, from 552 words for Go to 1,170 for AdonisJS, and each mixes toolchain facts with advice. The one IHP run with an expert brief produced typed routes, a policy module and bounded list queries that no unguided IHP run did. Nobody knows yet how large the brief effect is for each stack.
- **Passing the gates is not the same as being changeable.** Supplemental reviews found defects in apps that passed every gate, and the reader questions score near the ceiling. A product change that crosses HTTP, lists, exports, capabilities, sockets and old rows is a sharper test. The hand-off part does that.

## Part 1: contract v3, two instances

The product contract stays the same except for its topology. The draft below becomes `spec/features/multi-instance/` in a new fixture version; it is kept out of `spec/` until then, because `spec/` is hashed into the existing fixtures.

- **Deployment.** The harness starts two app containers built from the same image, one PostgreSQL, and a fixed reverse proxy it supplies. HTTP requests are spread across both instances. Each WebSocket stays on the instance that accepted it.
- **Services.** PostgreSQL only, as before. No Redis or message broker. `LISTEN`/`NOTIFY`, tables and advisory locks are all allowed.
- **Resources.** Each app container gets 1 CPU and 512 MiB, so the app tier keeps the same 2-CPU total as before. Inside its container a stack may run as many processes or threads as it likes. PostgreSQL keeps 2 CPUs and 1 GiB.
- **Invariants that must hold across instances:**
  - presence counts include editors on both instances;
  - the 100-editor cap is exact across instances, including when admissions race;
  - revoking or rotating a link disconnects its sockets on both instances;
  - a save on one instance reaches subscribers on the other with increasing revisions;
  - an export enqueued twice at once is built once;
  - failed-login throttling counts attempts from both instances together.
- **New gate.** The production gate runs every existing suite through the proxy, then cross-instance checks for each invariant above. For example, 60 editors join through one instance and 40 through the other, and the next join on either must be refused.
- **Validation before freezing.** A throwaway reference implementation must pass the new gate. Deliberately broken variants must fail it: process-local presence, a per-instance cap, and revocation that only reaches one instance.
- **Runtime.** The same nine HTTP workloads and the socket fan-out run through the proxy, in one paired session, alternating stack order.

This removes the single-process handicap and doubles as the two-instance incident the earlier [workshop plan](semantic-density-workshop.md) proposed. It adds code to every stack, so v3 results start a new baseline and are never pooled with earlier ones.

## Part 2: practitioner briefs, A/B

The [brief protocol](../briefs/README.md) defines the brief: six fixed sections, at most 500 words of guidance, written by a practitioner and reviewed by a second one, with no application code and every named API verified on the pinned versions. Toolchain facts move into a **neutral environment file** with the same structure for every stack, so the only difference between arms is the brief.

| Arm | Shared prompt | Environment | Brief |
| --- | --- | --- | --- |
| A | v3 prompt | neutral | none |
| B | v3 prompt | neutral | the stack's brief |

- **Stacks, first wave.** Rails, Phoenix, AdonisJS, Go, Python and Clojure. IHP, Servant and Loco follow once their tracks run under the lane runner; IHP also needs its Nix store build scripted.
- **Runs.** Three per arm per stack, launched in a balanced order such as A, B, B, A, A, B, so drift over time affects both arms equally.
- **Model.** `gpt-6.1-sol` at `xhigh` reasoning, recorded per session in a cohort launch configuration. v3 changes the contract anyway, so it is a new baseline either way. For a bridge to history, add one arm-A run per stack on `gpt-6-sol`.
- **Blind review.** Reviewers score framework use and rule ownership without knowing the arm.
- **Held-out checks.** The reviewer probes are public, and a brief could address exactly what they test. Before launch, write a small set of new checks, validate them against a correct app and a deliberately broken one like the other probes, and keep them out of the repository until every run is reviewed. Compare the arms on the held-out checks, and report the public probes beside them.
- **Predictions first.** Record the expected effect per stack before the first launch. Ours: the largest effect for Go and Clojure, where the builds underused their frameworks or had boundary defects, and the smallest for Rails and Phoenix. Briefed apps will be slightly larger but have fewer duplicated rules and bounded queries more often.
- **Analysis.** Per stack, compare the arm medians and show every run. Count an effect only when it exceeds the spread between runs of the same arm. There is no pooled "brief score" across stacks.

Why it matters on its own: the size of each stack's brief effect measures how far the model's defaults are from expert practice in that stack. A small effect means the model already writes the stack well. A large one means expertise is the bottleneck, and the stack's community can supply it.

## Part 3: fresh-agent hand-off

Finalize the [private published articles draft](../one-shot-v2-expert/HANDOFF-DRAFT.md) into a frozen product change. It needs a complete visibility matrix, exact error behavior, a migration that keeps old rows public, and public plus held-out checks validated against correct and deliberately broken implementations.

For each stack, start fresh agents from the median passing app of **each** arm of Part 2. The hand-off agent gets the neutral environment and no brief. This answers a second question directly: are briefed apps easier for the next agent to change?

## Measurements

| Area | What to record |
| --- | --- |
| Correctness | Development and production gates, the new cross-instance checks, the held-out checks, and the public reviewer probes: common HTTP, favorites and shared-edit boundary |
| Code | Owned and whole-backend tokens and lines against the scaffold; tests and project docs separately |
| Rule ownership | For visibility, edit authority, revision checks, share keys and room admission: how many places in the code enforce each rule, scored blind |
| Queries | SQL statements and rows visited per list request, at two catalog sizes and two page sizes |
| Runtime | Nine HTTP workloads and socket fan-out through the proxy, two rounds, one paired session |
| Effort | Wall time, total input processed, uncached input plus output, commands, broker gate actions, and failed builds or checks |
| Hand-off | Time and tokens, files opened and edited, wrong rule-owner guesses, source delta, regressions, and gates |

## Before any launch

1. Write the contract v3 checks, the proxy harness and the held-out checks, and validate them against the reference and broken variants.
2. Split each stack's expert environment into a neutral environment file that follows the [environment template](../briefs/ENVIRONMENT-TEMPLATE.md). Starting from the [brief seeds](../briefs/seeds/), get a practitioner's brief for each stack that passes `tools/brief_check.py`, and have a second practitioner review it.
3. Run Rails, Phoenix and AdonisJS through `tools/lane_run.py` like Go, Python and Clojure, instead of their per-track scripts.
4. Take model, reasoning and CLI settings from a per-cohort launch configuration rather than `stack.json`, as [the baseline refresh](baseline-refresh.md) recommends. Apply its command-contract fixes to the prompt and harness README.
5. Register the v3 series and conditions in the [cohort index](cohorts.md), freeze every input, verify it, and launch in the balanced order.

The first wave is 36 coding sessions: six stacks, two arms, three runs. At 15 to 25 minutes each, that is about 12 hours of coding. With gates, reviewer probes and benchmarks on one shared host, expect one to two days of machine time run one after another.

## Other open directions

These come from the reviews of the completed tracks and are worth their own experiments later:

- **Framework use that earns its complexity.** The Go one-shot used Huma only for health and tags, and a fully typed Huma and Bun reference would show what the framework can carry. Python's sequential app used more Ninja schemas and Channels groups than its one-shot.
- **Reliability under bounded resources.** The Clojure one-shot ran out of heap during concurrent bad logins. Related cases include atomic login counters, capability revalidation during socket admission, export snapshot consistency, queue retries and socket cleanup. Test them under declared fault conditions, and keep a reproduced failure distinct from a source concern.
- **Query cost at scale.** A fixed statement count can hide wide rows or expensive aggregates. Vary catalog and tag cardinality, and inspect query plans alongside throughput.
- **Models as conditions.** Replay archived inputs on a new model to isolate the model, or refresh prompts and harness together for a new baseline. [Comparing conditions](cohorts.md) explains the difference. If another model plans or reviews, give that role its own identity in the cohort index.
- **Longer product evolution.** The [workshop plan](semantic-density-workshop.md) also proposes organizations, workflow changes and compatibility migrations as later product changes.
