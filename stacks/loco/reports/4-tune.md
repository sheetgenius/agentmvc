## Status

DONE. Completed three tuning iterations and updated the [README](../4-tune/README.md).

## Gate result

`bin/check` and `bin/check-production` both passed in the final iteration: 15 of 15 acceptance files each.

## Before and after

| Scenario | Requests/s | p95 latency (ms) | SQL/request |
|---|---:|---:|---:|
| Anonymous list | 800.7 → 2801.0 | 37.17 → 7.69 | 42 → 4 |
| Signed-in list | 537.2 → 2382.7 | 48.51 → 9.36 | 83 → 7 |
| Tagged list | 799.0 → 3344.6 | 24.90 → 6.67 | 41 → 4 |
| Feed | 490.9 → 2101.2 | 52.02 → 10.03 | 84 → 7 |
| Article | 6839.9 → 4208.8 | 3.26 → 5.16 | 6 → 5.98 |
| Comments | 10153.1 → 5999.0 | 2.10 → 3.66 | 4 → 4 |
| Tags | 2043.7 → 3865.8 | 14.52 → 6.53 | 1 → 1 |
| Favorite toggle | 3339.0 → 2213.8 | 7.34 → 10.94 | 7 → 6.98 |
| Create article | 3232.1 → 2531.4 | 9.32 → 10.26 | 6 → 5 |

These are the supplied baseline and final benchmark. Several single-item scenarios were slower in the final run; their SQL counts were nearly unchanged, and unrelated scenarios varied between runs.

## What you changed

- Batched list-page authors, favorite counts, and viewer relationships to remove per-article queries.
- Moved tag filtering and pagination into PostgreSQL, with a `jsonb` tag list and GIN index.
- Made `/api/tags` select tag data without article bodies.
- Used subqueries for feed and favorited filters, and reused the signed-in author row for single articles.

## What didn't help

Nothing was tried and reverted.

## Run counts

`bin/check`: 3 runs; `bin/check-production`: 3 runs. Benchmarks: 3 completed, plus 1 attempt that failed before the image build. Build failures hit: 1 Buildx setup failure; no image compilation failures.

## Friction log

- List views issued dozens of queries because each article loaded its relationships separately.
- Tag filtering loaded every published article because tags were stored as JSON and filtered in Rust.
- Docker Buildx tried to write activity state outside the writable workspace; a workspace-local `BUILDX_CONFIG` resolved it.
- Throughput varied across runs even for unchanged paths, limiting attribution from latency alone.

## Agent-friendliness notes

SeaORM’s grouped queries and subqueries kept the tuning in ordinary application code, and Loco migrations kept the storage change explicit. The main discovery costs were SeaORM trait imports and the distinction between JSON and `jsonb`.