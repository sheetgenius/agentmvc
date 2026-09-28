# Findings so far

Ten agent runs on 27 and 28 September 2026, with one model and one small product. They show some patterns clearly, and they are too few to rank close differences. Every number here is in the [run ledger](../results/runs.jsonl).

## The baseline prompt in four stacks

| | Rails | Phoenix | Loco | IHP, three runs |
| --- | ---: | ---: | ---: | ---: |
| Code the agent wrote, tokens | 5,454 | 8,954 | 11,437 | 10,197–10,951 |
| Relative to Rails | 1.0× | 1.6× | 2.1× | 1.9–2.0× |
| Whole backend, tokens | 10,475 | 13,399 | 21,503 | 12,350–13,001 |
| Agent time | 12 min | 14 min | 20 min | 44–73 min |
| Agent tokens, uncached input plus output | 151k | 145k | 243k | 329k–452k |
| Framework API and source lookups | 12 | 4 | 10 | 39–54 |
| Largest file's share of the code | 13% | 25% | 30% | 59–64% |
| Single article, req/s | 517 | 5,439 | 7,470 | 2,468–3,976 |
| Article list as first written, req/s | 134 | 1,044 | 607 | 1–372 |

Lookups are commands that read framework or library source or searched API docs, counted from the run transcripts. Throughput is the mean of two rounds at 16 virtual users, with each app and its database limited to 2 CPUs and 1 GiB.

## What the runs show

- **The framework mattered more than the language.** Rust itself was not slow for the agent. The first Loco agent skipped Loco, wrote a plain Axum and SQLx server, and finished the cheapest build of all in 11 minutes. Inside Loco, the same model took 20 minutes and read Loco's source 10 times. The IHP agents made 39 to 54 lookups each. The Rails and Phoenix agents looked things up mainly for the raw WebSocket, the one part of the contract their frameworks don't cover by convention.
- **Code size is a stable property of each stack.** Rails and Phoenix reproduced their size within 3% across two different prompts, and IHP's three runs landed within 4% of their average. The gap comes from what each framework lets you leave unsaid, plus each language's ceremony: explicit queries, declared types, error handling.
- **The contract suits Rails, and IHP fit it worst.** The product is a REST JSON API plus a raw WebSocket protocol, and the baseline prompt names Rails as its model of compact domain code. All three IHP agents sent every API request to one action and matched method and path by hand, so one module holds most of each IHP app.
- **The density goal pushed agents away from what types are for.** The IHP agents declared no request types, and the Loco agent passed untyped JSON through its domain. The LiquidHaskell proofs covered only trivial arithmetic, and in one run nothing checked a proof's precondition where the app calls it. Rails and IHP signed their JWTs by hand, and Phoenix hashed passwords with raw PBKDF2. In the earlier eight-step study, typed request structs made Loco's hardening the cheapest of the three; that payoff needs the agent to write the types.
- **Runtime depended on query shape and server settings first.** IHP's three runs from one prompt served 372, 52 and about 1 article-list request per second. Rails ran one Puma process, and the IHP harness built an `-O0` single-core binary. Where the settings were sound, Phoenix and Loco served single articles at 10 to 15 times Rails' rate.
- **A stack brief changed the IHP app.** With the [expert brief](../stacks/ihp/briefs/expert.md), the agent used typed IHP routes and a separate policy module, and its article list ran one SQL statement per request at 649 req/s. It also wrote the most code of any IHP run, 14,797 tokens, and took 114 minutes. That is a single run.

## The earlier eight-step study

Before the one-shot runs, the same model built a smaller base app in Rails, Phoenix and Loco and then made seven changes: drafts, packaging, tuning, hardening, polish, a background job and live editing. It found the same size ordering, with each feature costing about the same multiple of Rails' code as the whole app. After the tuning step, Phoenix and Loco served about 20 times Rails' article-list throughput. Its code, transcripts and write-ups are in Git history at commit `4ac8ee4`.

## What the runs don't show

- Whether typed stacks make later changes safer. That needs the handoff experiments in the [roadmap](roadmap.md).
- Whether the results hold for another model.
- How the ratios behave in a codebase far larger than this 10,000 to 22,000-token backend.
- Fine rankings. With one to three runs per stack, gaps under about 2× in effort or speed are noise.
