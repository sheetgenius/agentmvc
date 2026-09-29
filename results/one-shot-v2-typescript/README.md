# TypeScript v2 pilot

This is one measured Conduit build using TypeScript 5.9, Node 24, AdonisJS 7, Lucid 22, and PostgreSQL 17. It received the **same frozen safe-evolution prompt** as the [Servant v2 pilot](../one-shot-v2-servant/README.md), with a stack-specific environment. It is a separate prompt condition from the earlier Rails, Phoenix, Loco, and IHP one-shots. The TypeScript fixture hash is `d7e4579bb7205a7e475aab382547f005626f34bf9dcf775626477852c7cebcc9`; the shared prompt hash is `8d39c1f7f584ee1c00e5f3056c80d99214a4c0790bf23c22b0ea0f5dccabb943`.

## Result

| Measure | TypeScript pilot |
| --- | ---: |
| Measured agent | `gpt-6-sol`, xhigh, Codex CLI 0.157.1 |
| Agent wall time | 36 min 35 s, **environment-stall affected** |
| Uncached input plus output | 239,207 tokens, **environment-stall affected** |
| Agent shell commands | 136; 28 returned nonzero |
| Owned backend source | 9,355 `o200k_base` tokens; 1,044 nonblank, noncomment lines |
| Whole backend source | 13,727 tokens; 1,705 lines |
| Production image | 333.7 MB |
| Cold start | 0.90 / 0.73 s |
| Independent development and production gates | Pass; 10.0 and 12.4 s |
| Focused tests | 2 pass |

The agent's last report says acceptance was unverified. It had started a persistent queue worker through the synchronous `harness/ts.sh run` channel, which held the Docker check broker's global lock and queued later requests. Its code was left untouched. After stopping that specific worker and clearing its orphaned check containers, independent development and fresh production gates both passed: 17 API files, 13 security files, the live socket protocol, and four browser tests. The first independent production attempt failed because an orphaned container held the port; [both attempts](pilot-1/production-attempt1.json) are recorded. The final production gate built the image from scratch.

The agent self-reported different size counts. [size.json](pilot-1/size.json) is the independent scaffold-relative count used here. The focused tests are [measured separately](pilot-1/tests.json) at 501 tokens and 67 nonblank lines. An independent Node 24 run passed TypeScript, ESLint, Prettier, and both focused tests. Its first `npm test` invocation lacked required environment variables; [static.json](pilot-1/static.json) and [static.log](pilot-1/static.log) preserve that harness invocation error and the successful retry.

Before the measured run, the product-free scaffold was proven in development and in a compiled production image, with a fresh PostgreSQL migration, worker, and browser check. A watched route edit reached the development server in 0.56 s. A disposable Codex probe confirmed own-workspace writes, denied parent and sibling reads, and denied the host Docker socket. The agent had a fresh home with memory and subagents off and no interactive approvals. See [preflight.json](preflight.json) and [isolation.json](isolation.json).

## Repeated production measurements

Each HTTP round used 16 virtual users, 3 s warmup, and 15 s per scenario. The app and database each had limits of 2 CPUs and 1 GiB. All HTTP checks passed. PostgreSQL statement counts are measured calls per request.

| Scenario | Requests/s, rounds 1 / 2 | p95 ms, rounds 1 / 2 | SQL statements/request |
| --- | ---: | ---: | ---: |
| Anonymous article list | 2,058 / 2,118 | 55.11 / 53.17 | 2.01 |
| Signed-in article list | 2,497 / 2,493 | 28.13 / 29.46 | 3.01 |
| Tag-filtered list | 2,450 / 2,316 | 46.22 / 48.70 | 2.01 |
| Feed | 2,785 / 2,724 | 18.39 / 18.92 | 3.01 |
| Single article | 6,630 / 6,298 | 3.66 / 3.53 | 2.00 |
| Comments | 4,439 / 4,242 | 3.62 / 3.43 | 2.00 |
| Tags | 5,080 / 5,019 | 2.50 / 2.61 | 1.00 |
| Favorite toggle | 2,592 / 2,624 | 11.91 / 16.97 | 4.01 |
| Article creation | 2,894 / 2,390 | 8.39 / 11.07 | 7.01 |

WebSocket broadcasts to 10, 100, and 500 subscribers had no missing, duplicate, or regressed revisions in either round. Their p95 delivery latencies were **11.15 / 11.16 ms**, **11.40 / 10.99 ms**, and **10.45 / 12.74 ms**. Admission and revocation are held in one process; this does not establish multi-instance behavior. The host was shared: one-minute load ranged from 5.1 to 8.0 during HTTP scenarios, and unrelated containers consumed up to 201% of one CPU. Treat cross-session speed comparisons as load-qualified. The [summary](pilot-1/runtime/summary.json) preserves all per-round data and host-load fields.

## What the implementation shows

AdonisJS supplied routes, controllers, Lucid migrations and query building, password hashing, and a durable PostgreSQL queue. The agent used `jose` for the contract's JWTs and `ws` for its raw WebSocket protocol. PostgreSQL constraints own persistent invariants. Article lists use a fixed two or three statements regardless of the number of returned rows, and both author and share edits call one compare-and-swap write path. The largest owned source file is `app/domain/articles.ts` at 2,240 tokens, about 24% of owned backend source.

This pilot did **not** fully exercise the language and framework path we wanted to test. Vine and Bouncer were installed but unused. Inputs remain mostly `Record<string, unknown>` with custom field extraction; database results are cast to manually declared row types. Authorization uses a boolean `required` parameter and non-null assertions, and article updates use an author/share mode flag. The named visibility rule is repeated in list SQL; the password minimum is repeated at registration and update; WebSocket attachment is registered in two places. These choices compress source, but give the compiler less leverage when a fresh agent changes a rule. [review.json](pilot-1/review.json) records the source audit. A guided follow-up should keep this measured result immutable and target those ownership and type boundaries directly.

The TypeScript pilot is about 29% smaller in owned tokens than the one Servant v2 pilot, but has about 21% more owned lines. Whole backend tokens are close because the TypeScript scaffold is larger. One run per stack, different framework familiarity, and this pilot's broker stall limit claims about agent effort. The two runtime sessions occurred under different host loads; neither result is a language speed ranking.

## Artifacts

- [Frozen shared prompt](frozen-prompt.md), [fixture manifest](../../one-shot-v2-typescript/fixture-manifest.json), [preflight](preflight.json), and [isolation probe](isolation.json)
- [Scrubbed transcript](pilot-1/transcript.md), [event stream](pilot-1/transcript.jsonl), [agent report](pilot-1/agent-report.md), [effort record](pilot-1/run.json), [command failures](pilot-1/command-failures.json), and [attempt counts](pilot-1/check-attempts.json)
- [Source snapshot](pilot-1/source/), [size](pilot-1/size.json), [file inventory](pilot-1/source-files.json), [test size](pilot-1/tests.json), [project docs size](pilot-1/docs.json), and [source review](pilot-1/review.json)
- [Development gate](pilot-1/development.json), [production gate](pilot-1/production.json), their logs, and the [first production attempt](pilot-1/production-attempt1.json)
- [Repeated runtime summary](pilot-1/runtime/summary.json), per-round HTTP and WebSocket JSON, and lossless raw streams indexed in [raw-data](../raw-data/README.md)

No scored application source was edited after the measured agent exited.
