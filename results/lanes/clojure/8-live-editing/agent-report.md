## Status

**DONE.** Shared live article editing is implemented, and [README.md](/work/app/README.md) is updated.

## Gate result

`bin/check`: **exit 0**. `bin/check-production`: **exit 0**. Each final gate passed 17 Hurl files (237 requests), the live protocol check, four Playwright tests, and 13 security files (52 requests) against the production image. Formatter and linter passed with zero warnings or errors. The development gate also passed the existing unit test.

## Where the feature landed

[shares.clj](/work/app/src/conduit/shares.clj) owns links and shared saves; [live.clj](/work/app/src/conduit/live.clj) owns sockets and presence. [articles.clj](/work/app/src/conduit/articles.clj) supplies the common revision update rule. The routes, migration, and gate scripts are updated.

## WebSocket and presence design

Ring and Jetty serve sockets in the existing container. An in-memory room admits 100 authorized sockets, sends ordered revision updates, and counts each connected tab. Admission and its `ready` snapshot share a lock with broadcasts, so a racing save appears in `ready` or a later `updated` message.

## Editing-link permissions

Only the author manages a link. Its stable ID survives slug changes; PostgreSQL stores only a hash of its 32-byte random key. Holders can read and revision-save that article’s title and body. Rotation or revocation closes active sockets. An invalid key returns `404` before shared `PUT` body validation.

## Cleanup passes

Two passes aligned database lock order, hardened socket sends, completed both gate entry points, and checked error precedence. Both gates were green after the final changes.

## Spec decisions

The shared client remains unchanged. Shared saves require exactly title, body, and an integer revision; stale saves return `409` with the current shared article. Presence is advisory and local to the single backend instance.

## Run counts

**11 check runs:** one failed development run exposed a presence count bug; the remaining ten exited 0.

## Friction log

The first protocol run showed existing editors the count before the new editor was included. Fixing that count cleared the protocol and browser checks. Host `git` was unavailable because its developer tools path was invalid; this did not affect the gates.

## Agent-friendliness notes

Link rules, room rules, and the shared article update rule each have a clear source owner, documented in the README.