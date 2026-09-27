**Status:** DONE. Completed three tuning iterations and updated the [README](../4-tune/README.md).

**Gate result:** `bin/check` and `bin/check-production` both passed in every iteration. The final benchmark recorded zero failed checks.

**Before and after:** Requests/s (higher is better), p95 in ms (lower is better), and SQL statements/request. Results: baseline and final.

| Scenario | Requests/s | p95 ms | SQL/request |
|---|---:|---:|---:|
| Anonymous list | 1,495 → 3,480 | 29.95 → 11.63 | 23 → 4 |
| Signed-in list | 790 → 2,453 | 30.90 → 10.32 | 64 → 7 |
| List by tag | 1,331 → 3,555 | 35.32 → 7.01 | 23 → 4 |
| Feed | 750 → 2,407 | 35.31 → 9.98 | 64 → 7 |
| Article | 8,236 → 6,799 | 3.10 → 3.93 | 6 → 4 |
| Comments | 11,828 → 8,178 | 2.29 → 3.28 | 4 → 3 |
| Tags | 6,821 → 4,878 | 3.38 → 5.07 | 1 → 1 |
| Favorite toggle | 3,246 → 2,221 | 7.23 → 10.88 | 7 → 5 |
| Create article | 2,744 → 2,316 | 9.17 → 10.26 | 6 → 4 |

The list and feed gains are substantial. The final run measured lower throughput than baseline on the other five scenarios despite fewer SQL statements on four of them; those regressions remain in the reported result.

**What you changed:**

- Batched favorite counts and viewer relationships across each article page, removing per-article queries.
- Joined authors when fetching articles, saving a query on article and comment paths.
- Combined favorite count and viewer status in one aggregate for single-article responses.
- Reused the author already loaded during article creation.
- Indexed `favorites.article_id` for counts by article.
- Reduced production request-log volume to warning and error messages.

**What didn't help:** No tuning change was reverted.

**Run counts:** `bin/check`: 3; `bin/check-production`: 3; benchmark: 3 completed runs plus 1 failed build attempt; build failures: 1.

**Friction log:**

- Presenter lookups hid three SQL queries per listed article, causing the largest initial cost.
- The first benchmark build could not write Docker Buildx activity outside the workspace; a workspace-local `BUILDX_CONFIG` resolved it.
- Throughput varied across short runs even on unchanged paths, making smaller changes harder to judge.

**Agent-friendliness notes:** Ecto query composition and virtual schema fields made page-wide loading straightforward. The baseline’s per-request SQL counts made the N+1 problem visible; the Presenter’s database calls made its cause less obvious from the controller alone.