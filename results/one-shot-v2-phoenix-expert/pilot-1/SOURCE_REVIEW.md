# Phoenix source review

This review covers the immutable [measured source snapshot](source/) at [source hash](source-snapshot.json) `96c0d9798699d5d9f485115de8becda9fda98876a9edd11885792d635e9df74d` and production image `sha256:d1320971dcf82f0cc831e8dcc5a9a6da833b306d101cd90d2a4d44cf54a92d4f`. It distinguishes accepted behavior from source inspection and post-run probes. The reference revision is a separate, unscored path.

## What the implementation gets right

| Observation | Evidence | Confidence |
| --- | --- | --- |
| Phoenix routes, Ecto schemas/changesets/queries, and a compiled Mix release handle ordinary transport, persistence, and packaging. | [Router](source/lib/conduit_web/router.ex), [article changeset](source/lib/conduit/articles/article.ex), [Dockerfile](source/Dockerfile); both independent gates passed. | Verified source and gates |
| Direct draft visibility and ownership have named owners. Author and shared-link content updates enter one locked commit; shared authority is rechecked under that lock. | [Articles](source/lib/conduit/articles.ex), especially `visible?/2`, `owner/2`, `commit/2`, and `locked_commit/3`. | Verified source; concurrency race not stress-proved |
| Article list projections batch authors, favorite counts, and caller flags for a page. | [Articles.present/3](source/lib/conduit/articles.ex); anonymous and tagged lists each measured four SQL statements/request, signed-in lists seven, in both rounds. | Verified source and runtime |
| Exports enqueue through Ecto.Multi and Oban, and completion locks the export row. | [Exports](source/lib/conduit/exports.ex), [worker](source/lib/conduit/exports/worker.ex). | Verified source; crash interleavings not exhaustively probed |
| Live rooms have a supervised per-article owner, monitored members, admission cap, and PubSub delivery. | [Room](source/lib/conduit/live/room.ex), [application supervision](source/lib/conduit/application.ex); browser and 10/100/500 subscriber measurements had no missing or reordered revisions. | Verified source and measured scenarios |

Routing and API delivery use Phoenix directly. One file, `Articles`, still holds 2,973 of 12,145 owned tokens (24.5%). Its responsibilities are explicit, but article content, comments, favorites, projections, and discovery queries all meet there; a future permissions/lifecycle handoff would test whether that remains a clear rule owner.

## Confirmed post-run failures

The [held-out production responses](held-out.json) prove these outcomes for the exact image above. The standard acceptance suite does not cover them.

- `ArticleController.update/2` parses the `article` envelope before `Articles.commit/2` checks visibility and ownership. A malformed request by a stranger returns 422 where the same valid-body request returns 403. A missing slug similarly returns 422 instead of 404 when its body is malformed.
- The changeset allows a 255-character title, then `slug_for/1` appends an 11-character suffix to the whole normalized title. PostgreSQL stores `slug` as a 255-character string; creation returned 500.
- Export and comment paths parse arbitrarily long decimal IDs, then pass the resulting integer into Ecto/database ID fields. The tested 100-digit IDs returned 500 instead of 404.
- The tag predicate is `tag = ANY(tag_list)`. With 10,001 articles and one-percent rare tags, both count and page plans used sequential scans, each filtering 9,900 rows. The GIN array index in the migration did not support this predicate shape. The query used a fixed number of SQL statements, but its scan work grew with catalog size.

## Source-inferred risks not tested here

- [Article deletion](source/lib/conduit/articles.ex) deletes the row without a matching live-room revocation broadcast. Existing editors may keep a room until another operation reveals deletion. This was identified by code inspection; no socket-after-delete probe was run.
- [Export completion](source/lib/conduit/exports.ex) reads articles and comment counts in separate statements inside a default transaction. PostgreSQL `READ COMMITTED` can give those statements different snapshots under concurrent writes. No concurrency test was run.
- Room presence and the admission cap are process-local. The measured production topology has one app container; multi-instance behavior remains outside this condition.

The frozen standard gates, transcript, measurements, and source remain unchanged by this review.
