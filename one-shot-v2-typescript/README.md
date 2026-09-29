# TypeScript safe-evolution pilot

This track uses the exact frozen `one-shot-v2/PROMPT.md`, `one-shot-v2/MEASUREMENT.md`, client, spec, security checks, and harness used by the Servant pilot. Its separate fixture hash adds the TypeScript environment, AdonisJS scaffold, toolchain, and launcher. Do not change the Servant fixture or pool this condition with the original one-shot runs.

The stack is Node.js 24, TypeScript 5.9, AdonisJS 7, Lucid 22, and PostgreSQL 17. The scaffold is product-free. It includes a health route, framework configuration, a database-backed queue, and a compiled production container that applies migrations and runs the queue worker beside the HTTP server. The agent owns the Conduit implementation and may change the scaffold. JWT and raw WebSockets are required protocol extensions because the framework's built-in access tokens are opaque and its native live transport is SSE.

Preflight must prove typecheck, watch-mode edit-to-response, fresh PostgreSQL migration, queue worker startup, and the compiled three-variable production image before freeze. The scored agent receives a fresh Codex home with memory off and no interactive approvals. The coordinator exposes only named Docker-backed commands and fixed checks, without the host Docker socket. An independent reviewer repeats both complete gates and records the same measurements as the Servant pilot.

## Prepare and launch

From the repository root, with Docker and an authenticated Codex CLI:

```sh
python3 tools/typescript_v2.py preflight
python3 tools/typescript_v2.py freeze
python3 tools/typescript_v2.py prepare
python3 tools/typescript_v2_isolation.py
python3 tools/typescript_v2_broker.py .work/one-shot-v2-typescript-control/token
# In another terminal after the broker starts:
python3 tools/typescript_v2_agent.py
```

The workdir and home are created once. `prepare` refuses to overwrite them. Any change to a frozen input requires a new fixture hash and a fresh workdir. The measured source remains in the workdir after the agent stops so the reviewer can rerun the development and fresh-production gates.
