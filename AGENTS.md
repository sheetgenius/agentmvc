**Name the track first: benchmark work and compile-program work follow different operating rules.**

Read `README.md`, then the guidance for the track being changed. State the track in the task or change description. This routing implements the October 31, 2026 two-track decision; the benchmark rules and commit checks below carry forward this repository's `AGENTS.md`.

## Benchmark

Read `docs/pitfalls.md` before running benchmark work. The following rules apply to the benchmark:

- Frozen inputs never change in place. `spec/`, `one-shot*/`, `steps/`, `stacks/*/scaffold/`, `tools/security/hurl/`, host check scripts and fixture manifests belong to recorded conditions. New inputs require a new labelled condition and the runner's `freeze` command. Keep drafts out of `spec/`.
- Measured sources and their records are immutable. Make repairs in a new, unscored reference with `tools/lane_reference.py`.
- Compare within one condition. Put the condition beside every number; distinguish measured runs from references.
- Serialize Docker work through `tools/lane_launch.py` and the shared resource lock. Never benchmark two lanes at once.

## Compile program

Read `docs/program.md` and the selected record's README and reproduction instructions. Compiler changes follow that upstream repository's own instructions and contribution rules. Operational work follows the private ops repository's `AGENTS.md` and `PROTOCOL.md`; benchmark launch rules do not govern that workspace.

Publish a new labelled compile record when the toolchain or inputs change. Preserve earlier records and the measured source. Record pins, patches, app changes, checks and limits. This follows `results/ruby-compile/roundhouse-spinel-conduit-pg-20261030/README.md`.

## Public repository boundary

Keep operational prompts, ledgers, transcripts and agent final messages out of this repository. Retain frozen benchmark prompts and compact evidence records. Package benchmark raw messages through the artifact tools. Never publish credentials or private source. BitterClip (private) appears with counts only. Sources: `results/README.md`; the October 31, 2026 two-track decision.

## Checks before you commit

Run these from this repository, not from an upstream compiler or the ops repository:

```bash
python3 tools/cohort_index.py --check                 # regenerate first after changing run records
python3 -m py_compile tools/*.py                      # tools must run on Python 3.9
.venv/bin/python -m unittest tools.test_scrub
(cd tools && ../.venv/bin/python -m unittest test_clojure_artifacts test_clojure_lane test_brief_check)
python3 tools/brief_check.py briefs/seeds/*.md         # plus changed briefs/<stack>.md
```

`docs/cohorts.md` explains result groups. `docs/experiment-v3.md` describes the next benchmark. `briefs/README.md` covers practitioner briefs. `tools/README.md` maps the tools.
