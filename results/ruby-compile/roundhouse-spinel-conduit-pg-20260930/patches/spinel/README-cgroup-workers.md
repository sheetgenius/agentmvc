**Container budgets for Spinel 813def1fb and the integrated Roundhouse series.**
Apply the Spinel patch to that commit. Apply `70-cgroup-boot.patch` after the
shared Roundhouse series. Both apply checks passed. No upstream changes were
published.

Spinel defaults to `ceil(quota/period)`, bounded by affinity and online CPUs.
Main worker 0 is included. An explicit `SPINEL_WORKERS` wins. The generic
`SPINEL_WORKER_FACTOR` scales a finite quota before rounding; without a quota
it has no effect. Roundhouse's synchronous PostgreSQL backend defaults this
factor to 2, based on the measured DB endpoint in `../REPORT.md`; factor 1
opts out. The runtime image carries no worker environment default.

The parser resolves the process cgroup and its mount through proc files,
checks visible ancestors, supports v2 and v1, and falls back to affinity and
online CPUs. `make resource-test` exercises fake proc/mount trees without a
production environment override. macOS uses the online-CPU fallback.

Memory detection caps collection triggers: object and old strings each at
M/8, young strings at M/(8 × configured workers). This limits GC pacing,
including adaptive retunes and explicit floors. It cannot cap live objects,
external allocations, or process RSS.

To reproduce source in a fresh w14-style directory containing these patches
and the scripts, run:

```sh
bash prepare-workspace.sh
python3 prepare-toolchain.py
BUILDX_CONFIG="$PWD/.buildx" docker build --platform linux/arm64 \
  -t spinel-spike-w14-toolchain:cgroup-v2 toolchain
bash build-fixtures.sh
bash repro/check.sh
python3 verify.py
```

`prepare-workspace.sh` expects the shared clones and series two directories
above its worker directory. Existing delivered clones are already patched;
skip that script to rebuild them. The source fixture is `../app`, copied
from w13's DB-bound article-list app.

Minimal two-CPU reproduction, after compiling the fixtures:

```sh
docker run --rm --name spinel-spike-w14-before --cpus=2 --memory=1g \
  -v "$PWD/repro:/work:ro" spinel-spike-w14-toolchain:cgroup-v2 /work/before
# 18

docker run --rm --name spinel-spike-w14-after --cpus=2 --memory=1g \
  -v "$PWD/repro:/work:ro" spinel-spike-w14-toolchain:cgroup-v2 /work/after
# 2 (cgroup cpu.max 200000/100000)
# memory=1073741824
```

`before.rb` contains the exact removed autodetection function and is compiled
with the original w12 toolchain. `after.rb` calls the patched scheduler's
accessor. `verify.py` builds the production fixture, verifies boot banners,
runs k6 against real PostgreSQL, and removes its containers and network in
`finally`. It uses only host ports 4324 and 54324.
