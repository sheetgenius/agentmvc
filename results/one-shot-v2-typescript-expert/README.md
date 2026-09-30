# TypeScript expert-guided diagnostic

This is one measured AdonisJS 7 / TypeScript build under the shared v2 expert prompt. It is a **guided diagnostic**, not a second sample of the unguided TypeScript pilot. The product contract, Lit client, security suite, and acceptance harness were shared with the Phoenix expert track. The additional [environment brief](../../one-shot-v2-typescript-expert/ENVIRONMENT.md) was frozen before the agent began.

| Provenance | SHA-256 |
| --- | --- |
| [Shared prompt](../../one-shot-v2-expert/PROMPT.md) | `8d39c1f7f584ee1c00e5f3056c80d99214a4c0790bf23c22b0ea0f5dccabb943` |
| [TypeScript fixture](../../one-shot-v2-typescript-expert/fixture-manifest.json) | `31947deee0870e654a96a829b2beaa48275ed0caf0fa341e9e15f589c42cdee7` |
| Node toolchain image | `sha256:658eafb6020d341d180dbe8faa1912f88ea746dc8cf5ab3b8c5e254ed5968d70` |

The [product-free preflight](preflight.json) and [Codex isolation probe](isolation.json) passed against that exact fixture. The agent could install dependencies and write inside its own workdir; parent and sibling directories, frozen inputs, and the host Docker socket were unavailable. The broker exposed bounded Docker-backed commands and separate development/worker lifecycles.

## Measured build

The single `gpt-6-sol` xhigh agent finished in **13 min 7 s**, using **148,415 uncached input plus output tokens** and 77 shell commands. Eight commands failed during iteration; one of three agent development-gate attempts failed before it corrected blank-field handling. Its own final development and production attempts passed. See [run metadata](expert-1/run.json), [scrubbed transcript](https://github.com/sheetgenius/agentmvc/blob/8c8999d8ef4c29acacd01a60d4fed1400231143d/results/one-shot-v2-typescript-expert/expert-1/transcript.md), [failure count](expert-1/command-failures.json), and [check attempts](expert-1/check-attempts.json).

The independent reviewer reran the unchanged source: the complete [development](expert-1/development.json) and fresh [production](expert-1/production.json) gates both passed, including HTTP, live socket, browser, and security checks. The captured [source](expert-1/source/), [source hashes](expert-1/source-snapshot.json), and [agent report](https://github.com/sheetgenius/agentmvc/blob/8c8999d8ef4c29acacd01a60d4fed1400231143d/results/one-shot-v2-typescript-expert/expert-1/agent-report.md) are separate from the frozen agent inputs.

The [independent size count](expert-1/size.json) is **10,027 owned backend tokens and 1,110 owned nonblank code lines**; whole backend size is 14,399 tokens and 1,776 lines. The expert classifier includes application startup `.sh` code and excludes linter configuration. It remeasures the immutable unguided pilot as **9,407 tokens / 1,050 lines**; that pilot's original published classifier reported **9,355 / 1,044**. Under one classifier, this expert run is 620 tokens and 60 lines larger. Use the 9,407 crosswalk for that comparison. [Tests](expert-1/tests.json) and [documentation](expert-1/docs.json) are reported separately.

## Repeated production runtime

The reviewer ran [two complete HTTP and WebSocket rounds](expert-1/runtime/summary.json), sequentially, with 16 HTTP virtual users, 3-second warmup and 15-second samples, and 2 CPU / 1 GiB limits on both app and database. The image was **333.7 MB**, and cold starts were **0.91 / 1.05 s**. Anonymous article lists returned **3,532 / 3,535 requests per second** with **two SQL statements per request**; single article reads returned **7,837 / 7,770 requests per second**. At 500 subscribers, delivery p95 was **10.7 / 9.58 ms**, with no missing, duplicate, or regressed revisions in the measured socket rounds. Host load and all other scenarios are in the JSON. The frozen benchmark's `foreign_container_cpu_percent_max` may count its own unnamed k6 load-generator container, so that field does **not** establish unrelated host CPU use. These are measurements under their recorded load, not causal speed rankings across stacks.

All **36 lossless raw HTTP streams** are recorded by the [raw-data manifest](expert-1/raw-data.json) and distributed with the Phoenix expert data in the [`raw-data-v2-expert` release](../raw-data-v2-expert/README.md); `raw-data-v1` remains unchanged.

## Source review and limits

The agent used Adonis routing, middleware, exceptions, migrations, queue, and Ace commands. [Article policy](expert-1/source/app/services/article_policy.ts), [article queries and writes](expert-1/source/app/services/articles.ts), and [share/live services](expert-1/source/app/services/shares.ts) give many rules identifiable owners and keep list query count bounded. The compiled image and fresh database passed production checks.

Read-only review found that the source still parses `Record<string, unknown>` in [inputs](expert-1/source/app/services/inputs.ts), asserts database rows as generic types in [store](expert-1/source/app/services/store.ts), and does not use Vine validators or Lucid model classes. It therefore does not demonstrate the full inferred-input/model path proposed by the brief. Later held-out probes confirmed the login-limit and keyed-edit/revocation races described below.

### Post-run held-out diagnostic

The reviewer used the unchanged measured image and a fresh, disposable database. [Raw probe outcomes](expert-1/held-out.json) and the [probe code](../../tools/typescript_expert_heldout.py) are separate from the frozen gates and did not alter scored source. Both database races were forced by holding the target row until two writes were blocked; the report records that barrier. The source tree SHA-256 matched before and after, and the disposable containers and network were removed.

| Probe | Observed | Expected or concern |
| --- | --- | --- |
| Unequal integer revision `0` or `-1` | `422`, no mutation | Drafts contract says unequal integer returns `409` with current article. |
| Two updates omitting `revision` | `200` and `409`; final revision `2` | Both should apply without an explicit revision precondition. |
| Two share rotations | `201` and `409` uniqueness error; one active link | Concurrent rotations should serialize without exposing a database conflict. |
| Invalid UTF-8 WebSocket frame | Server process exited; health failed | A malformed client frame should close that socket, not the server. |
| Padded nonblank text | Title, description, and body were trimmed | Stored text changes without a caller request; the frozen suite does not assert whitespace preservation. |
| Keyed edit waiting behind share revocation | Returned `200` and changed article revision/body after revocation committed | Revoked capability must return `404` without a write. [Barriered outcome](expert-1/held-out-share-revocation.json). |
| 25 simultaneous bad logins for one email | All 25 returned `401`; the next attempt also returned `401` | First 20 failures should be counted and later attempts limited. The probe confirmed three DB lookups blocked at once. [Burst outcome](expert-1/held-out-login.json). |

These failures do not change the independent gate results. A separate [validated reference improvement pass](expert-1/REFERENCE-NEXT.md) corrected all seven observed failure categories and passed development, production, and targeted held-out checks. It is an unscored maintainer diagnostic, not a continuation of the measured agent run. Its owned source is 519 tokens and 58 lines larger than expert-1 under the same classifier; no reference throughput benchmark was run.

The independent gates cover the frozen contract. A later fresh-agent handoff would test whether the rule map helps evolve a larger app; [the draft handoff](../../one-shot-v2-expert/HANDOFF-DRAFT.md) is not part of this scored run.
