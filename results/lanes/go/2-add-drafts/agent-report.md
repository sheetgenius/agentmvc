**Status:** DONE.

**Gate result:** 15/15 Hurl files passed. Formatter and linter clean. Final `bin/check` exit code: 0.

**Where the feature landed:**

- [articles.go](/work/app/internal/conduit/articles.go): draft creation, visibility, publishing, lists, tags, and revision checks.
- [comments.go](/work/app/internal/conduit/comments.go): shared draft visibility and comment restriction.
- [http.go](/work/app/internal/conduit/http.go): new routes and conflict response shape.
- [models.go](/work/app/internal/conduit/models.go): lifecycle fields in records and responses.
- [users.go](/work/app/internal/conduit/users.go): adapted error construction to the extended response type.
- [00002_drafts.sql](/work/app/internal/platform/migrations/00002_drafts.sql): schema fields and existing article backfill.
- [README.md](/work/app/README.md): routes, rules, and spec choices.

**Passes:** Pass 1 preserved last write wins for updates without a revision and removed a redundant comment helper. Pass 2 made article and tag writes transactional and fixed `status: null` validation. Stopped after two passes and a final green gate.

**Spec decisions:** Updates ignore `status`; publishing refreshes `updatedAt`. Existing articles receive their creation time as `publishedAt`. Authors can list their drafts’ comments, which are empty because drafts cannot receive comments.

**Run counts:** `bin/check`: 4; narrower test runs: 0; compile or build failures: 0.

**Friction log:**

- Draft visibility spans article, comment, favorite, and publish routes, so it needed one shared lookup.
- A stale revision must return the current article alongside the error; the existing error response held only errors.
- Concurrent article and tag edits needed one transaction to keep a stale edit from changing tags afterward.
- Go’s JSON decoder leaves a prefilled string unchanged for `null`, which exposed a status validation edge case.

**Agent-friendliness notes:** Chi’s central routes, Bun’s models and transactions, and Goose’s numbered migrations made the rules easy to locate. The fixed `bin/check` harness made full behavior verification quick.