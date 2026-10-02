# Spinel: no local patches in v5

Spinel `master` @ `d2c20df0bdc2c9c0788c24fff935c8a2fd6c5007` is built unpatched. The v4 package carried two patches; both are gone.

- **`spinel-poly-dispatch-arg-roots.patch`: dropped, now upstream.** [matz/spinel#6549](https://github.com/matz/spinel/pull/6549) (merge `02eec7d26`) is a broader version of the same GC-rooting fix, with its own regression test. The v4 package's [deterministic repro](../../../roundhouse-spinel-conduit-pg-20260930/patches/spinel/repro-poly-dispatch/) reports `bad=0` on this Spinel, also under `SPINEL_GC_STRESS=1` and with 16 threads ([log](../../evidence/probes/spinel-poly-dispatch-on-head.log)).
- **`spinel-cgroup-workers.patch`: dropped by choice.** It was never upstreamed, and its 3-way apply conflicts on this head (Makefile, docs). Upstream's documented answer ([matz/spinel#4266](https://github.com/matz/spinel/issues/4266), `docs/thread.md`) is a program-level `SPINEL_WORKERS`. The production image therefore sets `ENV SPINEL_WORKERS=4`: the 2-CPU budget times the PostgreSQL lane's factor of 2, the same 4 workers v4 derived from the cgroup quota. Roundhouse patch 73 (boot banner and factor default over the patch's FFI symbols) is dropped with it; the stock banner reports `OS workers: 4 (SPINEL_WORKERS)`.

What the cgroup patch did that v5 no longer does:
- **Quota-derived sizing.** The worker count no longer follows `--cpus`; a different CPU budget needs a different `SPINEL_WORKERS`.
- **Memory-budgeted GC trigger.** Peak memory in the anonymous-list sanity run was 30–33 MB, against 26–27 MB for v4 ([summary](../../evidence/sanity-throughput/summary.txt)).

A quota-aware default worker count belongs in an RFC issue on Spinel, with the memory budget as a separate proposal. It has not been opened.
