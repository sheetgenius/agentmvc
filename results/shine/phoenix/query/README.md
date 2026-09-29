# Phoenix list-query revision

This separate [source copy](../../../../.work/shine-phoenix-query) starts from the proven Phoenix release. The only application change is in `Conduit.Content`: list pages preload authors and fetch favorite counts, viewer favorites, and follows in bounded batch queries. The ordinary Ecto `represent/3` path remains for single articles; the page uses the same projection with explicit page data. The code adds 335 owned tokens and 48 owned lines relative to the release copy, using the same measurement exclusions as the original study.

[Development attempt 1](development-attempt1.json) passed the product and security checks but failed formatting after a final edit. The formatted source passed [development attempt 2](development-attempt2.json), including all 17 API files, direct sockets, four browser tests, 13 security checks, `mix format --check-formatted`, and warnings-as-errors compilation. Its [fresh-production gate](production-attempt1.json) also passed. That build took 1,108 seconds while another application saturated the host CPU; this is not a comparable build-time measurement.

| Metric | Release before query change | Query revision |
| --- | ---: | ---: |
| Anonymous list SQL/request | 42.01 | 4.00 |
| Anonymous list req/s, paired | 1,106.9 / 1,099.4 | 3,933.2 / 4,012.6 |
| Signed-in list SQL/request | 83.01 | 7.00 |
| Signed-in list req/s, paired | 643.8 / 640.7 | 3,179.1 / 3,444.0 |
| Tagged list SQL/request | 42.01 | 4.00 |
| Tagged list req/s, paired | 1,053.6 / 1,035.9 | 4,041.8 / 4,261.0 |
| Image size | 165.0 MB | 165.0 MB |
| 500-subscriber delivery p95 | 9.77 / 9.90 ms | 9.98 / 9.67 ms |

The [paired measurement](runtime/summary.json) passed all HTTP checks and both socket rounds; 36 compressed raw HTTP streams are retained beside it. Each app and database container had 2 CPU and 1 GiB limits. Single-article throughput did not show a consistent gain because its query path was unchanged. The list improvement is large enough in both rounds to be clear on this workload; other list sizes and favorite distributions still need testing before claiming a general scaling result.
