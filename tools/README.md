# Tools

Python 3.9+ with `pip install -r requirements.txt`, and Docker for anything that runs an app. New experiments run through the lane runner; the per-track runners further down reproduce earlier conditions.

## Lane runner: new work

| Tool | What it does |
| --- | --- |
| `lane_run.py` | `freeze STACK`, `prepare STACK PHASE`, `isolation`, `run`, `publish`, `pipeline STACK [--through 8]` and `one-shot STACK`: fresh, isolated, immutable sessions for sequential and one-shot lanes |
| `lane_continue.py` | The same commands with the versioned reviewer publication adapter |
| `lane_oneshot.py` | The TCP-readiness adapter the expert one-shots froze before coding |
| `lane_launch.py` | Waits for shared Docker work before starting a session's measured clock |
| `lane_broker.py` | Session-scoped toolchain and gate service; the agent never gets the Docker socket |
| `lane_check.py --session SESSION ACTION` | Independent `development`, `production`, `benchmark` or `security-scan` for one immutable session |
| `lane_reference.py` | Prepares and publishes an explicitly unscored repair of a measured session |
| `lane_demo.sh STACK VARIANT` | Runs a reviewed app with the shared editor |
| `clojure_lane.py`, `clojure_track_preflight.py` | Clojure's adapter for the lane runner and its toolchain preflight |
| `go_track_preflight.py`, `python_track_preflight.py` | Prove each product-free toolchain in disposable copies before any agent run |

## Review and evidence

| Tool | What it does |
| --- | --- |
| `lane_review.py` | Reviewer-side TCP readiness; measured fixtures stay unchanged |
| `lane_evidence.py`, `clojure_evidence.py` | Reviewer parity, fresh readers and repeated final runtime, kept separate from measured coding |
| `reviewer_common_http_run.py`, `reviewer_common_http_probe.py` | The common HTTP reviewer probe: 21 contract and 3 quality cases |
| `lane_favorites_probe.py` | The 48-case favorite-filter diagnostic |
| `lane_share_review.py`, `lane_share_probe.py` | The shared-edit boundary probe |
| `lane_report.py`, `clojure_report.py` | Render result pages from published evidence only |
| `lane_artifacts.py`, `clojure_artifacts.py`, `archive_raw.py` | Package transcripts and raw streams for a release, with hashes; never upload |

## Records

| Tool | What it does |
| --- | --- |
| `cohort_index.py [--check]` | Builds or checks `results/cohorts.json`, the identity of every recorded session |
| `brief_check.py BRIEF...` | Checks a practitioner brief against the protocol in `briefs/README.md` |
| `measure.py STACK [STEP]` | Code size in tokens and lines, following the stack's `stack.json` |
| `scrub.py EVENTS WORKDIR OUT` | Scrubs an agent transcript before it is shared outside Git |

## Earlier conditions

Each earlier condition has its own runner family. Use them to reproduce that condition exactly, not for new work:

- `one_shot*.py` and `one_shot_host/`: the first one-shot and the semantic-density runs.
- `ihp_candidate*.py`, `ihp_guided.py` and their host folders: the IHP track and its guided diagnostic.
- `servant_v2*.py`, `typescript_v2*.py`: the v2 pilots.
- `rails_expert_v2*.py`, `phoenix_expert_v2*.py`, `typescript_expert*.py`, `v2_expert_*.py`: the matched expert one-shots, their probes and paired benchmarks.
- `shine_*.py`: the framework-native optimization diagnostics.

The original eight-step study uses these:

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

`bench/` and `security/` also hold what the agents receive in steps 4 and 5. That's `bench.sh` and the benchmark, and the 13 checks in `security/hurl/` with their runner.

The step-8 load generator uses 10, 100, and 500 subscribers, with the 500 subscribers spread across five articles to respect the room cap. The backend is one container with PostgreSQL and the original three-variable environment contract. Measurements go to `results/live-editing/`.

For Clojure, use the adapter commands above rather than the historical runner
directly. The [Clojure reproduction sequence](../results/lanes/clojure/METHODOLOGY.md#reproduction-commands)
gives the exact eight-step, one-shot, reviewer, reader and artifact commands.
An existing fixture is immutable; reader keys must be saved before reader launch,
and measured coding must have stopped before runtime measurements or exports.
Artifact packaging requires nine verified coding sessions, two graded readers,
the selected final reviewer verdicts and all 72 measured runtime raw streams.
