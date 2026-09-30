# IHP production-build experiment

This is a **build-only revision** of the fourth, expert-guided IHP app. The application and migration sources are byte-for-byte identical to `.work/one-shot-ihp-4/ihp`; only `flake.nix` and `Dockerfile` changed. It is a separate optimization result, not another scored one-shot run.

The image uses IHP's `optimized-prod-server` instead of `unoptimized-prod-server`. Its startup script runs the migration first, then sets `GHCRTS=-A64m -N2 -H32m` for the server process. The worker continues to run in that server. The source copy (local workdir `shine-ihp/ihp`, not published), [fresh-production gate](production.json), [gate log](production.log), and [paired raw results](runtime/summary.json) retain the evidence.

| Metric | Guided source, original image | Same source, optimized image |
| --- | ---: | ---: |
| Production gate | Pass | Pass, 13.9 s |
| Image size | 4,363.4 MB | 4,363.3 MB |
| Cold start, paired | 0.29 / 0.27 s | 0.28 / 0.28 s |
| Anonymous list, paired | 651.2 / 646.6 req/s | 561.3 / 570.1 req/s |
| SQL per list | 1 | 1 |
| Single article, paired | 4,538.8 / 4,634.9 req/s | 5,377.2 / 5,495.1 req/s |
| 500-subscriber delivery p95 | 9.87 / 9.62 ms | 9.07 / 9.41 ms |

The optimized image passed both paired HTTP rounds and both 500-subscriber socket rounds, with 36 compressed raw HTTP streams retained. The application and database each had 2 CPU and 1 GiB limits. The combined compiler and RTS change made single-article reads about 19% faster and anonymous lists about 13% slower. The image remained too large; optimization alone did not fix packaging. These two rounds characterize this host and workload, not a general Haskell speed ratio. A follow-up should separate compiler optimization from `-N2` and test a layered/minimal image.

The [first production attempt](production-attempt1.json) failed. I initially set `GHCRTS` for every process in the image; the migration executable rejected those runtime flags, and the startup script continued to an unmigrated database. The corrected script fails on migration errors and applies the runtime setting only to the server. The [first attempt log](production-attempt1.log) is retained.
