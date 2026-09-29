# Python one-shot reference 2

This **unscored maintainer repair** continues the preserved
[failed reference 1](../reference-1/README.md). The measured original and the
failed reference are unchanged.

The [source](source/) has 9,058 owned backend tokens. Beyond reference 1, it
orders ready, presence, update and revocation messages with a per-client lock.
Presence reads the current room membership when sending, and refreshes the
newly ready client as well as existing members. Network sends happen after
releasing the room registry lock.

Two deterministic regressions first reproduced the inherited stale-count
failure for overlapping joins and departures. Four ordering tests now cover
those cases, pending updates, and revocation. All 16 direct tests, formatting,
linting and Django checks pass. The independent
[development and production gates](verification.json) both pass, including
the browser test that failed in reference 1. Supplemental reviewer results
are recorded alongside this source.

Live rooms remain process-local. The registry still holds a global lock
across a database lookup during admission, which may couple unrelated rooms;
this revision does not claim to remove that performance limitation.

[Source identity](source-snapshot.json) · [Size](size.json) ·
[Parent and condition](reference.json) · [Lane comparison](../../../lanes/README.md)
