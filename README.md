# AgentMVC

**When coding agents do most of the writing and reading, which language and framework should you build in?**

AgentMVC asks coding agents to build the same small publishing API in different stacks, then measures its correctness, code size, the agents' effort and the app's speed. The API is RealWorld's [Conduit](https://github.com/realworld-apps/realworld), extended with drafts, durable background exports and live shared editing over WebSockets. All the code, checks and measurements are published.

It began at [BitterClip](https://bitterclip.com), a Rails product with about three million tokens of application code. Its founder kept hearing that everything should be rewritten in Rust because agents would do the work. When agents read the code, how much of a product fits in their context matters, so the question became measurable: how much code does the same product take in each stack, and what do you get for it?

## What we've learned so far

**Rails needed the least new code, and was the slowest.** In one matched comparison, one agent per stack built the full app from the same shared prompt, with each stack's own scaffold and guidance. The agent added 6,010 tokens of backend code in Rails, 10,027 in AdonisJS and 12,145 in Phoenix. Counting each framework's generated scaffold too, the backends came to 12.6k, 14.4k and 15.2k tokens. Phoenix and AdonisJS served more requests per second on every workload, though the Rails build ran as a single process. [Comparison](results/v2-expert-symmetry/README.md)

**Passing the tests is not the same as being correct.** All three matched builds passed the required checks: the API suites, WebSocket and browser tests, and 13 security checks. Extra reviewer probes found defects in all three: edits with invalid revisions that changed articles, malformed input that crashed requests, and login limits that broke under concurrent attempts. In a separate track, a Clojure build ran out of memory during a burst of bad logins. [Three-stack review](results/v2-expert-symmetry/README.md) · [Clojure review](results/lanes/clojure/EXPERT-REVIEW.md)

**The same setup can produce wildly different apps.** Three agents with the same model, prompt and framework (Haskell's IHP) all passed every check. Their article lists ran about 21, 64 and 2,081 SQL queries per request, and served roughly 372, 52 and 1 requests per second. [IHP results](results/one-shot-ihp/README.md)

**Compiled Rails ran 2–5× faster while passing the same production checks.** We compiled the Rails app to a native binary with [Roundhouse](https://github.com/rubys/roundhouse) and Matz's [Spinel](https://github.com/matz/spinel). On the same two CPUs, the benchmarked build's per-workload median throughput was 2.0–5.4× that of Rails running two Puma workers ([benchmark](results/ruby-compile/roundhouse-spinel-conduit-pg-20260930/README.md#benchmark)). This is an experiment: it needs a modified copy of the app (+184/−46 lines) and local compiler patches on current upstream heads: 12 to Roundhouse (one repairs a new upstream regression) and none to Spinel. A few documented behavior differences sit outside the checks. The speed figure comes from the v4 benchmark; the v6 rebuild re-checked correctness only. [Write-up and limits](results/ruby-compile/roundhouse-spinel-conduit-pg-20261004/README.md)

## How to read these results

- **It's a small publishing API.** Maintaining a large product with agents is still untested.
- **Most results are one agent run.** In three IHP repeats, code size varied far less than effort and speed.
- **Every number belongs to its setup:** the model, prompt, guidance and benchmark session that produced it. Compare the matched groups each results page identifies, and compare speed only within one benchmark session. [How to read the results](docs/cohorts.md)
- **Original builds stay frozen.** Repairs and improvements are published beside them as reviewed versions, so you can always see what the agent actually produced.
- **One coding model so far.** Every measured build used OpenAI's `gpt-6-sol` through the Codex CLI. Comparing models is a goal, not yet a result.

## Explore the code

The rows from Ruby through Clojure link to reviewed versions, which pass every required check and the extra reviewer probes, or to the compiled variant. Rust and Haskell link to earlier studies. "One session" means the agent built the whole app in a single sitting; "eight steps" means it grew the app feature by feature across eight prompts.

| Language | Framework | Code or results |
| --- | --- | --- |
| Ruby | Rails 8.1 | [one session](results/one-shot-v2-rails-expert/pilot-1/reference-1/source/) |
| Ruby, compiled | Rails via Roundhouse + Spinel | [experimental compile variant](results/ruby-compile/roundhouse-spinel-conduit-pg-20261004/variant/source/) |
| Elixir | Phoenix 1.8 | [one session](results/one-shot-v2-phoenix-expert/reference-2/source/) |
| TypeScript | AdonisJS 7 | [one session](results/one-shot-v2-typescript-expert/expert-1/reference-1/source/) |
| Go | chi + Bun | [one session](results/one-shot-v2-go-expert/pilot-1/reference-1/source/) · [eight steps](results/lanes/go/8-live-editing/reference-1/source/) |
| Python | Django + Ninja | [one session](results/one-shot-v2-python-expert/pilot-1/reference-2/source/) · [eight steps](results/lanes/python/8-live-editing/reference-1/source/) |
| Clojure | Ring + Reitit | [one session](results/one-shot-v2-clojure-expert/pilot-1/reference-1/source/) · [eight steps](results/lanes/clojure/8-live-editing/reference-1/source/) |
| Rust | Loco | [eight-step study](docs/eight-step-study.md) |
| Haskell | IHP, Servant | [IHP builds](results/one-shot-ihp/README.md) · [Servant pilot](results/one-shot-v2-servant/README.md) |

To run one locally with Docker and Node.js, try `tools/lane_demo.sh go one-shot-reference`. It prints a link to the shared editor; open it in two tabs to see live editing.

## Get involved

- **Write a practitioner brief.** Show how you'd guide an agent in your stack, in at most 500 words. The next experiment runs each stack with and without its brief. [Briefs](briefs/README.md)
- **Improve a reviewed version.** Make it clearer, faster or more idiomatic, and show the before and after. [Contributing](CONTRIBUTING.md)
- **Add a stack or reproduce a run.** The runners freeze every input and check every result independently. [Running AgentMVC](docs/running.md)

The next experiment, [v3](docs/experiment-v3.md), is a proposal: a two-instance deployment, practitioner briefs tested in six stacks, and fresh agents asked to change an existing app rather than build a new one.

## Dig deeper

- [All results](results/README.md): every experiment, with its setup, code and measurements
- [Documentation](docs/README.md): how results are read, how the experiments run, and the original study
- [Glossary](docs/glossary.md): the handful of terms the result pages use

MIT licensed; see [LICENSE](LICENSE). The RealWorld spec in `spec/` is MIT-licensed by its authors.
