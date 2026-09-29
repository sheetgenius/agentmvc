# Semantic-domain-density one-shot run

Three fresh, isolated Codex agents built the same full Conduit backend from untouched Rails, Phoenix, and Loco scaffolds. They received one [frozen prompt](frozen-prompt.md), the same read-only product spec, Lit client, browser harness, and acceptance checks, plus a short stack-specific environment guide. The prompt asked for usable domain behavior per source line in a hypothetical agent-maintained system above three million lines, with any useful libraries and concise project docs allowed. All three used `gpt-6-sol` at `xhigh` effort. The [fixture manifest](frozen-fixture-manifest.json) hashes to `3c80961922dadb5f7a41ce27e081e787a5d0cabfc3ae0094588aaeb79c5faa25`; all scored workdirs and the common prompt matched it.

| Stack | Agent time | Uncached input + output | Commands | Independent development / production | Owned backend source | Whole backend | Added project docs |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| [Rails](rails/agent-report.md) | 710.0 s | 150,876 tokens | 80 | pass 25.5 s / pass 25.8 s | 5,454 tokens / 638 lines | 10,475 tokens | 259 tokens / 7 lines |
| [Phoenix](phoenix/agent-report.md) | 845.2 s | 145,244 tokens | 60 | pass 26.8 s / pass 9.9 s | 8,954 tokens / 990 lines | 13,399 tokens | 263 tokens / 8 lines |
| [Loco](loco/agent-report.md) | 1,183.6 s | 243,185 tokens | 76 | pass 125.4 s / pass 14.5 s | 11,437 tokens / 1,240 lines | 21,503 tokens | 325 tokens / 9 lines |

Owned backend source counts noncomment application lines added or changed from the original scaffold. Whole backend counts all nonblank source including the scaffold. The fixed frontend, tests, harness, lockfiles, generated schema, build caches, and Markdown are excluded from backend size; agent-written docs are reported separately. The [measurement rules](frozen-measurement.md), each stack's `size.json`, `docs.json`, and `source-files.json`, and the [domain rule map](domain-map.md) make the boundaries and file contributions reviewable. Phoenix's earlier source-count exclusion error was corrected in this run and in the [first one-shot erratum](../one-shot/errata.md).

The independent development and fresh-database production gates passed all 17 API/feature files, the direct WebSocket protocol check, four browser tests, and all 13 security files for each final app. Rails also passed RuboCop, Phoenix formatting and warnings-as-errors compilation, and Loco formatting and Clippy with warnings denied. The Loco reviewer initially started server-only mode, leaving an export pending; its preserved failed attempt and corrected server-and-worker rerun are in the [failure ledger](failures.md). Each agent's [scrubbed transcript](rails/transcript.md), [Phoenix transcript](phoenix/transcript.md), and [Loco transcript](loco/transcript.md) includes its implementation attempts and fixes; the corresponding `.jsonl` files preserve structured events. `run.json`, gate JSON, and gate logs sit beside each transcript. [Isolation evidence](isolation.md) records the own-workdir write/install probe, denied parent/sibling reads, brokered checks without a Docker socket, fresh homes, and final fixture verification.

## Repeated runtime results

The production images ran two nearby rounds in opposite order with fresh databases, 2 CPU / 1 GiB limits per app and database, nine HTTP scenarios at 16 virtual users, and direct sockets at 10, 100, and 500 subscribers. All 54 HTTP scenario results had zero failed checks; all 18 socket scenarios had zero missing, duplicate, or regressed revisions. The table shows paired round 1 / round 2 values, without hiding variation.

| Finished app | Anonymous list req/s (SQL/req) | Article read req/s | 500-subscriber delivery p95 | Image / cold start |
| --- | --- | --- | --- | --- |
| Rails | 128.2 / 140.4 (25 / 25) | 540.5 / 493.1 | 13.46 / 12.25 ms | 449.8 MB / 1.52–1.46 s |
| Phoenix | 1,049.3 / 1,038.1 (42 / 42) | 5,267.2 / 5,611.1 | 9.98 / 13.83 ms | 1,673.4 MB / 1.53–1.17 s |
| Loco | 608.0 / 605.4 (21 / 21) | 7,513.8 / 7,425.7 | 9.91 / 9.14 ms | 140.6 MB / 0.33–0.44 s |

These are untuned implementations on a shared host. All three article-list paths issue many SQL statements, and Loco's agent identified a list-pagination scaling limit. Host load and per-scenario SQL work are in the [paired summary](runtime/summary.json) and [runtime guide](runtime/README.md). The guide links the underlying per-round result, k6 summary, and 108 losslessly compressed raw point streams; all archives passed `zstd -t`. The common Lit client was outside the measured request path.

## What this run suggests

Rails expressed the contract in the fewest owned backend tokens. Phoenix used 1.64× and Loco 2.10× as many. The lower Rails source count came with framework conventions and short files, but article permissions and revision behavior cross its models and controllers. Phoenix's `Content` context makes a central rule owner easy to identify, while its largest context and API controller hold a substantial share of the code. This Loco app genuinely uses Loco for startup, routes, migrations, and a PostgreSQL-backed worker; its Conduit domain uses bound SQL through SeaORM and dynamic JSON rather than generated entities or strong domain types. Those choices, the project guides, and their change cost matter more than a token ratio alone; the [domain map](domain-map.md) names the evidence.

One agent per stack and a small product cannot answer the three-million-line question. The shared raw WebSocket protocol and single-container gate constrain native framework choices. The prompt also names Rails as the aspiration for domain-rich compression, which may prime agents. The [workshop plan](../../docs/semantic-density-workshop.md) makes the next study a set of fresh-agent product changes, migration, and multi-instance behavior, with rule navigation and safe evolution measured directly. This run is the fixed-client API baseline for that work, not a framework winner.

No repository changes have been pushed or reorganized. The measured source remains in the three `.work/one-shot-semantic-density/` workdirs for local review; this directory contains the locally published evidence and raw measurements. The [eight-step history](../../README.md) remains intact.
