# One-shot contract

**Given the complete product contract at once, what backend does one agent build in each stack?** The shared inputs and the prepared browser harness live in [`one-shot/`](../one-shot/README.md).

## Identical product input

Each agent starts with a fresh, pinned framework scaffold containing no Conduit product code. It can read the complete [`spec/`](../spec/) suite from the start: RealWorld, drafts, exports, live editing, HTTP and WebSocket checks, and browser acceptance tests, plus the [security checks](../tools/security/hurl/). It also receives the same frozen Lit editor, a versioned copy of the [original client](../frontend/). The only stack-specific text is a short `ENVIRONMENT.md` describing the pinned toolchain and idiomatic commands.

The editor, tests, prompt, scaffolds and browser image digest are frozen and hashed before any agent launches. Agents may read them but may not change them or see another stack's implementation. Every agent gets one measured coding session and may iterate inside it until the checks pass or its budget runs out.

## Backend contract

Build the complete JSON API and WebSocket endpoint in the stack's idioms. Run as one production container with PostgreSQL, configured only by `DATABASE_URL`, `SECRET_KEY_BASE` and `PORT`. The harness serves the shared editor, which has no stack-specific code and adds nothing to any backend's size.

The baseline prompt asks agents to imagine the backend inside an agent-maintained codebase of more than three million lines, and to maximize **usable semantic domain density**: domain behavior and invariants per line and token, with little context needed to find and change a rule. The assigned framework must run the production application. Code golf, hand-written substitutes for generated code, and moving product rules into uncounted test or harness files are outside the contract.

## Harness-owned verification

The harness prepares toolchains, package caches, the PostgreSQL image and one pinned browser image before timing starts. It preflights the browser runner against a known-good reference backend from the same sandbox and network setup the agents use. No agent installs a browser or writes its own browser wrapper.

The development and production gates run the same checks: every Hurl file, the socket checks, the isolated-context Playwright tests, the security checks, and the stack's formatter and linter. The host reruns both gates after the agent stops. Checks the agent writes may help it develop, but they are not the authority for a result.

## Measurement

The [measurement rules](../one-shot/MEASUREMENT.md) count hand-written backend source in nonblank lines and `o200k_base` tokens against the untouched scaffold, plus the whole backend. Each run also records correctness, agent tokens and wall time, and a review of rule locality, framework use in production, and how the language expresses logic outside the framework. After acceptance, the same HTTP and direct WebSocket workloads run against each production image, with the 100-editor room cap respected.

Source size is a proxy with comparable functional scope, not a direct measure of maintainability. Generated schema, entities, lockfiles, dependencies, tests and harness files are excluded by rules fixed before the runs; migrations, application configuration and product logic count wherever they live.
