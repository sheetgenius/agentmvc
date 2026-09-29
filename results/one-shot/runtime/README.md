# Runtime measurement files

Two rounds run in opposite stack order: Rails → Phoenix → Loco, then Loco → Phoenix → Rails. Each scenario starts a fresh production app and PostgreSQL database in Docker, both limited to two CPUs and 1 GiB. The shared Lit client is absent from the measured request path. The local demo app and database are paused for these measurements.

`http/STACK-roundN/results.json` holds startup, image, idle/peak memory, request rate, p50/p95/p99 latency, failed k6 checks, SQL statements per request, and sampled host/container load. `k6-SCENARIO.json` is k6's native summary. `raw-SCENARIO.json.zst` is the losslessly compressed per-metric point stream; `raw-warmup-SCENARIO.json.zst` contains warmup points. Nine scenarios use 16 virtual users, a 3-second warmup, and a 15-second measured interval: anonymous list, signed-in list, tag-filtered list, feed, article, comments, tags, favorite toggle, and article creation. All 108 compressed raw streams passed `zstd -t`.

The HTTP field `foreign_container_cpu_percent_max` includes the short-lived k6 container as well as unrelated containers because k6 has an automatic Docker name. It should be read as **non-app container activity**, not as a pure background-load estimate. `host_load_1m` is total host load. Direct WebSocket files separately record the other running containers without a k6 container.

`live/STACK-roundN.json` holds the direct WebSocket workload: 10, 100, then 500 subscribers, spread over at most 100 sockets per article. Each scenario sends 20 saves, targeted at five per second. The file contains every save and delivery latency, missed/duplicate/regressed revision counts, and idle/active Docker CPU and memory samples plus background container CPU and host load. The load generator is [tools/live-load.mjs](../../../tools/live-load.mjs).

These are nearby repeated measurements on a shared host, not isolated hardware benchmarks. The recorded background load and per-round variance matter more than a narrow speed ranking. Setup failures and corrections are retained in the [failure ledger](../failures.md).

The [paired summary](summary.json) indexes all six rounds, and [SHA256SUMS](../SHA256SUMS) covers the published artifacts.
