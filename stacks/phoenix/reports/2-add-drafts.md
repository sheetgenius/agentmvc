**Status:** DONE.

**Gate result:** All 15 Hurl files passed. Formatter and warning-free compile passed. Final `bin/check` exit code: 0.

**Where the feature landed:**

- [README.md](../2-add-drafts/README.md): documented routes, rules, and spec choices.
- [content.ex](../2-add-drafts/lib/conduit/content.ex): added draft visibility, publishing, edit conflicts, and published-only queries.
- [article.ex](../2-add-drafts/lib/conduit/content/article.ex): added lifecycle fields, validation, and optimistic locking.
- [article_controller.ex](../2-add-drafts/lib/conduit_web/controllers/article_controller.ex): added draft and publish actions and stale-edit responses.
- [comment_controller.ex](../2-add-drafts/lib/conduit_web/controllers/comment_controller.ex): applied draft visibility to comment routes.
- [fallback_controller.ex](../2-add-drafts/lib/conduit_web/controllers/fallback_controller.ex): added draft errors and fixed enum error rendering.
- [presenter.ex](../2-add-drafts/lib/conduit_web/presenter.ex): included the three new article fields.
- [router.ex](../2-add-drafts/lib/conduit_web/router.ex): added the drafts and publish routes.
- [20260927030000_add_article_drafts.exs](../2-add-drafts/priv/repo/migrations/20260927030000_add_article_drafts.exs): added columns and backfilled publication times for existing articles.

**Passes:** Pass 1 gave public lists, feeds, and tags one published-article query. Pass 2 backfilled `publishedAt` for pre-feature articles. Each pass ended with a green `bin/check`; I stopped after the allowed two passes.

**Spec decisions:** Article updates ignore `status`; publishing is the only status transition. An author may list their draft’s comments, which are empty. Pre-feature articles inherit their creation time as `publishedAt`.

**Run counts:** `bin/check`: 4 runs, including the final green run. Narrower Hurl runs: 2. Compile or build failures: 0.

**Friction log:**

- Invalid status initially returned 500 because shared error rendering eagerly stringified Ecto enum metadata.
- Draft visibility affected article, comment, and favorite routes; the shared context lookup kept it consistent.
- Edit conflicts required a current-article response while Ecto’s optimistic lock handled concurrent writes.
- `bin/check` tears down its stack, so diagnosing the 500 required a temporary database and server.

**Agent-friendliness notes:** Phoenix routing and Ecto changesets made the domain rules easy to locate. The shared fallback controller exposed one cross-cutting error-rendering issue; the full Hurl gate caught it.