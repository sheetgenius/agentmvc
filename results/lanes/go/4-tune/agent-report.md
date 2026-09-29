## Status

**DONE.** Completed three tuning iterations and updated the [README](/work/app/README.md).

## Gate result

`bin/check` and `bin/check-production` both pass on the final code: 15/15 Hurl files each. Tests and lint pass.

## Before and after

The table compares the [baseline](/work/app/perf/baseline/results.json) with the [final benchmark](/work/app/perf/latest/results.json). Each cell is **before → after**.

| Scenario | Requests/s | p95 ms | SQL/request |
|---|---:|---:|---:|
| list_anonymous | 759.3 → 2464.1 | 66.75 → 58.09 | 62 → 5 |
| list_signed_in | 422.5 → 3151.2 | 77.22 → 20.19 | 103 → 7 |
| list_by_tag | 670.5 → 2968.4 | 70.98 → 45.50 | 62 → 5 |
| feed | 325.5 → 2609.6 | 86.48 → 47.09 | 103 → 7 |
| article | 3368.5 → 3976.6 | 9.49 → 7.52 | 7 → 6 |
| comments | 5980.8 → 5468.1 | 3.53 → 4.15 | 4 → 3 |
| tags | 3528.9 → 3299.0 | 8.81 → 11.24 | 1 → 1 |
| favorite_toggle | 3303.9 → 3621.6 | 10.38 → 9.05 | 8 → 7 |
| create_article | 2953.3 → 4362.0 | 14.06 → 7.62 | 11 → 6 |

## What you changed

- Batched article tags, authors, follows, and favorite summaries per page to remove list query repetition.
- Batched comment authors and follows to reduce comment list queries.
- Added indexes for recent articles, tag filtering, favorite counts, and article comments.
- Built new article responses from saved values and skipped the unnecessary tag delete on creation.

## What didn't help

Nothing was tried and reverted. Comments and tags had lower throughput in the final short benchmark despite the comment query reduction.

## Run counts

`bin/check`: 4 runs, including one transient failure; `bin/check-production`: 3 runs; benchmarks: 3 runs; build failures: 0.

## Friction log

- Per-item relationship queries caused the high list SQL counts.
- Existing key order did not support tag filtering or favorite counts by article.
- One development check hit a database shutdown and missing container during harness startup; the retry passed.
- Three-second benchmark scenarios varied between runs, especially for comments and tags.

## Agent-friendliness notes

The route and model layout made the slow paths easy to locate. Bun’s query builder kept the batch reads readable, though assembling page responses required explicit grouping in Go. The fixed gates and benchmark made changes measurable; the short runs limit confidence in small throughput differences.