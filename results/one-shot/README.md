# AgentMVC one-shot results

Three sequential Codex CLI sessions built the full Conduit backend from fresh framework scaffolds. Each received the same [frozen prompt](frozen-prompt.md), shared Lit client, product spec, security checks, and harness. The source fixture hash was `432db079d956436c753c3355cb00a9d6b2501b3e194dc2410b258db58dbe0728`; the prompt hash was `39461187761fb6de81d5ce9fc09812ddb0a4a97deaa1b638df78d1772d33d899`. All three workdirs were prepared again after the Docker broker was added and verified unchanged after the runs. The eight-step files and historical results were untouched.

**Measurement correction:** A Phoenix path filter excluded its real `lib/conduit/` source along with a root toolchain alias. The [erratum](errata.md) preserves the original size record and explains the corrected counts below. Gates, agent effort, and runtime files were unaffected.

Each session used `codex-cli 0.157.1`, `gpt-6-sol` at `xhigh`, a fresh Codex home with memory disabled, `workspace-only` filesystem permissions, no interactive approvals, and access to install dependencies in its own directory. A narrow localhost broker ran named Docker-backed checks without exposing the host Docker socket. The [isolation preflight](isolation/README.md) records successful own-directory writes/dependency installation and denied parent/sibling reads and direct Docker access. The read-only fixtures were checked by hash around broker actions and at the end of every run. They are integrity-verified copies, not an OS-level immutable mount.

## Effort and source size

`o200k_base` owned source counts nonblank, noncomment lines added or changed against the untouched scaffold. Whole source includes the scaffold and comments. Tests, locks, dependency caches, generated schema, Dockerfiles, and shared inputs are excluded by the [frozen measurement boundary](../../one-shot/MEASUREMENT.md). Files that contain product rules, including migrations and application configuration, count. The Solid Queue installer schema copied into Rails is classified as generated; the Phoenix `conduit/` alias is a toolchain workaround, not application code.

| Stack | Agent wall time | Uncached input + output tokens | Commands / nonzero | Owned backend tokens / lines | Whole backend tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| Rails | 15m 18s | 163,288 | 70 / 18 | 5,575 / 631 | 10,518 |
| Phoenix | 19m 26s | 187,046 | 82 / 15 | 8,734 / 948 | 13,093 |
| Loco scaffold | 10m 44s | 135,684 | 40 / 5 | 9,247 / 1,050 | 21,582 |

The nonzero command count includes exploratory commands against missing paths and one deliberately stopped development server. Substantive failures and corrections are in the [failure ledger](failures.md). Full usage, code size, scrubbed transcripts, and each agent's own report are in the [Rails](rails/), [Phoenix](phoenix/), and [Loco](loco/) directories. Final implementation workdirs remain in Rails (local workdir `one-shot/rails`, not published), Phoenix (local workdir `one-shot/phoenix`, not published), and Loco (local workdir `one-shot/loco`, not published) for local review. The transcript is evidence of attempts, not a substitute for the independent results.

## Independent acceptance

After each agent stopped, the orchestrator reran both gates from a fresh PostgreSQL database and different ports. Each gate ran 17 API Hurl files, the direct WebSocket protocol check, four isolated-browser Playwright tests, and 13 security files. Development also ran the stack formatter/linter; production built and ran the final one-container image.

| Stack | Development | Production |
| --- | --- | --- |
| Rails | Pass, 23.2s | Pass, 24.5s |
| Phoenix | Pass, 50.4s | Pass, 27.7s |
| Loco scaffold | Pass, 21.9s | Pass, 96.0s |

The [per-stack logs](rails/development.log) and JSON records contain the exact check output and timings; equivalent files are in each stack directory. The Loco independent development gate started the agent's `conduit-server` binary because that is the implementation the agent built.

## Code review

- **Rails:** Rails controllers and Active Record own the API; Solid Queue stores exports durably, share keys are hashed, and room presence/caps are process local. The list serializer makes repeated per-article lookups, and the socket path holds a thread while waiting for subscription. Login throttling is process local.
- **Phoenix:** Data rules are centralized in `Conduit.Data`, with Phoenix HTTP/socket code, a monitored room GenServer, and Oban exports. Share keys are hashed. Presence and login counters are process local; article rendering also makes per-article queries.
- **Loco scaffold:** The agent wrote a standalone Axum and SQLx server in a 1,037-line `src/bin/server.rs`, with a custom PostgreSQL schema and polling export worker. It passes the acceptance contract, but the running backend does not use Loco's HTTP, migration, or job abstractions. This is a material departure from the prompt's request for stack idioms. Login failures are stored in PostgreSQL; live room state is process local.

