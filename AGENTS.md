# Working in this repository

AgentMVC measures how coding agents build the same backend in different stacks. Read [README.md](README.md) first, then [docs/pitfalls.md](docs/pitfalls.md) before running anything.

## Rules

- **Frozen inputs never change in place.** `spec/`, the `one-shot*/` folders, `steps/`, `stacks/*/scaffold/`, `tools/security/hurl/`, the host check scripts and every fixture manifest belong to recorded conditions. New inputs make a new, labeled condition, frozen with its runner's `freeze` command. `spec/` is hashed into existing fixtures, so keep drafts out of it.
- **Measured sources and their records are immutable.** Put repairs in a new, unscored reference with `tools/lane_reference.py`.
- **No agent messages in Git.** Transcripts, agent final reports and chat exports stay out; `.gitignore` covers the usual names. Package them for a release with the artifact tools.
- **Compare within one condition.** State the condition next to every number, and label measured runs and references separately.
- **Serialize Docker work.** Benchmarks and gates share one host; `tools/lane_launch.py` waits for the shared resource lock. Never benchmark two lanes at once.

## Checks before you commit

```bash
python3 tools/cohort_index.py --check                 # after changing run records, regenerate without --check first
python3 -m py_compile tools/*.py                      # tools must run on Python 3.9
.venv/bin/python -m unittest tools.test_scrub         # from the repository root
(cd tools && ../.venv/bin/python -m unittest test_clojure_artifacts test_clojure_lane test_brief_check)
python3 tools/brief_check.py briefs/seeds/*.md        # plus any briefs/<stack>.md you changed
```

## Where things are

- Results for each condition live under `results/`, and [docs/cohorts.md](docs/cohorts.md) explains the cohort index.
- [docs/experiment-v3.md](docs/experiment-v3.md) is the next experiment, and [briefs/](briefs/README.md) holds the practitioner brief protocol.
- [tools/README.md](tools/README.md) maps every tool; new work uses the lane runner.
