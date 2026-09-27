## Status

**DONE.** Shared live article editing is implemented. The README is updated, and the frozen frontend source was left unchanged.

## Gate result

The final `bin/check` and `bin/check-production` runs both exited **0**. Each passed 17 Hurl files (237 requests), the live protocol suite, 3 Playwright tests, formatter, and Clippy. Production also passed all 13 security files (52 requests).

## Where the feature landed

[shares.rs](../8-live-editing/conduit/src/controllers/shares.rs) defines the HTTP and WebSocket routes. [article_shares.rs](../8-live-editing/conduit/src/models/article_shares.rs) handles link storage; [live_rooms.rs](../8-live-editing/conduit/src/models/live_rooms.rs) handles rooms. The [migration](../8-live-editing/conduit/migration/src/m20260927_000005_article_shares.rs) adds the share table. [README.md](../8-live-editing/README.md) now records the rules.

## WebSocket and presence design

The first `subscribe` message authorizes admission. Each article room counts admitted sockets in memory, admits 100 atomically, and sends `room_full` to the next valid subscriber. A room lock covers the `ready` snapshot; broadcasts follow database commits, and each socket filters older revisions. Revocation sends `revoked` and closes active subscriptions.

## Editing-link permissions

Only the author manages links. A link grants title and body read/edit access to its one article. Its ID remains tied to the article when the slug changes. The server stores a hash of the random key; missing, unknown, and revoked credentials receive `404` on HTTP routes. Saves require a base revision and return the current article on `409`.

## Cleanup passes

One cleanup pass removed empty-room allocation for invalid socket IDs, added resync for lagging sockets, and reduced the Docker build context. Both gates exited **0** afterward.

## Spec decisions

Shared `PUT` accepts only title, body, and integer revision. Key verification precedes payload validation. The unchanged shared checker runs in a separate Linux Playwright harness through [bin/check-live](../8-live-editing/bin/check-live).

## Run counts

8 gate runs: `bin/check` exited **143, 1, 1, 1, 0, 0**; `bin/check-production` exited **0, 0**. The first development run was stopped while Playwright setup hung. This is below the 50-run budget.

## Friction log

The sandbox required a writable Cargo cache. The protocol client also exposed an IPv4 development binding issue. Host Chromium could not start under the macOS sandbox, so the shared checker ran in the matching Playwright Linux image. The first Linux attempt hid that image’s installed browser with a cache mount; removing it resolved the download timeout.

## Agent-friendliness notes

The README points to the link, room, route, and migration rules. Persistent capability rules live in the share model; connection counts and admission live in the room model.