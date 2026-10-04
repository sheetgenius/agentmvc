# Spinel patches: none

v6 builds Spinel master `b7d04a903c909ee6681c6b203ded8830841d114e` without local changes, 339 commits after
[v5](../../../roundhouse-spinel-conduit-pg-20261002/README.md). Both remaining LoginThrottle changes are still
needed; the v6 [workaround trials](../../evidence/gates/reverts/) record the failures.

The production image sets `SPINEL_WORKERS=4`, as v5 did. It does not restore v4's cgroup worker-count or
memory-budgeted GC patch. No timing or memory comparison was made for v6.
