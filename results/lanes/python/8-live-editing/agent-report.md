**Status**

DONE. Shared live article editing is implemented, and the [README](/work/app/README.md:41) includes the rule map.

**Gate result**

`bin/check`: **0**. `bin/check-production`: **0**. Each final run passed 17 Hurl files (237 requests), the live protocol check, four Playwright tests, and all 13 security files (52 requests). Ruff lint and format checks passed; the development gate also passed Django’s system check and three project tests.

**Where the feature landed**

The editing link model and migration are in [models.py](/work/app/conduit/models.py:99). Share routes, permissions, and revision checks are in [sharing.py](/work/app/conduit/sharing.py:21). The socket consumer is in [live.py](/work/app/conduit/live.py:21), wired through [asgi.py](/work/app/config/asgi.py:12).

**WebSocket and presence design**

A socket joins the event group before reading its authorized snapshot, so a racing save appears in `ready` or a later `updated`. Presence counts admitted sockets in the single process, caps a room at 100, and reads the current count when delivering events. Committed edits and revocations are broadcast after commit.

**Editing-link permissions**

Only the article author can create, rotate, or revoke a link. The key is generated with 256 bits of randomness; only its hash is stored. A valid holder can read and revise that article’s title and body. Missing, wrong, and revoked credentials return 404.

**Cleanup passes**

Two passes completed, each ending with both gates green. The first fixed out-of-order presence counts. The second consolidated key hashing and revocation and shortened the subscription timeout to four seconds. A final gate-wrapper correction added Ruff to `bin/check-production`; both gates passed again.

**Spec decisions**

Share IDs refer to the article row, so slug changes preserve access. Shared saves require exactly title, body, and integer revision; stale saves return 409 with the current shared article.

**Run counts**

Six development gate runs, four production gate runs, and two focused live-check runs: **12 check invocations**, below the 50-run budget.

**Friction log**

The first development gate exposed the presence race. A focused live check was run once without a server and failed with `ECONNREFUSED`; it passed after startup. One later development startup failed during disposable database/container preparation; its retry passed.

**Agent-friendliness notes**

The README points to each rule’s owner. Capability checks and shared save rules live in `sharing.py`; socket admission, ordering, and presence live in `live.py`.