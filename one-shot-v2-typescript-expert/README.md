# TypeScript expert-guided diagnostic

This is a new, labeled condition for AdonisJS 7 and TypeScript. It keeps the
shared v2-expert product prompt, measurement boundary, Conduit contract, fixed
Lit client, security checks, and acceptance harness. Its extra input is the
stack-specific expert brief in `ENVIRONMENT.md`. Do not pool its measurements
with the unguided TypeScript pilot or with the original eight-step study.

The experiment tests whether a fluent AdonisJS and TypeScript implementation
can keep product decisions visible, queries bounded, and code concise without
moving work into untyped records or scattered SQL casts. The brief names useful
framework APIs and measured pilot failure modes, but the coding agent chooses
the final design. Framework calls and inferred types must match the installed
versions and the frozen contract.

The prepared workspace uses the unchanged product-free TypeScript scaffold,
Node.js 24 toolchain, PostgreSQL 17, and port 4107. It gets a fresh Codex home
with memory and subagents off, no interactive approvals, and no host Docker
socket. The broker exposes bounded one-shot tool commands and a separate queue
worker lifecycle. The independent reviewer reruns both complete gates and
reports source size, effort, query counts, and repeated production measurements.

This condition counts application startup `.sh` files as backend code and
excludes `eslint.config.js` as linter configuration. The original pilot
classifier omitted shell files. Reapplying the expert classifier to the
**immutable pilot source** with the same untouched scaffold baseline gives
9,407 owned tokens and 1,050 owned lines, versus its originally published
9,355 tokens and 1,044 lines. This is a measurement crosswalk, not new work
by that agent; future source-size comparisons must use one classifier.

## Preparation after review

From the repository root:

```sh
python3 tools/typescript_expert.py verify-inputs
python3 tools/typescript_expert.py freeze
python3 tools/typescript_expert.py prepare
python3 tools/typescript_expert_preflight.py full
python3 tools/typescript_expert_isolation.py
python3 tools/typescript_expert_broker.py .work/one-shot-v2-typescript-expert-control/token
# In another terminal, after the broker starts:
python3 tools/typescript_expert_agent.py
```

Freeze only after an independent review of this brief and broker. Any later
change to an input requires a new fixture hash and a fresh workspace.
