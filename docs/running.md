# Running an experiment

This is the full sequence the recorded runs used, from frozen inputs to a ledger row. Read [pitfalls.md](pitfalls.md) before your first run.

## What you need

- **Docker.** The recorded runs used OrbStack on an Apple-silicon Mac. Hurl, k6, PostgreSQL 17, the Playwright browser, the Elixir toolchain and the IHP Nix toolchain all run from pinned images.
- **Python 3 with a virtualenv.** `python3 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt` installs the tokenizer the measurement tools need.
- **Node.** Run `npm ci` in `frontend/` once. The reference server, the demo and the socket load tools use its packages.
- **The Codex CLI, logged in.** Each measured session gets a fresh, isolated copy of your login; `codex login` creates it.
- **Stack toolchains on the host,** as listed in `one-shot/environment/<stack>.md`: Ruby 3.3.2 through rbenv for Rails, and Cargo 1.95 with the Loco and SeaORM CLIs for Loco. Phoenix and IHP run their toolchains in containers.

## Rails, Phoenix and Loco

`ONE_SHOT_RUN` names the run. Everything the run creates goes under `.work/$ONE_SHOT_RUN*` and `results/$ONE_SHOT_RUN/`, and Git ignores both.

```bash
export ONE_SHOT_RUN=my-run
python3 tools/one_shot.py verify-source                 # inputs match one-shot/fixture-manifest.json
python3 tools/one_shot.py prepare rails phoenix loco    # browser preflight, then one workspace per stack
python3 tools/one_shot_setup.py                         # fresh Codex homes and broker tokens
python3 tools/one_shot_broker.py .work/$ONE_SHOT_RUN-control/tokens.json &   # keep it running
python3 tools/one_shot_agent.py rails                   # one measured session, two hours at most
python3 tools/one_shot.py verify .work/$ONE_SHOT_RUN/rails   # the agent left the frozen inputs alone
python3 tools/one_shot_independent.py rails development
python3 tools/one_shot_independent.py rails production
.venv/bin/python tools/one_shot_publish.py rails        # scrubbed transcript, report, effort and size
```

Repeat the agent, verify, gate and publish steps for Phoenix and Loco. Run the agents one at a time: the broker and the benchmarks share one machine. Then measure the production images of all three stacks together:

```bash
python3 tools/one_shot_runtime.py                       # two rounds in opposite stack order
python3 tools/one_shot_summarize.py                     # validates and indexes the rounds
```

## IHP

IHP has its own track because its toolchain runs through Nix. Each run needs a positive run number, such as 5.

```bash
python3 tools/ihp_candidate.py verify-source            # inputs match ihp-candidate/fixture-manifest.json
python3 tools/ihp_candidate.py preflight
python3 tools/ihp_candidate.py prepare 5                # workspace, fresh Codex home and broker token
python3 tools/ihp_candidate_broker.py 5 .work/one-shot-ihp-5-control/token &
python3 tools/ihp_candidate_agent.py 5
python3 tools/ihp_candidate_independent.py 5 development
python3 tools/ihp_candidate_independent.py 5 production
.venv/bin/python tools/ihp_candidate_publish.py 5
python3 tools/ihp_candidate_runtime.py 5
```

Every run mounts its own Nix store, a Docker volume named `agentmvc-ihp-nix-run<N>`. Create it before `prepare` as a copy of a product-free, prewarmed base store, so no agent can read an earlier run's app out of the store. The base store for the recorded runs was built by hand, and the exact steps weren't recorded. Scripting the base build is on the [roadmap](roadmap.md).

The production image comes from the Nix output `agentmvc-image` in `stacks/ihp/scaffold/flake.nix`. It uses IHP's `unoptimized-prod-server`, which is compiled at `-O0` and runs on one core. Switch it to `optimized-prod-server` with an explicit capability count before comparing IHP's speed; that changes the frozen inputs.

### With a stack brief

`tools/ihp_guided.py` runs IHP with [the expert brief](../stacks/ihp/briefs/expert.md) appended to the baseline prompt. Its commands are `freeze`, `prepare`, `broker`, `agent`, `publish`, `development`, `production` and `runtime`, in that order. It is fixed to run number 4 and its paths today.

## Record the run

Add one ledger row per run, then check whether it becomes a stack's reference app:

```bash
python3 tools/ledger.py add results/my-run/rails --id 2026-10-01-rails-density-1 --stack rails \
  --prompt density --framework yes --runtime results/my-run/runtime/summary.json --note "..."
python3 tools/ledger.py best
.venv/bin/python tools/reference.py rails .work/my-run/rails 2026-10-01-rails-density-1 --replace
```

Choose the framework verdict by reading the production entry point: `yes`, `partial` or `no`, as defined in [results/README.md](../results/README.md). Run `tools/reference.py` only when `best` names your run. It refuses to finish if the copied app's measured size differs from the row.

Then archive the run's output, for example `tar -cf rails-my-run.tar results/my-run/rails`, upload it as a release asset, and put its name and SHA-256 in the row.

## Try an app

`tools/one_shot_demo.sh rails` builds a stack's reference app as a production image, starts PostgreSQL and the shared Lit editor, seeds an article, and prints a link. Pass an app directory as a second argument to serve something else. Press Ctrl-C to remove its containers.

## Frozen wording

`one-shot/README.md` is handed to every agent as `EXPERIMENT.md`, and `spec/README.md` arrives in every workspace with the spec. Both are hashed into the fixture, so they keep their original wording, including references to the earlier eight-step study. That way new runs get the same inputs as the recorded ones.
