# Proposed one-shot comparison

The eight-step study is the exploratory record. The next comparison asks a simpler question: **given the complete product contract at once, what backend does one agent build in each stack?** It is a new experiment alongside the step history, with no step-7 starting point and no claim about incremental growth.

The shared inputs and prepared browser harness are implemented in [`one-shot/`](../one-shot/README.md). A narrow localhost check service runs Docker-backed commands for isolated agents without exposing the host Docker socket.

## Identical product input

Each Rails, Phoenix, and Loco agent starts with a fresh, pinned framework scaffold containing no Conduit product code. From the start, it can read the complete [`spec/`](../spec/) suite: RealWorld, drafts, exports, live editing, HTTP/WebSocket checks, and browser acceptance tests, plus the existing [security checks](../tools/security/hurl/). It also receives the same frozen Lit editor, prepared as a versioned copy of the [exploratory client](../frontend/), which exercises shared editing. The other APIs are exercised by the spec suite; the editor stays small. The only stack-specific text is a short `ENVIRONMENT.md` describing the pinned toolchain and idiomatic commands.

The editor, tests, one shared prompt, scaffold revisions, and browser-runner image digest are frozen and hashed before any agent launches. Agents may read them but may not change them or see another stack's implementation. Every agent gets one measured coding session and may iterate inside it until the checks pass or a stated budget is reached.

## Backend contract

Build the complete JSON API and WebSocket endpoint in that stack's idioms. Run as one production application container with PostgreSQL and the existing `DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT` contract. The shared editor is served by the harness. It has no stack-specific branch and contributes no source tokens to any backend.

The new prompt asks agents to imagine this backend inside an agent-maintained codebase exceeding three million lines. They should maximize **usable semantic domain density**: real domain behavior and invariants per line and source token, with small context needed to locate and change a rule. Factor repeated rules, use the assigned framework's conventions and any useful libraries in the actual production application, and use the language's expressive features for logic those tools do not supply. Agents may write project docs that codify rule locations and extension patterns; doc size and usefulness are reported separately. Keep security and concurrency behavior explicit. Code golf, generated hand-written substitutes, and moving product rules into uncounted test or harness files remain outside the contract. A parallel server that bypasses the assigned framework does not meet the design goal.

## Harness-owned verification

The harness prepares the toolchains, package caches, PostgreSQL image, and one pinned browser image before timing starts. It preflights the browser runner from the same sandbox and network topology the agents will use, against a known-good backend. The runner has the exact locked npm package and browser versions, and writes test results to disposable scratch space. No agent installs Chromium or invents a Playwright container wrapper.

The backend exposes a documented build/start interface. The harness runs the same development and production acceptance gates once each: all Hurl files, socket checks, isolated-context Playwright tests, security checks, and the stack's formatter and linter. It independently repeats the final gates after the agent stops. Agent-written check scripts may help development but are not the authority for the published result.

## Measurements and publication

Compare hand-written backend application source in both nonblank lines and `o200k_base` tokens, measured against the untouched scaffold. Also report whole backend source, correctness, agent tokens and wall time, failed checks, and a qualitative review of rule locality, agent navigability, framework use in production, and language expression of logic outside the framework. The fixed contract gives comparable functional scope, while source size remains a proxy rather than a direct measure of maintainability at three million lines. Pre-register which generated schema, entities, lockfiles, dependencies, tests, and harness files are excluded; count migrations, application configuration, and product logic wherever they live. Report shared editor and harness source and preparation effort separately.

After acceptance, run the same HTTP and direct WebSocket workloads against each production image, with the 100-per-article cap respected. Publish raw samples and background host load, repeat close in time, and avoid narrow speed rankings when the host drifts. Preserve the original agent outputs, scrubbed transcripts, prompt and fixture hashes, independent gate results, and every encountered failure.

The historical eight-step results and fixture remain unchanged. The one-shot run can test whether the staged history itself affected final code size; it cannot measure the marginal cost of each feature or establish a growth curve.

## Run status

The versioned client includes the delayed-save regression test, and the exploratory step-8 fixture is unchanged. The pinned browser runner passed its reference preflight; the shared gates passed against the three existing step-8 backends. The prompt, fixture files, host check scripts, and browser image ID were frozen by [`tools/one_shot.py`](../tools/one_shot.py) before any measured session. All three measured sessions, independent development and production gates, and two rounds of HTTP and direct WebSocket measurements are complete. The scrubbed transcripts, raw measurement files, failures, sizes, and review are in [`results/one-shot/`](../results/one-shot/README.md).
