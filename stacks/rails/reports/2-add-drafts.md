**Status:** DONE.

**Gate result:** 15/15 Hurl files passed. Formatter and linter are clean (RuboCop: 0 offenses). Final `bin/check` exit code: 0.

**Where the feature landed:**

- [app/models/article.rb](../2-add-drafts/app/models/article.rb) — defines draft visibility, publication, status validation, and revision changes.
- [app/controllers/application_controller.rb](../2-add-drafts/app/controllers/application_controller.rb) — shares the draft interaction error.
- [app/controllers/api/articles_controller.rb](../2-add-drafts/app/controllers/api/articles_controller.rb) — adds draft listing, publishing, visibility, and locked revision checks.
- [app/controllers/api/comments_controller.rb](../2-add-drafts/app/controllers/api/comments_controller.rb) — hides others’ drafts and blocks comments on them.
- [app/controllers/api/tags_controller.rb](../2-add-drafts/app/controllers/api/tags_controller.rb) — lists tags on published articles.
- [app/views/api/articles/_article.json.jbuilder](../2-add-drafts/app/views/api/articles/_article.json.jbuilder) — adds lifecycle fields to article responses.
- [app/views/api/articles/conflict.json.jbuilder](../2-add-drafts/app/views/api/articles/conflict.json.jbuilder) — returns the current article on a stale edit.
- [config/routes.rb](../2-add-drafts/config/routes.rb) — adds drafts and publish routes.
- [db/migrate/20260927000001_add_drafts_to_articles.rb](../2-add-drafts/db/migrate/20260927000001_add_drafts_to_articles.rb) — adds status, publication time, and revision columns.
- [db/schema.rb](../2-add-drafts/db/schema.rb) — records the new schema.
- [README.md](../2-add-drafts/README.md) — documents routes, rules, and spec choices.

**Passes:** Pass 1 consolidated the repeated draft interaction error; the full gate stayed green. Pass 2 found no worthwhile further cleanup, and the final gate was green.

**Spec decisions:** Draft-only and orphaned tags are omitted from `/api/tags`. Authors can read their draft’s empty comments list. On protected comment and favorite routes without a token, authentication takes precedence over draft visibility, as required by the original suite.

**Run counts:** `bin/check`: 3 runs, all green; narrower runs: 0; compile or build failures: 0.

**Friction log:**

- The original authentication tests and draft visibility prose impose different error precedence; the tested authentication behavior determined the protected-route choice.
- Edit conflicts required a row lock so concurrent updates cannot both accept the same revision.
- Draft-only tags changed the earlier orphan-tag behavior, requiring an explicit README choice.

**Agent-friendliness notes:** Rails scopes, enums, callbacks, and Jbuilder kept the domain rules close to their conventional locations. The main difficulty was reconciling error precedence across the original and feature suites.