# IHP candidate: attempts and resolved failures

The counts below are the measured agents' brokered commands, not the independent review gates. An attempt includes an agent command that failed because of its invocation, a compile error, an acceptance failure, or an environment race. See each run's `check-attempts.json` and scrubbed transcript for the exact chronology and output.

| Action | Run 1 attempts / failed | Run 2 attempts / failed | Run 3 attempts / failed |
| --- | ---: | ---: | ---: |
| `ihp-run` | 115 / 39 | 75 / 8 | 55 / 2 |
| `ihp-build` | 0 / 0 | 10 / 7 | 21 / 14 |
| Database start | 2 / 0 | 2 / 2 | 2 / 1 |
| Full development check | 6 / 4 | 4 / 2 | 3 / 2 |
| Production check | 2 / 1 | 4 / 2 | 3 / 1 |

Run 1 worked through IHP schema parsing and generated ID types, typed SQL and Hasql's stale prepared-statement cache (`SQLSTATE 26000`), JSON validation and signed JWT behavior, and a development server occupying the production port. Its final independent [development](run-1/development.json) and [production](run-1/production.json) gates passed. The [agent report](run-1/agent-report.md) identifies the prepared-statement wrapper and a known token expiry/rotation limit.

Run 2 hit generated job status and schema issues, IHP's parsed JSON request middleware, JWT security cases, and PostgreSQL readiness at production startup. Two disposable database starts failed before recovery. The agent also documented a list implementation that filters and performs per-article lookups. Its final independent [development](run-2/development.json) and [production](run-2/production.json) gates passed; the [agent report](run-2/agent-report.md) records the remaining scaling limit.

Run 3 had repeated release-build failures while resolving generated job status and ID types, then corrected share-edit validation and JWT format. Its first production attempt encountered the development port; stopping that server resolved it. Its final independent [development](run-3/development.json) and [production](run-3/production.json) gates passed. The [agent report](run-3/agent-report.md) maps the implementation; the [runtime results](run-3/runtime/summary.json) expose the list-query cost the acceptance suite did not catch.

The preparation stage is separate from these three scored builds. An earlier 2,359-second partial attempt was stopped when the broker's IHP migration path lacked a required trailing slash. A 306-second research-only isolation probe then found that separate workdirs were insufficient while agents shared a Nix store containing earlier source. Both are preserved as [aborted path preflight](preflight-aborted-run/run.json) and [aborted isolation probe](preflight-isolation-run/run.json), with reasons in [preflight](preflight.json). The fixture was refrozen and three clean, private Nix stores were prepared before the scored agents launched. Those two probes are not counted as full builds.

The guided fourth run has a different frozen prompt and its own `guided/check-attempts.json`; its attempts should be compared as a guided diagnostic, not added to this table as another identical-prompt sample.
