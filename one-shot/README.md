# One-shot backend experiment

This is a full-product build alongside the exploratory eight-step study. Each agent receives one self-contained directory with a product-free framework scaffold, the complete API and security fixtures, a versioned Lit editor, the fixed browser harness, and the same `PROMPT.md`. The editor is a read-only backend consumer. Rails, Phoenix, and Loco receive separate directories.

The revised run asks each agent to imagine its backend inside an agent-maintained codebase of more than three million lines. The goal is usable semantic domain density: more domain behavior per line and source token, with predictable rule ownership and little context needed for a safe change. The agents may use any useful libraries and write project docs. They should use the assigned framework to the fullest in the production application, then use the language's expressive features for domain logic outside the framework or libraries. The completed first run remains under `.work/one-shot/` and `results/one-shot/`. Set `ONE_SHOT_RUN=one-shot-semantic-density` for fresh workdirs and result paths for this revised run.

## Prepare

From the repository root:

```sh
python3 tools/one_shot.py preflight       # build pinned browser image and run the new editor suite against the reference server
python3 tools/one_shot.py verify-source   # check the frozen input hashes
python3 tools/one_shot.py prepare         # preflight again, then create .work/one-shot/{rails,phoenix,loco}
```

`prepare` refuses to overwrite an existing workspace. Each directory contains `PROMPT.md`, `MEASUREMENT.md`, its stack's `ENVIRONMENT.md`, `realworld_spec/`, `security/`, `harness/`, an untouched `.scaffold/` baseline, and `FIXTURE.json` with copied-file hashes and the browser image ID. The source manifest also hashes all three starting scaffolds, the setup script, and the reference server. The current checkout's exploratory `frontend/` and step-8 fixture remain unchanged. `tools/one_shot.py verify WORKDIR` checks that the read-only inputs stayed unchanged after an agent run.

The image uses the Playwright 1.63.0 browser image and the exact npm dependency lockfile. The browser runner preflights networking, writable test results, the socket protocol suite, and all four browser tests. A backend agent starts its server and runs `harness/check-all.sh PORT`; no browser install or stack-specific browser wrapper is needed. `harness/db.sh` provides a disposable local PostgreSQL for development through the coordinator's check service.

The final gate is `harness/check-production.sh PORT`: it builds the agent's Dockerfile, creates a fresh database, starts one backend container with only the three agreed runtime variables, and runs the same acceptance files. The agent requests that fixed host command through a localhost broker; the independent reviewer invokes the host command directly.

The prepared runner passed its reference-server preflight: direct WebSocket protocol checks and four Playwright tests. The copied `check-all.sh` gate also passed against the existing Rails, Phoenix, and Loco step-8 production backends: all 17 API Hurl files, the socket checks, four browser tests, and all 13 security files. The fresh-database `check-production.sh` gate was exercised against the Rails step-8 backend. These are harness checks, not one-shot backend results.

## Measurement boundary

The prompt asks one agent per stack to build RealWorld plus drafts, exports, and live editing in one measured session, with exemplary care for domain density and clear terseness. The versioned client includes a regression check for a save response arriving after newer typing and a socket update. The full acceptance runner is harness-owned; the independent final gate and backend source line and token counts are recorded outside the agent workdir. Shared client, tests, scaffolds, generated schema, and harness code are reported separately or excluded according to the [contract](../docs/one-shot-contract.md).

This preparation does not alter the historical eight-step measurements.

## Agent isolation before launch

Launch each agent with a fresh Codex home, memories disabled, approval policy `never`, and `workspace-only` permissions rooted at its own directory. The permission profile denies reads of the parent and sibling directories while allowing ordinary toolchain paths and network package installs. Verify these boundaries with a disposable agent before the measured sessions.

`tools/one_shot_broker.py` gives agents only named checks, a disposable database, and for Phoenix a container toolchain mounted to its own workdir. It authenticates a per-stack token, checks frozen hashes around each action, and keeps the Docker socket solely in the orchestrator process. The agent-facing harness scripts call this broker; `tools/one_shot_host/` contains the identical Docker-backed checks for the broker and independent reviewer. A Dockerfile in a backend workspace remains part of the production build input.
