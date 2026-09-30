# Servant v2 pilot

This is one measured, agent-built Conduit backend under the new **safe evolution** prompt. It uses GHC 9.12.4, Servant, Hasql, PostgreSQL 17, and the same frozen client, product spec, security checks, and harness as the earlier runs. It is a new prompt condition, so these numbers are not a same-prompt ranking against Rails, Phoenix, Loco, or IHP. The original eight-step and one-shot fixture still verifies at `3c80961922dadb5f7a41ce27e081e787a5d0cabfc3ae0094588aaeb79c5faa25`; this pilot's frozen fixture is `c4dda93c55799387d4617caccc7fa405966f5c8a5fecd51950bfd39e16a2052b`.

## Result

| Measure | Servant pilot |
| --- | ---: |
| Measured agent | `gpt-6-sol`, xhigh, Codex CLI 0.157.1 |
| Wall time | 24 min 8.7 s |
| Uncached input plus output | 190,674 tokens |
| Agent shell commands | 102; 17 failed |
| Agent compilation | 15 `hs-build` attempts; 10 failed |
| Agent full development gate | 4 attempts; 1 failed; final pass after migration fix |
| Agent production gate | 2 attempts; both passed; final pass after migration fix |
| Independently repeated development and production gates | pass, 15.4 s and 15.2 s |
| Owned backend code | 13,253 `o200k_base` tokens; 861 nonblank, noncomment lines |
| Whole backend code | 13,516 tokens; 905 lines |
| Production image | 197.5 MB |
| Cold start | 0.30 s / 0.29 s |

The independent gates each passed 17 API files (237 requests), 13 security files (52 requests), the live socket protocol, and four browser tests. The agent's focused HTTP transition test, Fourmolu, and HLint also passed. The independently measured source counts differ from the agent's self-reported counts; use [size.json](pilot-1/size.json) as the consistent scaffold-relative measure. The agent-written test is [measured separately](pilot-1/tests.json) at 77 lines and 690 tokens.

The product-free scaffold compiled and served from its production image before the agent began. A trivial source edit reached the watched server in 2.22 seconds. Dependency and permission setup failures were resolved before the frozen measured run; they are listed in [preflight.json](preflight.json), not charged to agent effort. A disposable Codex probe verified own-workspace writes, denied reads of the parent and sibling, denied both host Docker socket paths, and access to the token-scoped localhost Docker check broker. The agent's fresh home had memory and subagents off and approvals set to never. The 7.15 GB toolchain image is a prewarm builder; the delivered production image is 197.5 MB.

## Repeated runtime measurements

Each HTTP round used 16 virtual users, 3 seconds of warmup, then 15 seconds of measurement per scenario. The app and database each had 2 CPU and 1 GiB limits. All reported HTTP checks passed. Statements are PostgreSQL `pg_stat_statements` calls per measured request.

| Scenario | Requests/s, rounds 1 / 2 | p95 ms, rounds 1 / 2 | SQL statements/request |
| --- | ---: | ---: | ---: |
| Anonymous article list | 560.9 / 569.9 | 33.39 / 33.34 | 1.01 |
| Signed-in article list | 530.9 / 537.7 | 37.06 / 35.17 | 2.01 |
| Tag-filtered list | 604.5 / 605.6 | 31.45 / 32.19 | 1.01 |
| Feed | 536.0 / 532.2 | 35.27 / 35.71 | 3.01 |
| Single article | 3,411.9 / 3,376.0 | 6.87 / 6.97 | 2.00 |
| Comments | 3,112.3 / 3,107.7 | 7.15 / 7.32 | 2.00 |
| Tags | 4,197.8 / 4,199.1 | 5.18 / 5.06 | 1.00 |
| Favorite toggle | 627.5 / 592.1 | 32.34 / 33.79 | 4.01 |
| Article creation | 632.9 / 637.5 | 30.74 / 30.29 | 2.01 |

WebSocket broadcasts to 10, 100, and 500 subscribers delivered without missing, duplicate, or regressed revisions in both rounds. Their p95 delivery latencies were **8.58 / 8.14 ms**, **9.75 / 9.80 ms**, and **12.58 / 10.03 ms**, respectively. Room admission is held in one process; these results do not establish multi-instance presence or revocation behavior.

