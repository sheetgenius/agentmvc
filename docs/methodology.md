# Methodology

## The question

For the same product, how much code does each stack take when AI agents write it? What does each change cost, and what do you get in return: speed, security, and code that a fresh agent can understand?

## The app

The [RealWorld](https://github.com/realworld-apps/realworld) "Conduit" backend API. The spec is pinned in [`spec/`](../spec/), with its public Hurl acceptance suite (13 files, 154 requests), run unmodified. Two features were specified for AgentMVC:
- [drafts](../spec/features/drafts/drafts.md): 2 files, 47 requests;
- [exports built in a background job](../spec/features/exports/exports.md): 1 file, 17 requests.

Before any agent saw them, each feature was validated by a throwaway Rails implementation that passed its tests. The exports tests were also run against a deliberately slowed job, to prove the polling path works.

## The agents

- **One agent per stack per step:** [Codex CLI](https://github.com/openai/codex) 0.157.1, model `gpt-6-sol`, reasoning `xhigh`.
- **Sandbox:** each agent could write only inside its own directory, plus the stack's package caches. It had network access for packages, and could not spawn subagents.
- **Prompts:** every step's prompt is byte-identical for every stack; its sha256 is in each `runs.json` record.
- **Stack facts:** the only stack-specific text is the stack's `ENVIRONMENT.md`. It gives the toolchain, generator command, formatter, linter, port and sandbox limits, and nothing about style.
- **Blind:** no agent was told that other stacks, other agents or a comparison existed.
- **The goal text:** every prompt asks for code that reads almost like a description of the domain, reaching Rails-like simplicity through each stack's own idioms. No prompt discloses a size metric. The tuning and hardening steps give the agent its benchmark or scan results, because those are the task.
- **Stopping rules:** each prompt defines three outcomes:
  - **DONE:** the checks are green, followed by the cleanup passes the prompt allows (one to three), each ending green;
  - **BLOCKED:** the same failure survives three fix attempts, or an environment failure survives two;
  - **BUDGET:** 50 check runs without a green one.

  Every run in AgentMVC ended DONE.

## The steps

Each step starts from a copy of the previous step's code. [`tools/workdir.py`](../tools/workdir.py) recreates exactly what the agent saw: the code, the untouched generator output in `.scaffold/`, `ENVIRONMENT.md`, the spec with the features that exist at that step, and, from step 4, the benchmark and the security checks. See [`steps/`](../steps/).

## Verification

Each agent wrote its own `bin/check`. The check must start a fresh PostgreSQL, prepare the schema from scratch, boot the app, run every Hurl file, and run the formatter and linter. From step 3, `bin/check-production` runs the same files against the production Docker image. From step 5, it also runs the 13 security checks.

After every run, the reviewer reran both checks independently and recorded the result in the step's `verified` field in `runs.json`. A step counts only if that rerun passes. All 21 did.

## Code size

**The unit:** tokens under the `o200k_base` tokenizer (via `tiktoken`). Lines are reported too.

**Two views:**
- **Whole app:** every non-blank line of the application source, comments included, wherever it came from. This is what an agent reads when it learns the codebase.
- **Owned code:** the non-blank, non-comment lines the agent added or changed, relative to its stack's untouched generator output (`scaffold/`). The same diff against the previous step gives the cost of one step.

**Excluded from both:**
- tests;
- lockfiles;
- dependencies and build output;
- generated schema: `db/schema.rb`, Solid Queue's schema, and SeaORM entities;
- Markdown;
- the check harness: `bin/check*`, compose files and Dockerfiles;
- formatter and linter configuration.

Migrations, dependency manifests and application configuration count. Each stack's rules are in its [`stack.json`](../stacks/rails/stack.json), and [`tools/measure.py`](../tools/measure.py) applies them.

One rule was set before step 7 ran. An agent that copies installer-generated schema into a hand-written migration doesn't own that schema. The Rails agent did exactly that with Solid Queue's schema (149 lines), so that migration counts as generated. The [background-jobs findings](findings/background-jobs.md) report the cost both ways.

## Agent effort

From each agent's event log:
- **Agent tokens:** uncached input tokens plus output tokens. Codex re-sends its cached context on every step, so total input mostly counts steps, not work.
- **Wall-clock time:** from launch to exit.
- **Shell commands:** how many the agent ran.

Uncached input depends on prompt-cache hits. A missed cache on the fixed instructions can add about 10k tokens to a run. That's noise on a 100k-token build, but not on a 20k-token reading task; see [comprehension](findings/comprehension.md).

## Speed

[`tools/bench/bench.py`](../tools/bench/bench.py) runs a production image with only `DATABASE_URL`, `SECRET_KEY_BASE` and `PORT`.
- **Resources:** the app and its PostgreSQL 17 each get their own container, limited to 2 CPUs and 1 GB.
- **Data:** identical, seeded through the public API: 50 users, 500 articles, 500 follows, 1,000 favorites and 1,000 comments.
- **Load:** k6 runs 9 scenarios at 16 virtual users, each with a 3-second warm-up and then 15 seconds of measurement.
- **Recorded:** requests per second, p50, p95 and p99 latency, SQL statements per request (from `pg_stat_statements`), peak memory, image size, cold start and idle memory. Later runs also record the CPU used by unrelated containers on the host.

## Security

[`tools/security/scan.py`](../tools/security/scan.py) runs three kinds of checks against a production image:
- **13 black-box Hurl checks:** 11 core (token forgery, mass assignment, injection, malformed input, wrong types, oversized bodies, unknown routes and login enumeration) and 2 defense in depth (`nosniff`, and login rate limiting);
- **OSV-Scanner** on the lockfile;
- **the stack's mainstream static analyzer** where one exists: Brakeman for Rails, Sobelow for Phoenix.

## Comprehension

After steps 1 and 6, a fresh agent in a read-only sandbox answered [12 questions](../comprehension/questions.md) about each implementation's domain rules, citing the file and function for each. It saw only the application source counted as the whole app. Each answer key was written by reading the code before any answer it grades was opened.

## Transcripts

Every session's event log is published in its stack's `transcripts/`, as raw JSONL and as readable Markdown, after [`tools/scrub.py`](../tools/scrub.py) has processed it:
- paths are rewritten to `/work/app`;
- the host's account name, hostname and temp paths are replaced;
- unrelated lines are removed from Docker listings.

The study's working name was also renamed to `agentmvc`. Nothing else was changed.

## Who did what

The maintainer set the question and the rules. One reviewer, Claude, wrote the feature specs, prompts, security checks, questions, answer keys and tools. The reviewer also reran every check, and wrote down hypotheses for speed, security, comprehension, polish and the background job before those steps ran. The [research log](research-log.md) records the session in time order, including every fault.
