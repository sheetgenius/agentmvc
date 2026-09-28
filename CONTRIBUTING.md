# Contributing to AgentMVC

AgentMVC tests how a prompt, a stack and a model together shape the app an agent builds. The most useful contributions are better prompts and stack briefs, fixes that make a stack's package fairer, and new stacks. Runs with other models help too.

## Rules that keep results comparable

- **Agents write the code, never people.** A reference app is exactly what an agent left. If a run fails, record the failure and run again; don't repair the output by hand. If the harness was at fault, fix the harness, say so, and rerun.
- **Leave the frozen inputs alone, or version them.** `spec/`, `one-shot/`, `stacks/*/scaffold/`, `tools/security/hurl/`, the host checks and the core run tools are hashed into `one-shot/fixture-manifest.json`. If you change any of them, run `python3 tools/one_shot.py freeze`, say so in your pull request, and treat later runs as a new fixture. IHP adds `ihp-candidate/` and its tools, frozen with `python3 tools/ihp_candidate.py freeze`.
- **Several runs, not one.** Runs from one prompt vary a lot. Submit at least three runs per stack for a prompt or brief, and report every one, failures included.
- **One model per comparison.** Compare prompts on the same model and reasoning setting. Runs with another model are welcome as their own rows.
- **Instructions, not solutions.** A prompt or brief can teach framework conventions, point at APIs and warn about pitfalls. It can't contain application code for this product.
- **No agent sessions in Git.** Transcripts, agent reports, gate logs and raw benchmark data stay out of the repository. The publish tools scrub transcripts; archive the run folder, for example as a GitHub release asset, and record the archive name and checksum in the run's ledger row.

## Submit a stack brief or a prompt

A **stack brief** is framework know-how appended to the baseline prompt for one stack. Put it in `stacks/<stack>/briefs/<name>.md`; [the expert IHP brief](stacks/ihp/briefs/expert.md) shows the level of detail that helped. Today only IHP has a launcher that appends a brief, `tools/ihp_guided.py`. For another stack, open an issue so the launcher can be generalized first.

A **new baseline prompt** replaces `one-shot/PROMPT.md` for every stack, which starts a new fixture. Open an issue first with the prompt and what you expect it to change.

Either way, the pull request should include:

1. The brief or prompt.
2. One ledger row per run, added with `tools/ledger.py add`.
3. An archive link for each run's transcript and logs.
4. A new reference app from `tools/reference.py`, if a run beats the current one under the rule in [results/README.md](results/README.md).

## Improve a stack package

A stack package is `stacks/<stack>/stack.json`, `stacks/<stack>/scaffold/`, `one-shot/environment/<stack>.md` and the build settings the harness uses. Fixes that make a stack's toolchain or production build more representative are welcome: an optimized production build, a faster development loop, a measured worker count. They change the frozen inputs, so re-freeze and rerun the stack before comparing it with older rows.

## Add a stack

1. Copy `stacks/rails/stack.json` to `stacks/<name>/stack.json`. Fill in the port, the agent settings, and the measurement rules: source extensions with their comment prefixes, plus lockfiles, generated files and formatter configs to skip.
2. Put the untouched, product-free generator output in `stacks/<name>/scaffold/`.
3. Write `one-shot/environment/<name>.md`: the toolchain and versions, the port, the formatter and linter commands, and how to run commands in the sandbox. It is the only stack-specific text the agent sees, so keep it to facts.
4. Add the stack to `STACKS` in `tools/one_shot.py` and teach the broker its toolchain if it needs a container, as Phoenix does. A stack with its own toolchain rules can get its own track instead, the way IHP has `ihp-candidate/`. Either way, re-freeze.
5. Run it several times, add the ledger rows, and add the reference app.

## Other ways to help

- **Another model.** Rerun all four stacks on the baseline prompt with another model. It is the most useful check this project could get.
- **A second reviewer.** Each ledger row carries a framework-use verdict from one reviewer. Review a reference app the way a practitioner of that stack would, and open an issue with what you'd change.
- **Handoff experiments.** The [roadmap](docs/roadmap.md) describes fresh agents changing an existing app. That is where typed stacks should show their value, and the tooling doesn't exist yet.