The host was not isolated: recorded one-minute load was 5.1–6.5 during HTTP scenarios, and unrelated containers reached 47–118% of one CPU. Treat absolute speed and cross-session comparisons as load-qualified. The two same-image rounds show the variation under this session's conditions. The [runtime summary](pilot-1/runtime/summary.json) includes all measurements and host-load fields. All 36 compressed raw k6 streams passed decompression checks and are indexed with SHA-256 hashes in [raw-index.json](pilot-1/runtime/raw-index.json); they currently occupy 65.4 MB locally. A scan found no common credential patterns in those streams. The [checksummed archive](pilot-1/runtime/raw-archive.json) is on the [raw-data-v1 release](https://github.com/sheetgenius/agentmvc/releases/tag/raw-data-v1).

## What the implementation shows

Servant's type-level route tree gives compiler-checked handler coverage, and the result uses Warp/WAI, STM socket rooms, PostgreSQL constraints and set-oriented list queries, `jose` JWTs, bcrypt, and a durable export worker. The code is split across domain, account, article, sharing, export, auth, database, and route modules. The largest source file is `app/Articles.hs` at 3,465 owned tokens, about 26% of owned backend tokens.

It did not reach the prompt's strongest **safe to change** form. HTTP bodies and domain states remain dynamic `Aeson.Value`, text statuses, optional integer user IDs, and a boolean shared-edit flag. `Db.runSql` tunnels every dynamic SQL statement through one JSONB parameter and one JSONB result; the prewarmed `hasql-th` typed statements and `pg-migrate` library were not used. One `MVar`-protected Hasql connection serializes database access. The agent documented that connection limit itself. Its focused rule test uses HTTP, so it does not directly check pure domain decisions. The source review found one incomplete rule-owner claim: draft visibility is checked in both `Domain.articleVisibility` and the list SQL predicate. [review.json](pilot-1/review.json) records the audit.

A held-out diagnostic found a second ownership gap: registration accepted a seven-character password and login succeeded, while password update rejects passwords shorter than eight characters. The frozen gates do not assert a registration minimum, so this is a **policy inconsistency diagnostic**, not a scored acceptance failure. The same diagnostic confirmed login after email change and a title containing `/ ? #` round-tripped correctly. See [diagnostics.json](pilot-1/diagnostics.json).

## Artifacts

- [Frozen shared prompt](frozen-prompt.md), [fixture manifest](../../one-shot-v2/fixture-manifest.json), [preflight record](preflight.json), and [isolation result](isolation.json)
- [Scrubbed readable transcript](https://github.com/sheetgenius/agentmvc/blob/8c8999d8ef4c29acacd01a60d4fed1400231143d/results/one-shot-v2-servant/pilot-1/transcript.md), [scrubbed event stream](https://github.com/sheetgenius/agentmvc/blob/8c8999d8ef4c29acacd01a60d4fed1400231143d/results/one-shot-v2-servant/pilot-1/transcript.jsonl), and [agent report](https://github.com/sheetgenius/agentmvc/blob/8c8999d8ef4c29acacd01a60d4fed1400231143d/results/one-shot-v2-servant/pilot-1/agent-report.md)
- [Measured effort](pilot-1/run.json), [attempt counts](pilot-1/check-attempts.json), [source size](pilot-1/size.json), [file inventory](pilot-1/source-files.json), [project docs size](pilot-1/docs.json), [test size](pilot-1/tests.json), and [finished source snapshot](pilot-1/source/)
- [Independent development gate](pilot-1/development.json) and [log](pilot-1/development.log); [independent production gate](pilot-1/production.json) and [log](pilot-1/production.log)
- [Runtime summary](pilot-1/runtime/summary.json), [raw stream index](pilot-1/runtime/raw-index.json), [prepared raw archive checksum](pilot-1/runtime/raw-archive.json), and the per-round HTTP and WebSocket JSON files under `pilot-1/runtime/`

No scored application source was edited after the measured agent exited.
