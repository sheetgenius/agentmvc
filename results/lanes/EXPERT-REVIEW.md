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
