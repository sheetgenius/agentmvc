# Python one-shot reference 1 — production check failed

This **unscored maintainer repair** is preserved as a failed reference attempt.
Its [source](source/) and [verification](verification.json) are immutable.
The [measured original](../source/) remains unchanged.

The repair separates favorite filtering from aggregation, validates the shared
envelope, adds an expiring login throttle, revokes sockets after article
deletion, and bounds comment follow lookups. It also avoids loading article
bodies for summaries. The source contains 9,015 owned backend tokens (+297).

All 12 direct tests, formatting/lint checks, and independent development checks
passed. The production browser check then failed: two simultaneous editor
joins did not consistently settle at `2 here`. The failure occurred in the
test for preserving newer typing and socket state during a delayed save.

The live-room code was unchanged from the measured original. Its captured
presence counts and readiness ordering can miss or overwrite a newer count.
This is now a reproduced failure, rather than only a source-review concern.
A separate reference revision repairs that race; this attempt is not presented
as a passing reference or included in the reference performance comparison.
