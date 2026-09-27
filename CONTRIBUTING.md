# Contributing to AgentMVC

AgentMVC compares what AI agents produce in each stack. The most valuable contribution is a new stack, built by an agent through the same steps. Reruns and reviews help too.

## The one rule

**Agents write the code, never people.** Your code in `stacks/<name>/` must be exactly what the agent left after each step. If a step fails, rerun the whole step; don't fix its output by hand. If the harness was at fault, say so in the PR, fix the harness, and rerun.

Keep the spec, the prompts and the checks as they are. The spec lives in `spec/`, the prompts in `steps/`, and the checks in `tools/security/hurl/`. Changing them breaks the comparison for every other stack.

## Add a stack

You'll need Docker, Python 3.9+, and your stack's toolchain. Then:

1. **Describe the stack.**
   - Copy `stacks/rails/stack.json` to `stacks/<name>/stack.json`, and fill it in:
     - `name`, `language`, `description`, `color`;
     - `port`, a free port such as 4104;
     - `agent`, the tool, model and reasoning level you'll use;
     - `code`: the source extensions and the comment prefix of each, plus any lockfiles, generated files and formatter configs to skip;
     - `security`: the lockfile, and a static analyzer if your stack has a mainstream one;
     - `setup`: an optional command that installs dependencies before `bin/check` runs.
   - Write `stacks/<name>/ENVIRONMENT.md` from an existing one. List the toolchain and versions, the generator command, the formatter and linter commands, the port, and what the sandbox allows. The prompts deliberately say nothing about any stack, so this file is the only stack-specific text the agent sees. Keep it to facts.
   - A stack's security analyzer needs a small branch in `tools/security/scan.py`, and only if `brakeman` or `sobelow` doesn't fit.

2. **Run the steps in order:**
   ```bash
   python3 tools/run-step.py <name> 1-build
   tools/check.sh <name> 1-build
   python3 tools/run-step.py <name> 2-add-drafts
   tools/check.sh <name> 2-add-drafts
   python3 tools/run-step.py <name> 3-package
   tools/check.sh <name> 3-package
   tools/bench/run.sh <name> 3-package           # its results are step 4's input
   python3 tools/run-step.py <name> 4-tune
   tools/check.sh <name> 4-tune
   tools/security/scan.sh <name> 4-tune          # its results are step 5's input
   python3 tools/run-step.py <name> 5-harden
   tools/check.sh <name> 5-harden
   tools/security/scan.sh <name> 5-harden
   python3 tools/run-step.py <name> 6-polish
   tools/check.sh <name> 6-polish
   python3 tools/run-step.py <name> 7-add-background-job
   tools/check.sh <name> 7-add-background-job
   ```
   - `run-step.py` builds the agent's working directory and runs the agent: Codex by default, or any other via `AGENT_CMD`. It then copies back only what the agent wrote, the agent's final report, the scrubbed transcript, and a record in `runs.json`.
   - Record each `tools/check.sh` result in the step's `verified` field in `runs.json`.

3. **Read your transcripts before you publish them.**
   - `tools/scrub.py` replaces your home directory, username, hostname and common secret shapes. It also removes unrelated lines from Docker listings, and it refuses to write a file that still contains any of them.
   - It can't know everything private on your machine. Pass `--deny '<regex>'` to `run-step.py` for anything else, such as project names, hosts or accounts, and read the `.md` transcripts yourself.

4. **Measure and report.**
   - Run `python3 tools/report.py`. It measures every stack, redraws the charts, and updates the table in `README.md` and your stack's `README.md`.
   - If you ran benchmarks, say so in the PR. Speed is only comparable within one machine and one session, so benchmark Rails again next to your stack with `tools/bench/run.sh rails 4-tune`, and include both results.

5. **Open a pull request** with `stacks/<name>/`, any `results/` files you produced, and the regenerated `README.md` and charts.
   - Steps 1 and 2 are enough to join the table; all seven complete the picture.
   - In the PR description, say which agent and model you used, and anything that went wrong.

## Other ways to help

- **Another model.**
  - Rerun an existing stack with a different agent or model, in a copy named, for example, `stacks/rails-claude/`.
  - Results from a different model stay separate from the headline comparison, which uses one model for every stack.
  - A second model across all three stacks is the most useful check this project could get.
- **A second reviewer.**
  - Grade the answers in `comprehension/answers/` against the questions without looking at the keys, and open an issue with your grades.
  - Or review whether a stack's code is idiomatic, and file what a practitioner of that stack would change.
- **A new step or lens:**
  - real-time updates;
  - a data migration;
  - an API version change;
  - a dependency upgrade.

  Open an issue with the prompt and how you would check it. A new step has to run on every stack.
- **Tools.** Better measurement, cleaner charts, CI that runs `tools/report.py` on pull requests.

## Style

Keep documents short, neutral and specific. Report what happened, including what went wrong. The [research log](docs/research-log.md) is the model.
