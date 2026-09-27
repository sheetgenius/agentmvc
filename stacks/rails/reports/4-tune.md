**Status:** DONE.

**Gate result:** `bin/check` and `bin/check-production` both pass: 15/15 Hurl files, 201/201 requests. The final benchmark recorded zero failed checks.

**Before and after:** Baseline → final run. RPS is requests per second; p95 is in milliseconds.

| Scenario | RPS | p95 | SQL/request |
|---|---:|---:|---:|
| Anonymous list | 89.6 → 251.6 | 205.70 → 89.36 | 44.89 → 6 |
| Signed-in list | 62.4 → 203.0 | 288.81 → 99.83 | 66.96 → 8 |
| List by tag | 82.1 → 225.2 | 223.66 → 84.86 | 53.27 → 3 |
| Feed | 62.4 → 185.9 | 289.18 → 111.08 | 67 → 8 |
| Article | 543.9 → 337.1 | 38.20 → 64.26 | 6.98 → 6.98 |
| Comments | 818.8 → 555.6 | 26.27 → 42.06 | 3.97 → 3 |
| Tags | 1610.2 → 811.4 | 13.32 → 27.43 | 1 → 1 |
| Favorite toggle | 489.6 → 272.5 | 40.25 → 82.17 | 9.45 → 9.44 |
| Create article | 425.7 → 234.0 | 46.43 → 81.77 | 10 → 10 |

The list gains are substantial. Throughput also fell on unchanged, low-query endpoints, including tags; that variation limits what can be attributed to these code changes. Image size stayed at 333.5 MB.

**What you changed:**

- [Article lists](../4-tune/app/controllers/api/articles_controller.rb#L96) preload authors, tags, and favorites to remove per-article queries.
- [Article rendering](../4-tune/app/views/api/articles/_article.json.jbuilder#L3) uses loaded associations for tags and favorite counts, with [favorite status](../4-tune/app/models/article.rb#L28) handled in the model.
- [Follow lookups](../4-tune/app/models/user.rb#L16) use a loaded association on lists and a targeted query on single records.
- [Comment lists](../4-tune/app/controllers/api/comments_controller.rb#L8) preload authors, reducing SQL from about 4 statements to 3.
- [README](../4-tune/README.md#L50) records the performance changes and measurement limits.

**What didn't help:** Raising Puma’s default from three to five threads produced mixed results and was reverted.

**Run counts:** `bin/check`: 4; `bin/check-production`: 4; completed benchmarks: 4; build failures: 1.

**Friction log:**

- Docker Buildx tried to write outside the workspace; setting `BUILDX_CONFIG` inside `tmp/` resolved it.
- Jbuilder partials hid repeated association queries, causing the list endpoints’ high SQL counts.
- The article partial serves lists and single records, so favorite and follow lookups needed to respect whether associations were already loaded.
- Throughput varied across runs even for unchanged endpoints, making the Puma setting inconclusive.

**Agent-friendliness notes:** Rails preloading and association behavior made the fix small and readable. The SQL counts exposed the problem clearly; lazy queries inside views made its source less obvious.