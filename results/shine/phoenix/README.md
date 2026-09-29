# Phoenix production release

This is a build-only copy of the semantic-density Phoenix app. The application code is unchanged. `Dockerfile` now runs `mix release` and copies the release into a Debian runtime image; `Conduit.Release.migrate/0` is the release migration entry point. The [source copy](../../../.work/shine-phoenix/phoenix) passed [development](development-attempt1.json) and [fresh production](production-attempt2.json) gates. The [first production attempt](production-attempt1.json) could not bind port 4102 because the existing development server was using it; the repeat used port 4412 without touching that server.

| Metric | Original image | Release image |
| --- | ---: | ---: |
| Image size | 1,673.4 MB | 165.0 MB |
| Cold start, paired | 1.53 / 1.17 s | 0.91 / 0.92 s |
| Anonymous list, paired | 1,049.3 / 1,038.1 req/s | 1,106.9 / 1,099.4 req/s |
| SQL per list | 42.01 | 42.01 |
| Single article, paired | 5,267.2 / 5,611.1 req/s | 5,820.3 / 5,756.2 req/s |
| 500-subscriber delivery p95 | 9.98 / 13.83 ms | 9.77 / 9.90 ms |

Both release rounds passed all HTTP and socket checks. The [summary and 36 compressed raw streams](release/runtime/summary.json) use the same 2 CPU / 1 GiB app and database limits as the original run. This is evidence for this image and workload, not a language-level speed claim. A separate [query revision](query/) addresses the list's repeated database calls.
