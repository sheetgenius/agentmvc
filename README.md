# AgentMVC

**How do coding models, languages and frameworks affect the code, effort, correctness and runtime of the same application?**

AgentMVC gives coding agents one product contract and measures what they build in each stack. The product is the [RealWorld](https://github.com/realworld-apps/realworld) "Conduit" backend plus drafts, durable background exports, and live shared editing through a fixed Lit client. Every build passes through the same checks: the API suites, a WebSocket protocol check, browser tests and 13 security checks, rerun independently after the agent stops.

It is also a growing set of working references. Measured builds stay frozen, and later repairs are published beside them with their own labels.

## How to read the results

- **Results belong to a condition.** A condition fixes the model, prompt, stack guidance, scaffold, build protocol and harness. Compare numbers only within one table. The [cohort index](results/cohorts.json) records the identity of every session, and [comparing conditions](docs/cohorts.md) explains the rules.
- **Measured runs and references are different things.** A measured run is one agent session, preserved as it was. A reference is a later, unscored repair of a measured run.
- **One model so far.** Every recorded coding session used `gpt-6-sol` at `xhigh` reasoning through the Codex CLI. Clojure used CLI 0.159.0; everything else used 0.157.1.

| Condition | Protocol | Stacks | Measured runs | What sets it apart |
| --- | --- | --- | ---: | --- |
| [Expert v2, matched session](results/v2-expert-symmetry/README.md) | one-shot | Rails, Phoenix, AdonisJS | 3 | Shared v2 prompt, a frozen expert environment per stack, runtime measured together |
| [Expert v2, lane runner](results/lanes/README.md) | one-shot | Go, Python, Clojure | 3 | Same prompt and approach, run through the lane runner and its adapters, with separate runtime sessions |
| v2 pilots: [Servant](results/one-shot-v2-servant/README.md), [AdonisJS](results/one-shot-v2-typescript/README.md) | one-shot | Servant, AdonisJS | 2 | v2 prompt without expert guidance |
| [Semantic density](results/one-shot-semantic-density/README.md) | one-shot | Rails, Phoenix, Loco | 3 | Earlier prompt that named Rails as its model |
| [IHP track](results/one-shot-ihp/README.md) | one-shot | IHP | 3 | Same prompt as semantic density, on a Nix toolchain |
| [First one-shot](results/one-shot/README.md) | one-shot | Rails, Phoenix, Loco | 3 | Earliest prompt; the Loco agent bypassed Loco |
| [Original eight steps](docs/eight-step-study.md) | sequential | Rails, Phoenix, Loco | 24 | Agents generated their own scaffolds |
| [Prepared lanes](results/lanes/README.md) | sequential | Go, Python, Clojure | 24 | Supplied scaffolds; Clojure on the newer CLI |

Two diagnostics sit outside these conditions: an [IHP run with an expert brief](results/one-shot-ihp/README.md) and a [Ruby compiler feasibility probe](results/ruby-compile/roundhouse-spinel-v2026.9.18/README.md).

## The matched one-shot baseline

One agent per stack received the [same v2 prompt](one-shot-v2-expert/PROMPT.md), contract, client and gates, plus a frozen expert environment for its stack. Speed comes from one paired session in alternating order, with each app and its database limited to 2 CPUs and 1 GiB.

| Stack | Code the agent wrote | Agent time | Article list | SQL per list | Extra contract probes | Runs as | Environment |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Rails 8.1 · Ruby | 6,010 tokens · 644 lines | 14 min | 604–606 req/s | 4 | 20 of 21 | one Puma process | 666 words |
| Phoenix 1.8 · Elixir | 12,145 tokens · 1,359 lines | 20 min | 5,124–5,201 req/s | 4 | 16 of 20 | the BEAM on both CPUs | 740 words |
| AdonisJS 7 · TypeScript | 10,027 tokens · 1,110 lines | 13 min | 3,371–3,438 req/s | 2 | 19 of 21 | one Node process | 1,170 words |

Read it with its limits:
- **One run per stack.** Code size is stable between runs; agent time and speed are not.
- **The topology differs.** The contract keeps presence and room caps in process memory, so Rails and AdonisJS run as a single process while Phoenix uses both CPUs.
- **The guidance differs.** Each environment file mixes toolchain facts with expert advice, in different amounts.
- **The gates aren't the whole story.** All three passed every required gate, and each still missed some [supplemental probes](results/v2-expert-symmetry/README.md) on different edge cases.

[Experiment v3](docs/experiment-v3.md) is designed to remove the topology and guidance differences.

## The other conditions

- **Expert v2 with the lane runner.** Go wrote 12,530 tokens in 16 minutes, Python 8,718 in 12, and Clojure 9,312 in 15. All passed their independent gates. Supplemental review found defects that separately labeled references repair. [Lane results](results/lanes/README.md) · [Clojure](results/lanes/clojure/README.md)
- **Prepared eight-step lanes.** Final sizes were 14,203 tokens for Go, 8,308 for Python and 8,603 for Clojure, after 71, 70 and 83 coding minutes.
- **The original eight-step study.** After eight steps the whole backend, scaffold included, came to 6,259 tokens in Rails, 12,029 in Phoenix and 16,653 in Loco. The [study page](docs/eight-step-study.md) has the full record.
- **Earlier one-shots.** The first prompt and the semantic-density prompt each ran Rails, Phoenix and Loco once, and IHP ran three times on its own track. Their pages record the conditions and review notes.

## Start from working code

These references are repaired, unscored revisions of measured runs. They are good starting points for agents and people, not entries in a ranking.

- **Rails:** [one-shot reference 1](results/one-shot-v2-rails-expert/pilot-1/reference-1/source/). Compact domain code that leans on Rails conventions.
- **Phoenix:** [one-shot reference 2](results/one-shot-v2-phoenix-expert/reference-2/source/). Supervised rooms and PubSub delivery.
- **AdonisJS:** [one-shot reference 1](results/one-shot-v2-typescript-expert/expert-1/reference-1/source/). Raw SQL throughout, so Vine validators and Lucid models are still untried.
- **Go:** [eight-step reference 1](results/lanes/go/8-live-editing/reference-1/source/) and [one-shot reference 1](results/one-shot-v2-go-expert/pilot-1/reference-1/source/). Most request bodies are decoded by hand, so a fully typed Huma and Bun version is still open.
- **Python:** [eight-step reference 1](results/lanes/python/8-live-editing/reference-1/source/) and [one-shot reference 2](results/one-shot-v2-python-expert/pilot-1/reference-2/source/). The eight-step build leans more on Ninja schemas and Channels groups.
- **Clojure:** [eight-step reference 1](results/lanes/clojure/8-live-editing/reference-1/source/) and [one-shot reference 1](results/one-shot-v2-clojure-expert/pilot-1/reference-1/source/). The eight-step build coordinates export and capability transactions explicitly.

Each one-shot reference has an `AGENTS.md` that maps where its product rules live. The eight-step references' maps predate the later steps, so use the [Go](results/lanes/go/README.md), [Python](results/lanes/python/README.md) and [Clojure](results/lanes/clojure/CODE-GUIDE.md) guides instead. Try a reference with `tools/lane_demo.sh go one-shot-reference`. Docker and Node.js are required.

## What the runs suggest so far

- **Framework familiarity and fit mattered more than language.** An early Rust agent that skipped Loco for plain Axum and SQLx finished the fastest full build of its round. In the next round, required to use Loco, the same model took about twice as long. The IHP agents looked up framework APIs several times more often than any other agent.
- **Code size is the most stable measurement.** A stack's size came out within a few percent from run to run and across prompts. Effort and speed did not: IHP's three runs from one prompt varied 1.65× in agent time and from about 1 to 372 article-list requests per second.
- **Passing the gates is not the same as being correct.** Supplemental probes found defects in most measured one-shots. Keep the two verdicts separate.
- **Guidance changes what gets built.** The IHP run with an expert brief produced typed routes, a policy module and bounded list queries that no unguided IHP run did. How much guidance each stack receives is not yet controlled.
- **Speed depends on query shape and topology before language.** Without guidance, first drafts issued a query per article; with expert notes, the matched v2 builds kept article lists to two to four statements. The one-instance contract also keeps Rails and AdonisJS in a single process.

## What's next

- **[Experiment v3](docs/experiment-v3.md)** proposes a two-instance contract, an A/B test of practitioner briefs in six stacks, and a fresh-agent product change starting from the apps it produces.
- **[Practitioner briefs](briefs/README.md)** invite each stack's community to show how they would prompt a model for their stack: six sections, at most 500 words, no product code.
- **[Pitfalls](docs/pitfalls.md)** collect what went wrong in earlier runs, so a new experiment doesn't rediscover it.

## Run it yourself

You need Docker, Node.js, Python 3.9 or newer, and a signed-in Codex CLI for agent sessions. Hurl and k6 run from pinned Docker images. The runners were built on macOS with OrbStack, so read the [pitfalls](docs/pitfalls.md) before using another Docker runtime. Set up once:

```bash
python3 -m venv .venv && .venv/bin/pip install tiktoken matplotlib   # size measurement and charts
npm ci --prefix frontend                                               # client packages for live checks
```

New work runs through the lane runner, which freezes inputs, isolates each agent, and records independent checks:

```bash
.venv/bin/python tools/lane_run.py freeze STACK      # hash a new lane's inputs; an existing fixture is immutable
.venv/bin/python tools/lane_run.py one-shot STACK    # one isolated, measured one-shot session
.venv/bin/python tools/lane_check.py --session SESSION.json production
python3 tools/cohort_index.py --check                # confirm the cohort index matches the records
```

The [lane methodology](results/lanes/METHODOLOGY.md) gives the full sequence, including reviewer probes and references, and [tools/README.md](tools/README.md) maps every tool. Transcripts and raw measurements are release downloads: [Go and Python](https://github.com/sheetgenius/agentmvc/releases/tag/go-python-lanes-v1), [Clojure](https://github.com/sheetgenius/agentmvc/releases/tag/clojure-lane-v1), and the [earlier raw data](https://github.com/sheetgenius/agentmvc/releases/tag/raw-data-v1). Older transcripts and agent reports live in Git history; [`results/message-archive.json`](results/message-archive.json) lists them.

## Repository map

```
spec/                        the product contract: RealWorld spec, Hurl suites and the three added features
frontend/                    the eight-step study's shared editor, and Node packages the harness uses
one-shot/, one-shot-v2*/     frozen prompts, environments and fixtures for each one-shot condition
steps/                       the eight sequential prompts and the comprehension prompt
stacks/<stack>/              stack.json, the product-free scaffold, and each step's code for sequential lanes
briefs/                      the practitioner brief protocol, template and seeds
comprehension/               reader questions, answer keys and grades
results/                     one folder per condition, the cohort index, and the message archive list
docs/                        comparing conditions, pitfalls, the next experiment, and study records
tools/                       runners, independent checks, reviewer probes, measurement and reports
```

## Why this exists

AgentMVC started as R&D at [BitterClip](https://bitterclip.com), a Rails product with about 3 million tokens of application code, more than three times a 1-million-token context window. Its founder, [@ruemic](https://x.com/ruemic), kept hearing that everything should move to Rust because agents would do all the reading and writing. When agents do the reading, what matters is how much of a product fits in their context, so the question became measurable: how much more code does the same product take in another stack, and what does it buy?

## Contribute

Improve a reference, submit a practitioner brief, add a stack, or reproduce a frozen run. Keep measured runs and references labeled separately. [CONTRIBUTING.md](CONTRIBUTING.md) explains the rules.

## License

MIT; see [LICENSE](LICENSE). The RealWorld spec in `spec/` is MIT-licensed by its authors; see [spec/LICENSE](spec/LICENSE).
