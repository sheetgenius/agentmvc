# Rails page-query revision

This separate source copy (local workdir `shine-rails-query`, not published) changes only `ApplicationController#page` and `ConduitJson`. A page now preloads authors and asks Active Record for favorite counts, viewer favorites, and follows in bounded batches. The same serializer still owns the article and profile JSON shapes. It adds 207 owned tokens and 12 owned lines under the original Rails measurement exclusions.

The product and security checks passed on [development attempt 1](query/development-attempt1.json), but RuboCop found four missing spaces in newly written array literals. After formatting, [development attempt 2](query/development-attempt2.json) and the [fresh-production gate](query/production-attempt1.json) passed. Both paired runtime rounds passed all HTTP and socket checks, with [36 compressed raw HTTP streams](query/runtime/summary.json).

| Metric | Original one-shot Rails | Page-query revision |
| --- | ---: | ---: |
| Anonymous list SQL/request | ~25 | 4.01 |
| Anonymous list req/s, paired | 128.2 / 140.4 | 535.1 / 537.0 |
| Signed-in list SQL/request | 47.08 | 7.02 |
| Signed-in list req/s, paired | 69.5 / 79.2 | 390.8 / 388.3 |
| Tagged list SQL/request | ~33.4 | ~4.0 |
| Tagged list req/s, paired | 117.9 / 124.6 | 508.6 / 511.7 |
| Image size | 449.8 MB | 449.8 MB |
| 500-subscriber delivery p95 | 13.46 / 12.25 ms | 11.54 / 9.59 ms |

Each app and database had 2 CPU and 1 GiB limits. This is a clear list-query gain for the fixed workload; the single-article and WebSocket paths were not intentionally changed. Puma still uses its default one-worker setting. A separate worker-count experiment can test CPU scaling without mixing that configuration change into these code results.
