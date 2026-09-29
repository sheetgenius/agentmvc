# Final Go/Python lane expert review

Reviewer source inspection: 2026-09-30. Scope: original final sources under
`stacks/{go,python}/8-live-editing`. Originals and frozen fixtures were not edited.
No Docker, application HTTP requests, load tests, or measured one-shot workspaces
were used in this review. Existing live diagnostic outcomes below were supplied
by the coordinating reviewer; additional findings are explicitly pending probes.
These findings justify small unscored reference changes, not framework rewrites.

## Existing reproduced failures

### Python: malformed owner update accepted

- Evidence: `results/lanes/python/8-live-editing/reviewer-parity/results.json`,
  `malformed_owner`: `{"article":[]}` reportedly returns 200 and increments revision.
  Existing common diagnostic totals: 20/21 contract, 3/3 quality.
- Source: `stacks/python/8-live-editing/conduit/articles.py`, `ArticleChangesBody`
  and `update_article` (approximately lines 100 and 179).
- Contract: `spec/features/drafts/drafts.md:65-81`, especially the ordered
  authentication, visibility, ownership, revision, field-validation rules.
- Minimal fix: remove the typed payload parameter on this route. After loading
  and locking the visible article and checking ownership, parse JSON and require
  a dictionary envelope with a dictionary `article`. Convert via
  `ArticleChanges.model_validate(...).model_dump(exclude_unset=True)` so unknown
  normal-update fields remain ignored. Keep revision checks before field checks.
  A route-level schema shape validator would run too early and risk changing
  the required authorization/error precedence. Do not apply arbitrary input
  keys through the existing `setattr` loop.
- Verify: malformed object as anonymous/stranger/missing article/owner returns
  401/403/404/422. Owner rejection preserves the whole article including revision
  and timestamps. Stale revision with invalid body still returns 409 first.

### Python: favorited filter narrows the global favorite count

- Evidence: coordinating review reports 38/48 favorite diagnostics for Python,
  versus Go's 48/48. Two favorites are reported as one under `favorited=`.
- Source: `conduit/articles.py:list_articles` filters `favorites__username`
  before `conduit/models.py:ArticleQuerySet.with_viewer` adds `Count("favorites")`.
- Contract: `spec/docs/endpoints.md:102-126` defines favorite membership as an
  article filter; `spec/docs/api-response-format.md:60-103` retains each article's
  `favoritesCount` and viewer-specific `favorited` representation.
- Minimal fix: use a membership subquery:
  `articles.filter(pk__in=Article.favorites.through.objects.filter(user__username=favorited).values("article_id"))`.
  Keep the existing count annotation. `distinct=True` does not recover rows
  removed by the earlier favorites join.
- Verify: two users favorite one article; filter by either user and inspect as
  anonymous, either favoriter, and a third viewer. Global count remains two;
  viewer flags remain independent. Repeat after one favorite is removed.

Neither reported failure is explained by a confirmed reviewer defect.

## Additional source findings: HTTP reproduction pending

### Go: shared stale nonpositive integers return 422

- Source: `stacks/go/8-live-editing/internal/conduit/shares.go:150-155` rejects
  `revision < 1` before comparing against the current revision.
- Contract: `spec/features/live-editing/live-editing.md:21-23` requires the same
  revision rule; `spec/features/drafts/drafts.md:65-74` distinguishes any unequal
  integer (409) from a noninteger (422). Normal Go owner edits implement this.
- Minimal fix: decode a `*int` to reject missing/null/noninteger values, remove
  the positivity restriction, then compare revisions.
- Probe: independently create each case; submit valid title/body with revision
  zero and negative one. Expect 409, `errors.revision == ["is stale"]`, the current
  shared article, and unchanged full/shared reads.

### Go: extra shared envelope keys ignored

- Source: `internal/conduit/shares.go:updateSharedArticle` uses
  `internal/conduit/http.go:decodeObject`, which ignores other outer keys.
- Contract wording: `spec/features/live-editing/live-editing.md:21` says
  "accepts exactly" the specified envelope; the frozen Hurl extra-field test
  (`spec/features/live-editing/hurl/live-editing.hurl:83-89`) checks an extra
  *inner* field. Outer-key rejection is therefore treated conservatively as
  a **quality diagnostic**, not an added frozen acceptance requirement.
