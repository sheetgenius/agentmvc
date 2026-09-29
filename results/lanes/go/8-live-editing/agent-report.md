## Status

**DONE.** Shared live article editing is implemented, and the README is updated.

## Gate result

`bin/check` and `bin/check-production` both exited **0** on the final cleanup pass. Each passed 17 API Hurl files, the live protocol check, four Playwright tests, and all 13 security Hurl files. Go tests, the race test, gofmt, and go vet passed.

## Where the feature landed

[shares.go](/work/app/internal/conduit/shares.go) owns link and shared HTTP rules; [live.go](/work/app/internal/conduit/live.go) owns sockets and presence. The share schema is in [00006_shares.sql](/work/app/internal/platform/migrations/00006_shares.sql). Routes, article broadcasts, and the contract guide are updated in [http.go](/work/app/internal/conduit/http.go), [articles.go](/work/app/internal/conduit/articles.go), and [README.md](/work/app/README.md).

## WebSocket and presence design

An in-process room serializes admission, snapshots, and broadcasts. It admits 100 authorized sockets per article; presence counts sockets. Subscribers receive `ready`, then revision-ordered `updated` messages. Revocation sends `revoked` and closes affected sockets.

## Editing-link permissions

Only the author manages a link. The database stores its key hash and attaches its share ID to the article’s stable ID. A valid holder can read and revision-check edits to that article’s title and body only. Invalid or revoked pairs return 404.

## Cleanup passes

One pass prioritized revocation over queued notifications and made shared saves return the revision from their conditional database update. Both gates ended that pass green.

## Spec decisions

The frozen client and shared tests were left unchanged. The socket accepts the frozen Vite client’s local origin; dirty-draft handling remains in that client.

## Run counts

Four `bin/check` runs: two failures, then two passes. Two `bin/check-production` runs: both passed. Final gates each ran 17 API files, one protocol check, four browser tests, and 13 security files.

## Friction log

The first browser run exposed a WebSocket origin rejection. A subsequent development run hit a transient database shutdown race in the check harness; retrying passed.

## Agent-friendliness notes

The README now maps the link, shared-save, room, and revocation rules to their Go files and explains the stable share ID and single-process presence model.