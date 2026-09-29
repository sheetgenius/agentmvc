# Goal

This directory holds a backend implementing the RealWorld ("Conduit") API. It is a pilot for rewriting a much larger product on this stack. AI agents will learn that product by reading its source, so make its rules easy to find and understand. Reach Rails-like simplicity through **this stack's own idioms and libraries**. Keep code clean, terse, and explicit: every line should express a product rule, data shape, or relationship, and each rule should live in one place.

You are working alone and unsupervised. Keep going until a RETURN condition below is met.

# Your task: shared live article editing

The step-7 backend is working. Read `ENVIRONMENT.md` first. Add the feature in `realworld_spec/features/live-editing/live-editing.md`. The small application in `realworld_spec/frontend/` is the **same, frozen, read-only client** that will be used against every implementation. Read it to understand the user flow and wire contract. Do not edit it or add stack-specific behavior to it.

An author creates a revocable article editing link. Anyone with that link can edit the one article from any browser, using revision-checked HTTP saves and a JSON WebSocket subscription. Presence counts connected editors. A room admits 100 authorized connections; the 101st sees Room full and can retry after a slot opens. Remote updates must not discard an unsaved local draft. See the feature spec for exact routes, messages, errors, ordering, and permissions.

# Checks

Keep `bin/check` and `bin/check-production` working. With no arguments, they must run:

- every original and feature Hurl file using `realworld_spec/bin/run-hurl PORT`;
- the shared live-editing protocol and Playwright checks using `realworld_spec/features/live-editing/bin/check PORT`;
- the formatter and linter;
- all 13 existing security checks against the production image.

Each check starts a fresh PostgreSQL, prepares the schema from scratch, boots the app, and stops everything it started. The production image runs the web server and WebSocket endpoint in its single container, with the same environment contract: only `DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT`. No Redis or additional service. Shared frontend and test dependencies may run in the check harness, outside the production app container.

The Hurl, protocol, and browser tests define correct behavior. Never edit, skip, filter, or work around them. The old API and all earlier features must keep passing. A title edit may change the article slug, so the editing link's stable share ID identifies the article throughout its life.

# Boundaries

- Work only inside this directory, apart from your toolchain and package caches. Do not read other stack implementations.
- Do not modify `realworld_spec/`, `.scaffold/`, `security/`, or `perf/`.
- Use your stack's mainstream libraries and conventions. Expose the specified common JSON API and WebSocket messages; implementation details are yours.
- Keep business logic in application code rather than database functions or triggers. No code golf or invented metaprogramming to shorten the result.
- Do not spawn subagents.

# RETURN conditions

1. **DONE:** `bin/check` and `bin/check-production` both exit 0. Then make up to two cleanup passes over the changed code, ending each pass with both checks green. Update this implementation's README and return.
2. **BLOCKED:** the same failure survives three consecutive fixes without a new hypothesis, an environment failure survives two attempts, or completion requires crossing a boundary. Report the exact failure and attempts.
3. **BUDGET:** 50 check runs without both checks green. Report the current state.

# Final report

Use these headings: **Status**, **Gate result**, **Where the feature landed**, **WebSocket and presence design**, **Editing-link permissions**, **Cleanup passes**, **Spec decisions**, **Run counts**, **Friction log**, **Agent-friendliness notes**. Include check exit codes, Hurl and browser/protocol counts, security results, and formatter/linter status.
