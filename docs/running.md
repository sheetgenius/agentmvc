# Running AgentMVC

There are three things you can run, from lightest to heaviest.

## Try a finished app

You need Docker and Node.js 22.12 or newer (or 20.19+ on the 20.x line). Each command builds a backend, starts a fresh PostgreSQL and the shared editor, and prints a link. The `lane_demo.sh` commands run reviewed versions; `demo.sh` runs the original eight-step study's final snapshots. Open it in two tabs to see live editing. Ctrl-C cleans up.

```bash
tools/lane_demo.sh go one-shot-reference
tools/lane_demo.sh python eight-reference
tools/lane_demo.sh clojure one-shot-reference
tools/demo.sh rails            # the original eight-step study's apps: rails, phoenix or loco
```

For `tools/lane_demo.sh`, `DEMO_BACKEND_PORT` and `DEMO_FRONTEND_PORT` change the ports. For `tools/demo.sh`, `DEMO_ORIGIN` sets a reachable origin for sharing across devices.

## Reproduce a published result

Each result page links the source, prompt, checks and benchmark it used, as far as they were published; some early runs have no published source snapshot ([details](cohorts.md#what-is-indexed)). The [compiled Conduit package](../results/ruby-compile/roundhouse-spinel-conduit-pg-20260930/README.md#reproduce) is self-contained: scripts rebuild the patched toolchains from pinned upstream commits, build the image and rerun the unmodified production gate.

Set up once:

```bash
python3 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt   # size measurement and charts
npm ci --prefix frontend                                                     # client packages for live checks
```

Then, for example:

```bash
.venv/bin/python tools/measure.py rails     # code size at every step of the eight-step study
python3 tools/cohort_index.py --check       # confirm the cohort index matches the run records
```

Transcripts and per-request measurements are release downloads, listed in [results](../results/README.md#raw-data-and-transcripts).

## Run a new experiment

You also need a signed-in Codex CLI. Hurl and k6 run in Docker. The runners were built on macOS with OrbStack, so read the [pitfalls](pitfalls.md) before using another Docker runtime.

New work runs through the lane runner. It freezes the inputs, isolates each agent from the rest of the machine, and records independent checks after the agent stops. A new experiment is a new setup with its own result folder: existing fixtures and results are immutable, and the runner refuses to overwrite them.

1. Prepare and preflight the stack's toolchain, scaffold and environment, so the runner has evidence that they work before any agent starts.
2. Freeze the inputs (`tools/lane_run.py freeze STACK`), then launch the measured sessions.
3. Run the independent checks, reviewer probes and runtime measurements, then regenerate the cohort index (`python3 tools/cohort_index.py`) and confirm it with `--check`.

Follow the exact sequence used for [Go and Python](../results/lanes/METHODOLOGY.md#coordinator-commands) or [Clojure](../results/lanes/clojure/METHODOLOGY.md). [tools/README.md](../tools/README.md) maps every tool by job, and the [pitfalls](pitfalls.md) list what went wrong before.
