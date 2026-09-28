# AgentMVC

**If agents write and read most of an application, which language and framework help them build and evolve it best?**

AgentMVC gives a coding agent one product contract and one prompt, and has it build the same backend in each stack. The product is the [RealWorld](https://github.com/realworld-apps/realworld) "Conduit" API plus drafts, article exports built in a durable background job, and live shared editing over WebSockets. A fixed harness checks every build the same way, and one measurement counts the code, the agent's effort and the running app's speed.

[TodoMVC](https://todomvc.com) let developers compare frameworks by reading the same app. AgentMVC compares stacks by what agents build in them, and lets anyone test whether a better prompt builds a better app.

## The baseline so far

One model built the whole product from the [baseline prompt](one-shot/PROMPT.md) in four stacks: Codex CLI 0.157.1 running `gpt-6-sol` at `xhigh` reasoning. Every build passed all acceptance and security checks. The build with the least code in each stack is kept as that stack's reference app.

| Stack | Code the agent wrote | Agent time | Single article | Article list |
| --- | ---: | ---: | ---: | ---: |
| [Rails](stacks/rails/), Ruby | 5,454 tokens | 12 min | 517 req/s | 134 req/s |
| [Phoenix](stacks/phoenix/), Elixir | 8,954 tokens, 1.6× | 14 min | 5,439 req/s | 1,044 req/s |
| [Loco](stacks/loco/), Rust | 11,437 tokens, 2.1× | 20 min | 7,470 req/s | 607 req/s |
| [IHP](stacks/ihp/), Haskell | 10,197 tokens, 1.9× | 73 min | 3,976 req/s | 372 req/s |

Code is the backend source the agent added to an untouched framework scaffold, counted in `o200k` tokens. Speed is the mean of two rounds at 16 virtual users, with each app and its database limited to 2 CPUs and 1 GiB. Rails ran one Puma process and IHP an unoptimized single-core build, so both speed figures understate their stacks. IHP ran three times from the same prompt, and its runs varied widely. The [findings](docs/findings.md) explain what the numbers do and don't show, and every run is in the [run ledger](results/runs.jsonl).

## What's already worked out

- **A frozen product contract.** The [spec](spec/), a shared [Lit client](one-shot/frontend/), 17 API test files, a WebSocket protocol check, four browser tests and 13 security checks. Every input is hashed, so each run records exactly what it was given.
- **Isolated agents.** Each agent gets its own workspace and a fresh Codex home with memory off. It never gets the Docker socket. A narrow local broker runs only the named checks and a disposable PostgreSQL for it.
- **Independent gates.** After the agent stops, the host reruns the development gate and a fresh-database production gate.
- **One measurement.** Owned and whole-app code size against the untouched scaffold, agent time and tokens, and HTTP and WebSocket load on the production image.
- **A run ledger and reference apps.** One line per scored run in [results/runs.jsonl](results/runs.jsonl), and the current best app for each stack in `stacks/<stack>/reference/`.
- **Known pitfalls.** [docs/pitfalls.md](docs/pitfalls.md) lists what went wrong in earlier runs and how to avoid it.

## Run an experiment

You need Docker, Python 3, Node, the Codex CLI and each stack's toolchain. [docs/running.md](docs/running.md) walks through a run from start to finish. The core of a Rails run looks like this:

```bash
python3 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt
(cd frontend && npm ci)
export ONE_SHOT_RUN=my-first-run
python3 tools/one_shot.py prepare rails          # frozen inputs, scaffold and browser preflight
python3 tools/one_shot_setup.py rails            # fresh Codex home and broker token
python3 tools/one_shot_broker.py .work/$ONE_SHOT_RUN-control/tokens.json &
python3 tools/one_shot_agent.py rails            # one measured agent session
python3 tools/one_shot_independent.py rails production
```

## Contribute

The most useful contributions are prompts and stack briefs. A stack brief is framework know-how appended to the baseline prompt for one stack, written by someone who knows that stack well. The [expert IHP brief](stacks/ihp/briefs/expert.md) is the first one. It gave IHP typed routes, a separate policy module and database-bound article lists, at the cost of more code and agent time. [CONTRIBUTING.md](CONTRIBUTING.md) explains how to submit a prompt, a brief, a stack fix or a new stack.

## Repository map

```
spec/              the product contract: RealWorld API spec, Hurl suite and the three added features
one-shot/          the frozen experiment inputs: prompt, measurement rules, per-stack environments,
                   the shared Lit client and the agent-facing check harness
stacks/<stack>/    stack.json with measurement rules, the untouched scaffold/, and the reference/ app
ihp-candidate/     IHP's extra frozen inputs: environment and Nix toolchain wrapper
tools/             prepare, isolate, run, check, publish, measure and benchmark; see tools/README.md
results/           the run ledger; run output stays local or goes to an archive
docs/              how to run, pitfalls, findings, the contract and the roadmap
frontend/          Node dependencies for the reference server, the demo and the socket load tools
```

## Caveats

- **One model so far.** The results show what this model writes well in each stack, including how familiar each framework is to it.
- **Few runs.** Rails, Phoenix and Loco ran once on the baseline prompt. Treat gaps under about 2× in effort or speed as noise.
- **A small product.** The backend is 10,000 to 22,000 tokens. That is far too small to show how ratios behave in a codebase a hundred times larger.
- **Later changes are not measured yet.** The claim typed stacks make, safer changes by later agents, needs the handoff experiments in the [roadmap](docs/roadmap.md).

## License

MIT; see [LICENSE](LICENSE). The RealWorld spec in `spec/` is MIT-licensed by its authors; see [spec/LICENSE](spec/LICENSE).
