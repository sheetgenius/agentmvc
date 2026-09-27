# One-shot backend experiment

This is a new full-product build alongside the exploratory eight-step study. Each agent receives one self-contained directory with a product-free framework scaffold, the complete API and security fixtures, a versioned Lit editor, the fixed browser harness, and the same `PROMPT.md`. The editor is a read-only backend consumer. Rails, Phoenix, and Loco receive separate directories.

## Prepare

From the repository root:

```sh
python3 tools/one_shot.py preflight       # build pinned browser image and run the new editor suite against the reference server
python3 tools/one_shot.py verify-source   # check the frozen input hashes
python3 tools/one_shot.py prepare         # preflight again, then create .work/one-shot/{rails,phoenix,loco}
```

`prepare` refuses to overwrite an existing workspace. Each directory contains `PROMPT.md`, `MEASUREMENT.md`, its stack's `ENVIRONMENT.md`, `realworld_spec/`, `security/`, `harness/`, an untouched `.scaffold/` baseline, and `FIXTURE.json` with copied-file hashes and the browser image ID. The source manifest also hashes all three starting scaffolds, the setup script, and the reference server. The current checkout's exploratory `frontend/` and step-8 fixture remain unchanged. `tools/one_shot.py verify WORKDIR` checks that the read-only inputs stayed unchanged after an agent run.

The image uses the Playwright 1.63.0 browser image and the exact npm dependency lockfile. The browser runner preflights networking, writable test results, the socket protocol suite, and all four browser tests. A backend agent starts its server and runs `harness/check-all.sh PORT`; no browser install or stack-specific browser wrapper is needed. `harness/db.sh` provides a disposable local PostgreSQL for development.

The final gate is `harness/check-production.sh PORT`: it builds the agent's Dockerfile, creates a fresh database, starts one backend container with only the three agreed runtime variables, and runs the same acceptance files. The agent and independent reviewer use that fixed command.

The prepared runner passed its reference-server preflight: direct WebSocket protocol checks and four Playwright tests. The copied `check-all.sh` gate also passed against the existing Rails, Phoenix, and Loco step-8 production backends: all 17 API Hurl files, the socket checks, four browser tests, and all 13 security files. The fresh-database `check-production.sh` gate was exercised against the Rails step-8 backend. These are harness checks, not one-shot backend results.

## Measurement boundary

The new prompt asks one agent per stack to build RealWorld plus drafts, exports, and live editing in one measured session. The versioned client includes a regression check for a save response arriving after newer typing and a socket update. The full acceptance runner is harness-owned; the independent final gate and backend source-token count are recorded outside the agent workdir. Shared client, tests, scaffolds, generated schema, and harness code are reported separately or excluded according to the [proposed contract](../docs/one-shot-contract.md).

This preparation does not launch backend agents or alter the historical eight-step measurements.

## Agent isolation before launch

The prepared directories are copies, not a filesystem boundary. A Codex agent launched with ordinary `workspace-write` access can read the parent repository and sibling workspaces. The launch setup must give each agent full write and command freedom inside its own directory, deny reads outside it apart from required toolchain paths, turn off memories, and use a fresh Codex home. It should run with no interactive approvals. Verify parent and sibling reads fail before starting a measured session.

The fixed checks currently call the host Docker daemon. Exposing that daemon to an agent would let it bypass a filesystem read restriction by mounting host paths. Keep Docker-backed browser, database, and production checks under the coordinator's control until a narrow check interface or an isolated Docker daemon is ready. The prepared workspaces are not yet an enforced-isolation launch environment.
