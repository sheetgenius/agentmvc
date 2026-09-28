# Measurement boundary

The objective is usable semantic domain density for agent-maintained codebases of more than three million lines. The fixed product contract makes backend source size a comparable proxy for how much code expresses the same domain behavior. Size alone does not establish ease of navigation or safe modification; the reviewer also examines rule ownership, framework use in the running application, and the amount of context a future change would require.

The one-shot comparison measures backend application code added to each untouched framework scaffold. The reviewer reports both nonblank lines and `o200k_base` tokens. The qualitative review checks clear terseness; whether product rules are explicit, local, and easy for an agent to find and change; which domain behavior is supplied by the framework or chosen libraries; and how the language expresses the remaining logic without repetitive plumbing.

- **Owned source:** nonblank, noncomment lines added or changed against `.scaffold/`, including application logic, migrations, dependency manifests, and application configuration.
- **Whole backend:** all nonblank lines in the final application source, including the scaffold and comments.
- **Excluded from both:** `realworld_spec/`, `security/`, `harness/`, the shared frontend, prompt and environment files, tests, lockfiles, generated schema/entities, dependency caches, build output, Markdown, formatter/linter configuration, Dockerfiles, and check scripts.

Agent-written project docs, including `AGENTS.md`, are reported separately in nonblank lines and `o200k_base` tokens added or changed against `.scaffold/`, with a brief review of whether they help a future agent locate and extend domain behavior. Frozen inputs and generated dependency docs are excluded. Docs are not counted as executable backend source or treated as free evidence of code density.

The same per-stack file rules already used by `tools/measure.py` in the exploratory study apply. The reviewer records both counts and any generated-file classification before comparing results; moving product rules into excluded files is outside the contract. Shared editor and harness size and preparation effort are reported separately.

Agent effort runs from prompt delivery through the final response. Record elapsed time, uncached input and output tokens, check attempts, failures, and fixes. Independently rerun the development and production gates after the agent stops. Runtime measurements use the same production topology and direct protocol load for all stacks, with repeated nearby runs and background host load recorded.