- Minimal fix if strict envelope behavior is desired: shared-route-specific
  exact outer/inner key validation after share authorization. Keep ordinary
  routes' behavior unchanged.
- Probe: valid current article fields plus outer `extra: true`; desired 422
  with structured errors and no mutation. Independently created article avoids
  stale revisions hiding whether extra keys were accepted.

### Go: potential lost disjoint edits when revision omitted

- Source: `internal/conduit/articles.go:updateArticle`, approximately lines
  188-237, reads an unlocked article then updates every text field from that
  snapshot, even fields absent from the submitted payload.
- Hypothesis: two concurrent requests changing different fields without a
  revision can overwrite each other's untouched fields. Not reproduced here.
- Relevant behavior: `spec/docs/endpoints.md:165-183` defines optional update
  fields; `spec/features/drafts/drafts.md:67` preserves revision-omitted updates.
  Neither explicitly specifies concurrency semantics for omitted revisions,
  so this is a quality/concurrency concern, not a declared frozen failure.
- Minimal robust fix: load and lock the article inside the transaction before
  authorization, revision comparison and applying changes. Alternatively update
  only supplied columns. Verify with a barrier-controlled disjoint-update test.

## Small performance opportunities (source confirmed, gains unmeasured)

- **Go list body reads:** `internal/conduit/articles.go:articleList` selects
  whole articles before `articleViews(..., false)` omits bodies. Add
  `ExcludeColumn("body")` to the list select. Verify equivalent JSON and inspect
  generated SELECT. Relevant intent: `spec/docs/api-response-format.md:62-67`
  explicitly omits list bodies for performance; drafts use the same shape
  (`spec/features/drafts/drafts.md:57-60`). Python already defers body.
- **Python authenticated comment N+1:** `conduit/articles.py:comment_data` calls
  `profile_data(comment.author, current)` for each row; `select_related("author")`
  does not batch `current.following.filter(...).exists()`. Annotate the existing
  article-style `Exists` expression for author following on comments and pass
  its boolean to `profile_data`. Verify stable query count for 1 versus 20
  comments and correct following flags. This concerns efficiency of the comment
  author shape in `spec/docs/api-response-format.md:106-122`, not a shape failure.

## Supplemental probe

`tools/lane_share_probe.py` uses the common HTTP `Client`, identical requests
for all final applications, separate articles/shares per case, one positive
baseline and the three cases above. It does not start services. Results export
only fixed labels, status/count integers, booleans and type names; no origin,
URLs, request/response bodies, credentials, share keys, slugs, or titles.
Setup failures retain safe structured observations. Contract and quality totals
are separate; quality failures affect exit status only with `--strict-diagnostics`.
No real HTTP execution was performed while authoring it. Offline validation:
Python syntax parsed; a conforming fake client passed every case; a fake client
with the three suspected Go deviations failed exactly those three cases.
The fake-client checks also verified four independent articles and absence of
sentinel credentials, slugs, article text and origins in serialized results.

## Closing review: published reference outcomes

The initial findings above describe preserved originals. They do not override
later reference evidence. The following statuses were read directly from each
published reference's `verification.json`, `size.json`, and, where present,
`reviewer-parity/{results,share-boundary}.json`:

| Reference | Owned tokens | Independent development / production | Supplemental review |
| --- | ---: | --- | --- |
| `results/lanes/go/8-live-editing/reference-1` | 14,249 | pass / pass | parity and shared boundary pass |
| `results/lanes/python/8-live-editing/reference-1` | 8,429 | pass / pass | parity and shared boundary pass |
| `results/one-shot-v2-go-expert/pilot-1/reference-1` | 12,846 | pass / pass | common 21/21 contract + 3/3 quality; favorites 48/48; shared boundary pass |
| `results/one-shot-v2-python-expert/pilot-1/reference-1` | 9,015 | pass / fail | production failure preserved; replacement pending at review time |

These are unscored repaired references. Token counts describe owned source size,
not measured coding effort or proof of broad performance superiority. The Python
one-shot reference-1 production failure must not be presented as a passing final
candidate. Reference-2 had only its metadata published during this review.

