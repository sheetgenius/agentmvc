**Status:** DONE.

**Gate result:** `bin/check` and `bin/check-production` both pass. The final production benchmark is in [results.json](/work/app/perf/latest/results.json).

**Before and after:** Baseline → final; 16 users, 3-second scenarios.

| Scenario | Requests/s | p95 (ms) | SQL/request |
|---|---:|---:|---:|
| Anonymous list | 151.7 → 518.6 | 128.00 → 42.75 | 22.00 → 2.00 |
| Signed-in list | 61.7 → 382.6 | 306.66 → 57.83 | 63.00 → 3.00 |
| List by tag | 149.4 → 512.0 | 134.19 → 44.80 | 22.01 → 2.00 |
| Feed | 61.1 → 385.3 | 328.39 → 56.24 | 63.03 → 3.00 |
| Article | 449.3 → 497.7 | 49.32 → 45.33 | 5.00 → 2.00 |
| Comments | 664.8 → 633.9 | 32.66 → 38.35 | 2.00 → 2.00 |
| Tags | 956.5 → 955.8 | 22.76 → 23.01 | 1.00 → 1.00 |
| Favorite toggle | 371.0 → 378.9 | 59.08 → 57.53 | 8.97 → 8.97 |
| Create article | 450.4 → 450.6 | 50.73 → 51.50 | 6.00 → 6.00 |

**What you changed:**

- Added favorite counts and viewer relationship checks to the article queryset, removing per-article queries from lists and feeds.
- Deferred article bodies in summaries and used the same queryset for single-article reads.
- Documented the measured changes in [README.md](/work/app/README.md).

**What didn't help:** A fresh annotated read after favorite changes cut SQL from about nine to seven statements, but reduced throughput and raised p95 latency. I reverted it.

**Run counts:** `bin/check`: 5 runs; `bin/check-production`: 4 runs; benchmarks: 4 runs; build failures: 0.

**Friction log:**

- Response formatting hid the list N+1 queries because each article fetched three relationship values.
- Each benchmark rebuilt and reseeded disposable containers, making iterations slow.
- Host load varied between short runs, making small latency differences hard to trust.
- An initial 101-character line failed Ruff after the acceptance requests had passed.

**Agent-friendliness notes:** Django queryset annotations made the query fix easy to locate and reuse. The serializer’s implicit database reads made the performance cost harder to see from the route alone.