## Status

**DONE.** Shared live article editing is implemented. The frozen frontend and acceptance tests were left unchanged.

## Gate result

`bin/check` exited **0** and `bin/check-production` exited **0** after both cleanup passes. Each final gate run passed 17 Hurl files, one live protocol suite, three Playwright tests, and RuboCop (53 files, no offenses). The production image also passed all 13 security files (52 requests). Hurl request totals varied slightly because the export checks poll for completion.

## Where the feature landed

[ArticleShare](../8-live-editing/app/models/article_share.rb) stores the stable share ID and key digest. [SharesController](../8-live-editing/app/controllers/api/shares_controller.rb) serves revision checked shared reads and saves. [Article](../8-live-editing/app/models/article.rb) owns the shared article shape and broadcasts committed revisions. Routes, the migration, and [README.md](../8-live-editing/README.md) were updated.

## WebSocket and presence design

[ShareSocket](../8-live-editing/app/services/share_socket.rb) accepts the JSON subscription through Faye. [ShareRoom](../8-live-editing/app/services/share_room.rb) keeps presence in memory, admits at most 100 sockets atomically, and queues ordered broadcasts on EventMachine after commit. Revocation closes admitted sockets.

## Editing-link permissions

Only the author can create, rotate, or revoke a link. A holder can read and revise that article’s title and body; the key grants no other API access. The server stores a SHA-256 key digest, and the share ID stays attached to the article when its slug changes.

## Cleanup passes

1. Moved unauthenticated socket timeout closure onto EventMachine. Both gates exited 0.
2. Captured broadcast recipients at queue time, initialized the room mutex eagerly, and removed a routine save log warning. Both gates exited 0.

## Spec decisions

A socket receives no article or presence data before a valid first subscription. An unauthenticated socket closes after four seconds. Revision checks use the existing locked `Article#revise!` rule; stale shared saves return the current shared article.

## Run counts

`bin/check`: **9** invocations, including early failures and one interrupted dependency setup. `bin/check-production`: **3** standalone invocations, all green; it also ran inside each of the **3** successful `bin/check` invocations.

## Friction log

Faye broadcasts initially failed from the HTTP thread; scheduling writes on EventMachine fixed delivery. Host Chromium could not start under the macOS sandbox. An older Linux Playwright image could not download the matching browser, so [bin/check-live](../8-live-editing/bin/check-live) now runs the unchanged shared harness in the matching official Playwright image.

## Agent-friendliness notes

Link authentication lives in `ArticleShare`, revision rules and the shared article shape in `Article`, and socket admission and presence in `ShareRoom`. The README maps these rules to their files.