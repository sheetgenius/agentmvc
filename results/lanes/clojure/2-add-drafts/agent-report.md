**Status:** DONE.

**Gate result:** 15/15 Hurl files passed; formatter and linter clean; final `bin/check` exit code 0.

**Where the feature landed:**

- [articles.clj](/work/app/src/conduit/articles.clj): added draft visibility, publishing, draft lists, and atomic revision checks.
- [http.clj](/work/app/src/conduit/http.clj): added draft and publish routes and the current article in conflict responses.
- [002-drafts.up.sql](/work/app/resources/migrations/002-drafts.up.sql): added lifecycle columns and backfilled existing articles.
- [002-drafts.down.sql](/work/app/resources/migrations/002-drafts.down.sql): added migration rollback.
- [README.md](/work/app/README.md): documented routes, rules, and spec choices.

**Passes:** Pass 1 put the shared published-article check in one place. Pass 2 made concurrent deletion return `404` during update or publish. Each pass ended with a green `bin/check`; stopped after two passes.

**Spec decisions:** Existing articles receive their creation time as `publishedAt`. Updates ignore `status`, and even an update with no changed fields increments `revision`. Authors may read a draft’s empty comments list; favoriting and unfavoriting a draft both return `422`.

**Run counts:** `bin/check`: 3, all green. Narrower runs: 3 formatter runs, no narrower test runs. Compile or build failures: 0.

**Friction log:**

- Draft visibility touched article, comment, and favorite routes; the shared lookup keeps that rule together.
- Edit conflicts needed an atomic database revision check and the current article in the `409` response.
- Concurrent deletion needed separate handling from a stale revision.
- `git status` was unavailable because the local `xcrun` developer path was invalid.

**Agent-friendliness notes:** Reitit routes and the concentrated article namespace made the feature easy to locate. The explicit SQL queries made visibility rules easy to inspect, but required checking each list and nested route.