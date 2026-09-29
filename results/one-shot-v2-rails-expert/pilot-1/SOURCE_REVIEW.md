# Rails measured source review

This reviews the immutable [pilot source](source/) at the hash in
[source-snapshot.json](source-snapshot.json). The measured implementation passed
the original development and production gates. The separate
[common HTTP replay](../../v2-expert-symmetry/held-out/rails-scored.json) passed
20 of 21 contract probes and all three additional quality diagnostics. Its one
contract failure is explicit JSON `"revision": null`: the author update returns
200 and changes the article, where [drafts.md](../../../spec/features/drafts/drafts.md)
requires 422 for a noninteger revision. An omitted author revision remains
valid. The scored source and image have not been changed.

## Framework and rule ownership

Rails handles routing, controllers, validation, associations, scopes,
transactions and jobs. `has_secure_password` owns password hashing; GoodJob
provides the PostgreSQL queue; Faye WebSocket handles the raw client protocol.
The [rule map](source/AGENTS.md) points to `ArticleCommit` for revision checked
edits, `ArticleShare` for keys, `LiveRooms` for presence, and `ArticleExport`
for pending job recovery. Article pages are selected before association
preloading and page scoped follow/favorite aggregates. The migration contains
unique, reference, status and revision constraints. Export snapshots read
article and comment data in one SQL statement, then finish idempotently.

## Source-level risks beyond the frozen gates

These are code review findings, not claims of observed remote failures:

- `ArticleCommit` uses `nil` for both omitted and explicit-null revision. This
  mechanism explains the observed HTTP failure.
- `SharesController#create` and `#destroy` collect revoked link IDs before
  acquiring the article lock. A concurrent rotation could revoke a newly
  created link in the database without notifying its connected sockets.
- `LiveSocket` rescues JSON parsing errors but then indexes the parsed value
  as an object. Valid scalar JSON can raise outside that rescue.
- `CommentsController#index` defaults to a 100-comment cap, though the base
  comments endpoint has no pagination contract. A thread with more than 100
  comments could be silently truncated.
- Publishing increments the article revision without an `updated` event for
  an already subscribed shared editor.
- The `ArticleCommit` service itself receives no author identity and does not
  verify `share.article_id == article.id`. Current HTTP callers supply matching
  objects, but direct future callers could misuse the service.
- Room and login throttle maps retain old keys; the throttle checks after
  password verification. These are growth and load concerns in long-lived
  processes.

## Measurement note

[size.json](size.json) is authoritative: **6,010 agent-owned tokens / 644
agent-owned code lines**, versus the agent report's 6,604 / 643 self-count.
The unchanged generated GoodJob migration adds zero owned code but contributes
1,448 tokens / 114 nonblank lines to the whole-backend view. The same size
classifier includes application startup code and excludes tests, docs,
lockfiles, Dockerfiles, and generated schema.

The separately labelled unscored Rails reference revision addresses several
of these findings; its checks and numbers must not be attributed to this
measured agent.
