# Rails, Phoenix, and TypeScript: current comparison

**Explore the [Rails](../one-shot-v2-rails-expert/pilot-1/reference-1/source/), [Phoenix](../one-shot-v2-phoenix-expert/reference-2/source/), or [TypeScript](../one-shot-v2-typescript-expert/expert-1/reference-1/source/) reference.** These are readable starting points for agents building Conduit-like applications. They are later, unscored revisions of three measured one-shot builds. The original source, prompt, gates, and measurements remain intact for comparison.

This page compares the three **measured snapshots** from September 2026 and shows what subsequent reference work changed. AgentMVC is a continuing hill climb: future iterations can use better guidance and multiple passes, provided their source and evidence are labeled. A better reference does not retroactively improve its one-shot result.

## At a glance: measured one-shots

| Stack | Agent-owned backend¹ | Agent wall time | Production image | Anonymous list² | SQL/list |
| --- | ---: | ---: | ---: | ---: | ---: |
| Rails 8.1 / Ruby 3.3 | **6,010 tokens / 644 lines** | 13m 42s | 324.0 MB | 604–606 req/s | 4 |
| Phoenix 1.8 / Elixir | 12,145 tokens / 1,359 lines | 20m 03s | **165.7 MB** | **5,124–5,201 req/s** | 4 |
| AdonisJS 7 / TypeScript | 10,027 tokens / 1,110 lines | 13m 07s | 333.7 MB | 3,371–3,438 req/s | **2** |

