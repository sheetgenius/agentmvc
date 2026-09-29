# Safe evolution pilot

This is a new one-shot condition. The shared prompt asks an agent to build the same complete Conduit backend with clear ownership of product rules and safe future change as its first concern. The first pilot uses Servant, Haskell, and PostgreSQL. Later comparator runs may use the same prompt and frozen client, spec, and harness. Do not pool this pilot with the earlier semantic-density runs or claim a language comparison from one new stack.

The measured agent receives one prepared workspace, a fresh Codex home with memory and subagents disabled, no interactive approvals, and only named Docker-backed commands through a token-scoped coordinator. The agent can edit its application directory and install dependencies, but cannot read the parent repository or sibling workspaces. The Docker socket stays with the coordinator.

`realworld_spec/`, `security/`, `harness/`, the prompt, environment and measurement documents, and `.scaffold/` are hashed read-only inputs. The reviewer repeats the development and fresh-production gates after the agent stops. Seconds-long focused smoke checks are implementation feedback; full gates and repeated runtime measurements are separate final observations.

The eight-step history and the earlier one-shot fixtures remain unchanged. The Servant pilot is reported as its own condition, including setup costs, failures, backend size, agent effort, correctness, runtime, and known limitations.

## Reproduce the pilot

From the repository root, with Docker and a signed-in Codex CLI:

```sh
python3 tools/servant_v2.py preflight
python3 tools/servant_v2.py freeze
python3 tools/servant_v2.py prepare
python3 tools/servant_v2_isolation.py
python3 tools/servant_v2_broker.py .work/one-shot-v2-servant-control/token
# In a second terminal, after the broker is listening:
python3 tools/servant_v2_agent.py
```

`preflight` compiles the product-free scaffold, checks its small production image and the fixed browser harness, and preloads the agent's private Cabal store. `freeze` hashes the exact shared inputs and Servant scaffold. `prepare` refuses to overwrite an existing workspace or Codex home. The broker binds localhost, verifies frozen hashes around every delegated check, and exposes no Docker socket to the agent.

After the measured agent ends, run `python3 tools/servant_v2_independent.py development` and `production`, then `.venv/bin/python tools/servant_v2_publish.py` for token counts and scrubbed transcripts. Run `python3 tools/servant_v2_runtime.py` after both independent gates pass and the host is quiet enough for timing. The `results/one-shot-v2-servant/` page distinguishes preflight setup, the measured run, and independent observations.
