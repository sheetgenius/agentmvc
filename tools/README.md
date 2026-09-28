# Tools

Rails, Phoenix and Loco share the `one_shot_*` tools. IHP has matching `ihp_candidate_*` tools because its toolchain runs through Nix. [docs/running.md](../docs/running.md) shows the order to run them in.

| Stage | Rails, Phoenix, Loco | IHP | What it does |
| --- | --- | --- | --- |
| Freeze and prepare | `one_shot.py` | `ihp_candidate.py` | Hash the frozen inputs, preflight the browser runner, and create an agent workspace |
| Isolate | `one_shot_setup.py` | `ihp_candidate.py prepare` | Create a fresh Codex home, using `codex_home.py`, and a broker token |
| Broker | `one_shot_broker.py` | `ihp_candidate_broker.py` | Run only the named checks and a disposable PostgreSQL for a token holder; agents never get the Docker socket |
| Host checks | `one_shot_host/` | `ihp_candidate_host/` | The Docker-backed checks the brokers and the reviewer run |
| Agent session | `one_shot_agent.py` | `ihp_candidate_agent.py` | One measured Codex session, with its effort recorded |
| Independent gates | `one_shot_independent.py` | `ihp_candidate_independent.py` | Rerun the development and fresh-database production gates after the agent stops |
| Publish | `one_shot_publish.py` | `ihp_candidate_publish.py` | Scrub the transcript with `scrub.py`, and record effort and code size in `results/<run>/` |
| Runtime | `one_shot_runtime.py`, `one_shot_live_bench.py`, `one_shot_summarize.py` | `ihp_candidate_runtime.py` | HTTP load with `bench/` and direct WebSocket load with `live-load.mjs`, in two rounds |
| Record | `ledger.py`, `reference.py` | same | Add a ledger row; copy the best app into `stacks/<stack>/reference/` and check its size |

Other tools:

- `measure.py` counts an app's code in `o200k` tokens and lines against its stack's scaffold, using the rules in `stack.json`.
- `ihp_guided.py` runs IHP with a stack brief appended to the baseline prompt. `ihp_guided_host/` holds its production check.
- `ihp_candidate_migration_preflight.py` checks IHP's development launcher with a real, product-free migration.
- `reference-live/server.mjs` is the known-good backend the browser preflight runs against.
- `security/hurl/` holds the 13 security checks, which are frozen inputs.
- `one_shot_demo.sh` serves the shared editor against a reference app, and `live-demo-seed.mjs` seeds it.
- `requirements.txt` lists the Python packages the measurement tools need.