### Go one-shot reference-1: repair and framework verdict

Read source root:
`results/one-shot-v2-go-expert/pilot-1/reference-1/source`.

- `internal/conduit/app.go:decodeShared/decodeBody` validates the exact outer
  envelope and trailing JSON; `integer` uses `*int`, preserving stale zero and
  negative integers while rejecting null. Focused input tests cover the repair.
- `internal/conduit/articles.go:saveArticle` is one author/share update rule,
  reads the current row with `FOR UPDATE`, applies changes, commits, then
  broadcasts. This removes the earlier original-lane disjoint-update concern
  from this independently designed implementation.
- `internal/conduit/login_limits.go` reserves in-flight attempts before password
  verification; deterministic concurrency/expiry tests exercise its limit. It
  is process local, consistent with the one-instance deployment, and resets
  across restarts.
- `internal/conduit/exports.go` inserts export and River job in one transaction;
  snapshot content uses one SQL statement and completion is conditional on
  pending status. These are compact, direct uses of database/queue guarantees.

No additional acceptance blocker was established by this source review.
The implementation is idiomatic **Chi + database/sql + River**, with parameterized
SQL making relationships, aggregates and locking explicit. Its use of Huma is
limited to health and tags; Bun mainly supplies database/transaction wrappers
and the tags query. It should not be characterized as a full test of typed Huma
operations or a Bun ORM-centered product. A future typed-Huma comparison would
be a separate experiment, not a necessary correctness repair.

Two performance limitations are visible in source but their workload impact is
**unmeasured**: the single `rooms.mu` spans database work for edits, publishing,
link management and subscription, serializing unrelated articles; `viewSelect`
still fetches body on list routes before `scanView(..., false)` removes it.
Neither is a measured throughput failure. A focused future reference could
use article-scoped room locking and body-free list projections, with concurrency
tests preserving admission and revision ordering. No load or runtime experiment
was performed by this reviewer.

### Python one-shot reference-2: pending repair source review

The coordinator expressly authorized reading only the current repair workspace
for this follow-up. Inspected
`.work/lanes/python-one-shot-reference-2/app/conduit/live.py` and
`tests/test_live_ordering.py`; no source was edited and no test was run here.

The presence repair addresses the reported scheduling race concretely:
`ready`, presence, updates and revocation use a per-client send lock; presence
reads current membership after obtaining that lock; the newly ready client is
also refreshed. Room membership locks are released before transport awaits.
Pending updates retain the greatest revision, and the admitted guard prevents
an update following revocation. Four deterministic tests control delayed ready,
overlapping leaves, pending-update ordering and revocation during ready. These
tests target observable scheduling failures rather than duplicating helpers.
No additional fix was identified. Publication and independent production/browser
verification remain required evidence; source inspection alone is not a pass.

**Coordinator follow-up:** reference-2 was subsequently published at
`results/one-shot-v2-python-expert/pilot-1/reference-2/source` (9,058 owned tokens).
Its independent development and production gates pass, as do the common,
favorites and shared-boundary probes recorded beside that source. This confirms
the checks on the published repair; reference-1's failure remains preserved.

### Selection and reading entry points

For a compact, framework-led current reference, Python final-8 reference-1 is
the strongest already-verified choice in these artifacts: 8,429 owned tokens,
Django model/query/transaction machinery, Ninja routing, Channels sockets and
Procrastinate jobs. Begin with its `conduit/models.py`, `articles.py`, `sharing.py`,
`live.py` and `tasks.py`. Its density is observed for this product and these
checks, not a universal language result.

For explicit SQL, typed Go response structures, and River integration, Go
one-shot reference-1 is a useful verified reference. Begin with
`internal/conduit/articles.go:saveArticle`, `shares.go`, `login_limits.go`,
`exports.go`, then `cmd/server/main.go` for actual framework boundaries.
Do not infer a Huma productivity result from this candidate's size.
After Python one-shot reference-2 independently passes, its `domain.py`,
`api.py`, `live.py` and `tests/test_live_ordering.py` are the natural entry points
for comparing its consolidated rule ownership with final-8 Python.