During their measured sessions, Rails ran 74 shell commands with 15 nonzero exits; Phoenix ran 86 with 13; TypeScript ran 77 with 8. Those counts include normal implementation attempts, not just product failures. The [run records](#evidence-and-limits) also retain model token use, but prompt caching makes it a poor headline score.

All three passed independent full development and fresh-production gates: the RealWorld API plus drafts, exports, live editing, browser tests, and 13 security check files. These are three successful implementations of the same product, with different source and runtime costs. The measured Phoenix image is a compiled BEAM release; the TypeScript image runs compiled JavaScript; Rails runs Ruby with YJIT and precompiled Bootsnap. A separate [Roundhouse + Spinel feasibility round](../ruby-compile/roundhouse-spinel-v2026.9.18/README.md) found compile blockers for this exact Rails source; it produced **no comparable throughput result**.

¹ `o200k_base` tokens and nonblank, noncomment lines added or changed against each product-free scaffold. Backend application code, configuration, migrations, and startup scripts count; tests, generated code, lockfiles, Dockerfiles, project docs, the fixed client, and the harness do not. [Measurement rules](../../one-shot-v2-expert/MEASUREMENT.md) and each size JSON give the boundary. Scaffolds and framework conventions differ, so code size describes these implementations, not an intrinsic language constant.

² Two same-session runs, rounded to whole requests per second, from the immutable measured images. A disposable PostgreSQL 17 database and each app had separate 2-CPU / 1-GiB limits. k6 used 16 virtual users, a 3-second warmup, and 15 seconds per scenario. The run order was Rails → TypeScript → Phoenix → Phoenix → TypeScript → Rails. Every workload round had zero failed checks. [Measurement summary](runtime/summary.json) · [raw-stream validation](runtime/raw-validation.json).

## Read or build the code

| Stack | Current unscored reference | Current owned backend | Frozen measured source | Track environment |
| --- | --- | ---: | --- | --- |
| Rails | [reference-1 source](../one-shot-v2-rails-expert/pilot-1/reference-1/source/) · [notes](../one-shot-v2-rails-expert/pilot-1/reference-1/README.md) | [6,085 tokens / 657 lines](../one-shot-v2-rails-expert/pilot-1/reference-1/size.json) | [pilot-1 source](../one-shot-v2-rails-expert/pilot-1/source/) | [Rails environment](../../one-shot-v2-rails-expert/ENVIRONMENT.md) |
| Phoenix | [reference-2 source](../one-shot-v2-phoenix-expert/reference-2/source/) · [notes](../one-shot-v2-phoenix-expert/reference-2/README.md) | [12,893 tokens / 1,464 lines](../one-shot-v2-phoenix-expert/reference-2/size.json) | [pilot-1 source](../one-shot-v2-phoenix-expert/pilot-1/source/) | [Phoenix environment](../../one-shot-v2-phoenix-expert/ENVIRONMENT.md) |
| TypeScript | [reference-1 source](../one-shot-v2-typescript-expert/expert-1/reference-1/source/) · [notes](../one-shot-v2-typescript-expert/expert-1/REFERENCE-NEXT.md) | [10,546 tokens / 1,168 lines](../one-shot-v2-typescript-expert/expert-1/reference-1/size.json) | [expert-1 source](../one-shot-v2-typescript-expert/expert-1/source/) | [AdonisJS environment](../../one-shot-v2-typescript-expert/ENVIRONMENT.md) |

Each source tree has an `AGENTS.md` map for locating product rules. The references are useful as agent examples, but they are not a reusable package or a guarantee that all contracts hold in a multi-instance deployment. The [shared prompt](../../one-shot-v2-expert/PROMPT.md) states the intended standard: one owner per rule, explicit domain decisions, database invariants, bounded queries, and familiar framework services. The per-stack environment files supply idioms and toolchain details; their guidance was frozen before each measured run.

## Current references: short runtime diagnostic

The three **unscored reference images** were measured in a separate, paired session. It repeats only the anonymous article list and single-article read, with the same seed, app/database limits, 16 users, and alternating stack order as the full measured-snapshot session. Warmup was 2 seconds and measurement 10 seconds per scenario in each of two rounds. Values below are rounded requests per second; every check passed.

| Current reference | Anonymous list | SQL/list | Single article |
| --- | ---: | ---: | ---: |
| Rails reference-1 | 608–618 req/s | 4 | 720–730 req/s |
| Phoenix reference-2 | 5,139–5,183 req/s | 4 | 7,191–7,421 req/s |
| TypeScript reference-1 | 3,517–3,545 req/s | 2.01 | 7,787–7,932 req/s |

[Reference summary](reference-runtime/summary.json) · [Rails rounds](reference-runtime/rails/round1/results.json) / [2](reference-runtime/rails/round2/results.json) · [Phoenix rounds](reference-runtime/phoenix/round1/results.json) / [2](reference-runtime/phoenix/round2/results.json) · [TypeScript rounds](reference-runtime/typescript/round1/results.json) / [2](reference-runtime/typescript/round2/results.json). All **24** warmup and measurement raw streams passed [checksum, decompression, and sensitive-marker validation](reference-runtime/raw-validation.json). [Download the raw archive](https://github.com/sheetgenius/agentmvc/releases/download/raw-data-v2-expert-symmetry/agentmvc-v2-expert-reference-runtime.tar.zst) (SHA-256 `349c9a2eb0f234b8a7de2e5b886fb7f69880ddbd51852a45f7b9a6423502efbb`). This shorter diagnostic is useful for the current code; its rates should not be spliced into the nine-scenario scored session or treated as a causal estimate of each repair's speed.

## Frozen measured snapshots: full production workload

Requests per second, shown as the lower–higher values of the two same-session rounds. Each scenario starts from its defined seed state. The complete per-round JSON also records latency percentiles, SQL statements, memory, host load, and image hashes.

| Request | Rails | Phoenix | TypeScript |
| --- | ---: | ---: | ---: |
| Anonymous article list | 604–606 | **5,124–5,201** | 3,371–3,438 |
| Signed-in article list | 447–457 | **3,701–4,093** | 3,270–3,321 |
| Article list by tag | 562–579 | **5,103–5,370** | 3,203–3,309 |
| Feed | 442–449 | **3,935–4,081** | 2,790–2,807 |
| Single article | 705–719 | 6,459–7,317 | **7,590–7,749** |
| Comments | 902–910 | **11,621–12,435** | 5,148–5,179 |
| Tags | 1,799–1,846 | **8,345–8,611** | 5,561–5,579 |
| Favorite toggle | 590–597 | **3,113–3,308** | 3,042–3,067 |
| Create article | 587–589 | 2,669–3,178 | **3,690–4,015** |

Per-round metrics: [Rails 1](runtime/rails/round1/results.json) / [2](runtime/rails/round2/results.json), [Phoenix 1](runtime/phoenix/round1/results.json) / [2](runtime/phoenix/round2/results.json), [TypeScript 1](runtime/typescript/round1/results.json) / [2](runtime/typescript/round2/results.json). The [benchmark runner](../../tools/v2_expert_symmetry_bench.py) records the workload and seed, and the [validation script](../../tools/v2_expert_symmetry_validate.py) verifies **108** compressed raw k6 streams by checksum and decompression and scans for sensitive markers. [Download the 440-MB raw archive](https://github.com/sheetgenius/agentmvc/releases/download/raw-data-v2-expert-symmetry/agentmvc-v2-expert-symmetry-runtime.tar.zst) (SHA-256 `7f8ecdb6407db5a392dfaa3ec82513a8ed4ffaa0973add54bbe7ee384ba863c5`). The per-run JSON and SHA-256 manifest remain here. Earlier runtime rounds in each track used the same general harness but occurred in different sessions; the table above uses this paired session only.

## Correctness after the frozen gates

The reviewer ran the same additional HTTP diagnostic against each **unchanged measured image** on fresh databases. It is supplemental evidence, not a hidden gate that an agent was expected to anticipate. [Probe code](../../tools/reviewer_common_http_probe.py) · [Docker runner](../../tools/reviewer_common_http_run.py).

| Measured source | Contract probes | Additional quality probes | Observed gaps |
| --- | ---: | ---: | --- |
| [Rails](held-out/rails-scored.json) | 20/21 | 3/3 | Explicit `revision: null` was accepted and changed an article. |
| [Phoenix](held-out/phoenix-scored.json) | 16/20³ | 1/3 | Malformed edit error precedence; huge numeric IDs returned 500; an accepted long title returned 500; concurrent login burst exceeded the intended admission cap. |
| [TypeScript](held-out/typescript-scored.json) | 19/21 | 1/3 | Stale integer revisions `0` and `-1` returned 422 rather than 409; nonblank text was trimmed; concurrent login burst exceeded the cap. |

³ Phoenix reached 20 contract probes because the diagnostic skipped a second long-title-dependent case after its first 500. The denominators differ; this is a defect inventory, not a ranking by percentages. Each run's [source review](../one-shot-v2-rails-expert/pilot-1/SOURCE_REVIEW.md) or track report discusses further source-level risks. See [Phoenix review](../one-shot-v2-phoenix-expert/pilot-1/SOURCE_REVIEW.md) and [TypeScript diagnostic](../one-shot-v2-typescript-expert/README.md).

The three current references pass the full development and fresh-production gates and the common reviewer probe (**21/21 contract and 3/3 quality cases each**). The TypeScript [reference-1](../one-shot-v2-typescript-expert/expert-1/REFERENCE-NEXT.md) also corrects observed WebSocket and share races. Phoenix [reference-1](../one-shot-v2-phoenix-expert/reference-1/README.md) first corrected its HTTP boundary defects; the [current reference](../one-shot-v2-phoenix-expert/reference-2/README.md) adds a concurrent-login reservation. That admission policy may reject valid simultaneous logins once 20 attempts for one email are in flight. The [Rails revision](../one-shot-v2-rails-expert/pilot-1/reference-1/README.md) addresses revision handling and several source-review risks. Their independent records are below. The [short reference diagnostic](#current-references-short-runtime-diagnostic) measures the current images; the nine-scenario production table belongs only to the earlier frozen images.

| Current reference evidence | Development gate | Fresh production gate | Common reviewer probe |
| --- | --- | --- | --- |
| Rails reference-1 | [pass](references/rails-reference-1/development.json) | [pass](references/rails-reference-1/production.json) | [21/21 + 3/3](references/rails-reference-1/common-http.json) |
| Phoenix reference-2 | [pass](references/phoenix-reference-2/development.json) | [pass](references/phoenix-reference-2/production.json) | [21/21 + 3/3](references/phoenix-reference-2/common-http.json) |
| TypeScript reference-1 | [pass](../one-shot-v2-typescript-expert/expert-1/reference-1/development.json) | [pass](../one-shot-v2-typescript-expert/expert-1/reference-1/production.json) | [21/21 + 3/3](held-out/typescript-reference-1.json) |

## Evidence and limits

| Evidence | Rails | Phoenix | TypeScript |
| --- | --- | --- | --- |
| Run record and code count | [run](../one-shot-v2-rails-expert/pilot-1/run.json) · [size](../one-shot-v2-rails-expert/pilot-1/size.json) | [run](../one-shot-v2-phoenix-expert/pilot-1/run.json) · [size](../one-shot-v2-phoenix-expert/pilot-1/size.json) | [run](../one-shot-v2-typescript-expert/expert-1/run.json) · [size](../one-shot-v2-typescript-expert/expert-1/size.json) |
| Independent gates | [dev](../one-shot-v2-rails-expert/pilot-1/development.json) · [production](../one-shot-v2-rails-expert/pilot-1/production.json) | [dev](../one-shot-v2-phoenix-expert/pilot-1/development.json) · [production](../one-shot-v2-phoenix-expert/pilot-1/production.json) | [dev](../one-shot-v2-typescript-expert/expert-1/development.json) · [production](../one-shot-v2-typescript-expert/expert-1/production.json) |
| Failure history | [commands](../one-shot-v2-rails-expert/pilot-1/command-failures.json) · [checks](../one-shot-v2-rails-expert/pilot-1/check-attempts.json) | [commands](../one-shot-v2-phoenix-expert/pilot-1/command-failures.json) · [checks](../one-shot-v2-phoenix-expert/pilot-1/check-attempts.json) | [commands](../one-shot-v2-typescript-expert/expert-1/command-failures.json) · [checks](../one-shot-v2-typescript-expert/expert-1/check-attempts.json) |
| Scrubbed agent session | [Rails release asset](https://github.com/sheetgenius/agentmvc/releases/download/raw-data-v2-expert-symmetry/agentmvc-v2-rails-expert-pilot-1-transcript.tar.zst) (SHA-256 `1f629ffe39a77018dc9dcd0e26c0cc2d877049bffa76b29f945832abf7dab4e1`) | [Phoenix](https://github.com/sheetgenius/agentmvc/blob/8c8999d8ef4c29acacd01a60d4fed1400231143d/results/one-shot-v2-phoenix-expert/pilot-1/transcript.md) | [TypeScript](https://github.com/sheetgenius/agentmvc/blob/8c8999d8ef4c29acacd01a60d4fed1400231143d/results/one-shot-v2-typescript-expert/expert-1/transcript.md) |

The prompt SHA-256 is `8d39c1f7f584ee1c00e5f3056c80d99214a4c0790bf23c22b0ea0f5dccabb943` for all three. [Rails](../one-shot-v2-rails-expert/pilot-1/run.json), [Phoenix](../one-shot-v2-phoenix-expert/pilot-1/run.json), and [TypeScript](../one-shot-v2-typescript-expert/expert-1/run.json) run records give separate fixture hashes, pinned toolchain images, model, and elapsed time. Each agent used `gpt-6-sol` at `xhigh`, with one measured coding session and no sight of sibling source. This controls the brief but does not remove differences in scaffold, framework maturity, model familiarity, or agent choices.

Two more differences shape these numbers. The contract keeps presence, room caps and login throttles in process memory, so Rails ran one Puma worker and TypeScript one Node process, while Phoenix's BEAM used both CPUs inside one process. Each track's frozen environment also mixes toolchain facts with expert advice in different amounts: 666 words for Rails, 740 for Phoenix and 1,170 for TypeScript. [Experiment v3](../../docs/experiment-v3.md) proposes a two-instance contract and a capped, separate brief to remove both differences.

The benchmarks ran sequentially on one Apple-silicon workstation under OrbStack. Alternating order narrows session drift but does not make the rates portable to other hardware or prove why one implementation is faster. These workloads are small and database-backed; high request rates do not by themselves predict a large application's change cost. The current references have not undergone a fresh-agent handoff phase, so the central claim—how safely another agent can evolve the system—remains to be tested. Later iterations may relax the one-shot protocol to find better implementations; keep their provenance, source counts where practical, gates, and paired speed controls visible. [Contribute a revision](../../CONTRIBUTING.md) · [Original eight-step study](../../docs/README.md) · [Other one-shot tracks](../README.md).
