**Status:** DONE.

**Gate result:** `bin/check` and `bin/check-production` both pass. The final benchmark completed with zero failed checks.

**Before and after:** Throughput is requests/second; p95 is milliseconds; SQL is statements/request.

| Scenario | Throughput | p95 | SQL |
|---|---:|---:|---:|
| Anonymous list | 906.6 → 2048.8 | 61.64 → 60.67 | 62 → 4 |
| Signed-in list | 644.5 → 1995.5 | 66.82 → 61.77 | 103 → 5 |
| List by tag | 942.4 → 1875.7 | 62.85 → 67.05 | 62 → 4 |
| Feed | 627.8 → 1968.3 | 66.18 → 60.08 | 103 → 5 |
| Article | 7415.2 → 9498.2 | 3.20 → 2.71 | 7 → 4 |
| Comments | 14353.1 → 14227.1 | 1.79 → 1.85 | 4 → 4 |
| Tags | 6218.4 → 5753.1 | 2.52 → 2.75 | 1 → 1 |
| Favorite toggle | 3328.0 → 4392.0 | 8.88 → 6.67 | 8 → 5 |
| Create article | 3419.0 → 4912.5 | 8.99 → 5.47 | 11 → 8 |

**What you changed:**

- [articles.clj](/work/app/src/conduit/articles.clj): Batched author, follow, favorite, and tag reads across each article page to remove per-article queries.
- [README.md](/work/app/README.md): Documented the resulting query pattern.

**What didn't help:** Folding article details into the page query saved one SQL statement but lowered measured list throughput and raised latency; I reverted it.

**Run counts:** `bin/check`: 3; `bin/check-production`: 3; benchmarks: 3; build failures: 0.

**Friction log:**

- Article rendering hid database calls inside each item’s presenter, causing the list query count to grow with page size.
- Signed-in requests add a user lookup, so their SQL counts differ from anonymous requests.
- Three-second benchmark runs varied enough that fewer SQL statements did not establish a performance gain.
- Each production gate and benchmark rebuilt and started the image, making measured iterations relatively slow.

**Agent-friendliness notes:** The domain code is concentrated in `articles.clj`, which made the query pattern easy to find. The `next.jdbc` adapter kept the batch change small; database work inside presentation made its cost less visible until the benchmark.