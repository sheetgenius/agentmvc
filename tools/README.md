# Tools

Python 3.9+ with `pip install -r requirements.txt`, and Docker for anything that runs an app.

| Tool | What it does |
| --- | --- |
| `measure.py STACK [STEP]` | Code size in tokens and lines, following the stack's `stack.json` |
| `report.py` | Rebuilds `results/sizes.json`, the charts, each stack's README and the README table |
| `workdir.py STACK STEP DEST [--before]` | Recreates an agent's working directory: the code, `.scaffold/`, `ENVIRONMENT.md`, `realworld_spec/`, and `perf/` or `security/` from steps 4 and 5 |
| `run-step.py STACK STEP` | Runs an agent for one step and records the result; see [CONTRIBUTING.md](../CONTRIBUTING.md) |
| `check.sh STACK STEP` | Reruns a step's `bin/check`, and `bin/check-production` if the step has one |
| `bench/run.sh STACK STEP` | Benchmarks a step's production image into `results/speed/` |
| `security/scan.sh STACK STEP` | Scans a step's production image into `results/security/` |
| `scrub.py EVENTS WORKDIR OUT` | Scrubs an agent transcript and renders it as Markdown |

`bench/` and `security/` also hold what the agents receive in steps 4 and 5. That's `bench.sh` and the benchmark, and the 13 checks in `security/hurl/` with their runner.
