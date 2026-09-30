# Tools

Python 3.9+ with `pip install -r requirements.txt`, and Docker for anything that runs an app.

| Tool | What it does |
| --- | --- |
| `measure.py STACK [STEP]` | Code size in tokens and lines, following the stack's `stack.json` |
| `report.py` | Rebuilds `results/sizes.json`, the charts, each stack's README and the README table |
| `workdir.py STACK STEP DEST [--before]` | Recreates an agent's working directory: the code, `.scaffold/`, `ENVIRONMENT.md`, `realworld_spec/`, and `perf/` or `security/` from steps 4 and 5 |
| `run-step.py STACK STEP` | Runs an agent for one step and records the result; see [CONTRIBUTING.md](../CONTRIBUTING.md) |
| `check.sh STACK STEP` | Reruns a step's `bin/check`, and `bin/check-production` if present; clears its disposable `.work/` checkout and raw agent logs after both pass |
| `bench/run.sh STACK STEP` | Benchmarks a step's production image into `results/speed/` |
| `security/scan.sh STACK STEP` | Scans a step's production image into `results/security/` |
| `scrub.py EVENTS WORKDIR OUT` | Scrubs an agent transcript and renders it as Markdown |
| `live_fixture.py freeze\|verify\|verify-workdir DIR` | Records or checks the frozen step-8 prompt, spec, client and security inputs |
| `demo.sh rails\|phoenix\|loco` | Starts a step-8 production backend, PostgreSQL and the shared editor, then prints a new editing link |
| `live-bench.py` | Runs two interleaved rounds of direct socket load against the three step-8 production images |
| `live-review.mjs BACKEND FRONTEND` | Supplemental reviewer checks outside the frozen agent fixture |
| `clojure_track_preflight.py` | Checks the product-free Clojure foundation in disposable copies before a new condition is frozen |
| `clojure_lane.py freeze\|pipeline\|one-shot clojure` | Clojure adapter for the unchanged lane runner: fixture/image verification, isolated coding, and independent gates; `pipeline` accepts `--through 8` |
| `clojure_lane.py prepare clojure PHASE` | Prepares a Clojure session for `1`–`8` or `one-shot`; `isolation\|run\|publish\|check SESSION` expose its individual stages |
| `clojure_evidence.py` | Clojure common/favorite and shared-boundary review, fresh readers after steps 1 and 6, and repeated final runtime; reviewer work stays separate from measured coding |
| `clojure_artifacts.py inspect\|export-feedback\|export-checks\|package VERSION\|verify VERSION` | Exports and packages complete scrubbed Clojure transcripts/raw streams with hashes, retaining failures; no uploads |

`bench/` and `security/` also hold what the agents receive in steps 4 and 5. That's `bench.sh` and the benchmark, and the 13 checks in `security/hurl/` with their runner.

The step-8 load generator uses 10, 100, and 500 subscribers, with the 500 subscribers spread across five articles to respect the room cap. The backend is one container with PostgreSQL and the original three-variable environment contract. Measurements go to `results/live-editing/`.

For Clojure, use the adapter commands above rather than the historical runner
directly. The [Clojure reproduction sequence](../results/lanes/clojure/METHODOLOGY.md#reproduction-commands)
gives the exact eight-step, one-shot, reviewer, reader and artifact commands.
An existing fixture is immutable; reader keys must be saved before reader launch,
and measured coding must have stopped before runtime measurements or exports.
Artifact packaging requires nine verified coding sessions, two graded readers,
the selected final reviewer verdicts and all 72 measured runtime raw streams.