In a later, unmeasured [retrospective fork](https://github.com/sheetgenius/agentmvc/blob/8c8999d8ef4c29acacd01a60d4fed1400231143d/results/one-shot/loco/retrospective.md), the Loco agent said it chose Axum/SQLx as the faster path through the full contract, did not attempt a Loco implementation first, and understood that the stack-idioms instruction applied to the production server. That answer is a self-report; the measured transcript independently shows the implementation path.

These are one run per stack, with different starting scaffolds and local toolchain paths. The size figures describe these implementations; they do not establish a general framework ranking.

## Shared preparation

The fixed editor contributes 2,252 tokens across five HTML/JS/CSS source files; its three test files contribute 2,672 tokens. Agent-facing harness code contributes 1,112 tokens, host check scripts 1,548, and Python orchestration/measurement code 10,249, using the same tokenizer on nonblank lines. These are shared costs and are excluded from all backend totals. Preparation wall time was not instrumented, so no time estimate is imputed to an agent. The [isolation record](isolation/README.md) describes the work done before the measured sessions.

## Runtime measurements

Two nearby production-image rounds ran in opposite stack order. Each app and its fresh PostgreSQL database had a two-CPU, 1-GiB limit. HTTP used 16 k6 virtual users, 3 seconds of warmup, then 15 measured seconds per scenario. The direct WebSocket workload used 20 saves at a target of five per second at 10, 100, and 500 subscribers, with no more than 100 in any article. All 54 HTTP scenarios had zero failed checks; all 18 live scenarios had zero missed, duplicate, or regressed revisions. The [method and raw files](runtime/README.md) include 108 losslessly compressed k6 point streams, 54 native summaries, six HTTP result files, and six files of per-save/per-delivery WebSocket samples. The [paired summary](runtime/summary.json) includes throughput, SQL work, memory, image size, and host samples for every scenario.

HTTP p95 latency in milliseconds, round 1 → round 2:

| Scenario | Rails | Phoenix | Loco scaffold |
| --- | ---: | ---: | ---: |
| Anonymous list | 133.93 → 232.35 | 20.35 → 21.53 | 76.30 → 74.40 |
| Signed-in list | 218.72 → 219.37 | 34.72 → 34.68 | 75.52 → 73.43 |
| List by tag | 163.62 → 146.46 | 23.26 → 22.23 | 76.78 → 76.00 |
| Feed | 370.20 → 230.71 | 37.22 → 35.20 | 76.45 → 76.19 |
| Article | 63.53 → 46.74 | 4.88 → 5.07 | 2.78 → 2.72 |
| Comments | 30.37 → 34.05 | 3.47 → 3.09 | 3.58 → 3.24 |
| Tags | 30.14 → 27.53 | 4.18 → 4.03 | 2.37 → 1.87 |
| Favorite toggle | 55.66 → 58.54 | 10.61 → 9.37 | 8.48 → 6.85 |
| Create article | 44.38 → 52.10 | 11.09 → 8.67 | 8.61 → 7.75 |

Direct WebSocket delivery p95 in milliseconds, round 1 → round 2:

| Subscribers | Rails | Phoenix | Loco scaffold |
| --- | ---: | ---: | ---: |
| 10 | 15.64 → 16.08 | 8.97 → 10.62 | 8.28 → 7.98 |
| 100 | 20.80 → 18.55 | 10.29 → 9.92 | 9.46 → 18.55 |
| 500 | 19.92 → 11.89 | 14.22 → 9.29 | 10.21 → 8.31 |

The image sizes were 449.9 MB for Rails, 1,673.9 MB for Phoenix, and 113.4 MB for the Axum implementation in the Loco scaffold. Loco's small runtime image is influenced by bypassing the framework at runtime. List endpoints made repeated per-article queries: round-1 anonymous list used about 25 SQL statements/request in Rails, 42 in Phoenix, and 81 in Loco. Round-2 Rails anonymous-list p95 rose substantially while its feed p95 fell; the host load across HTTP samples ranged from 6.6 to 13.4. The HTTP non-app CPU field also includes the k6 generator, so it is not a pure background measure. These observations support workload-specific discussion, not a narrow general speed ranking.

The shared editor's [status-pill preview patch](editor-status-preview.patch) was applied only to the live demo scratch copy after the frozen runs began. It does not change any measured input or historical client.
