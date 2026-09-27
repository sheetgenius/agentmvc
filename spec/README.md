# The spec

The app every stack builds is the [RealWorld](https://github.com/realworld-apps/realworld) "Conduit" backend, copied unchanged from commit `ebbcdeb8d55b42a3a613c787560498b8ef10003f` (2026-08-26). Its license is in [LICENSE](LICENSE).

- **`api/`:** the OpenAPI contract, and the official Hurl acceptance suite: 13 files, 154 requests.
- **`docs/`:** the prose backend spec.
- **`bin/run-hurl PORT [file ...]`:** runs the suites in Docker against `http://host.docker.internal:PORT`. The files call `{{host}}/api/...`. With no file arguments, it runs `api/hurl/*.hurl` plus every feature suite that's present.

Two features were written for AgentMVC. Each was validated by a throwaway Rails implementation before any agent saw it; the `validation/` diffs are those implementations.
- **[`features/drafts/`](features/drafts/drafts.md):** drafts, publishing and edit conflicts. 2 files, 47 requests. Added in step 2.
- **[`features/exports/`](features/exports/exports.md):** article exports, built in a durable background job. 1 file, 17 requests. Added in step 7.

The agents never see this directory as it is here. Each agent gets `realworld_spec/`, holding the spec and the features that exist at its step; [`tools/workdir.py`](../tools/workdir.py) assembles it.
