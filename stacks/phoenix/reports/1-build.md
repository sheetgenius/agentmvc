**Status:** DONE.

**Gate result:** All 13 Hurl files passed. Formatter and warnings-as-errors compile passed. Final `bin/check` exit code: 0.

**Libraries:** Phoenix routes the API; Bandit serves HTTP; Jason handles JSON; Ecto SQL and Postgrex persist data in PostgreSQL; Bcrypt hashes passwords; Joken signs and validates JWTs; CORSPlug handles browser preflights.

**Code map:**

- [AGENTS.md](../1-build/AGENTS.md) — project guidance.
- [README.md](../1-build/README.md) — run instructions, architecture, and spec choices.
- [.formatter.exs](../1-build/.formatter.exs) — formatter inputs.
- [.gitignore](../1-build/.gitignore) — local build and cache exclusions.
- [bin/check](../1-build/bin/check) — fresh database and full acceptance gate.
- [compose.yml](../1-build/compose.yml) — PostgreSQL and app containers.
- [mix.exs](../1-build/mix.exs) — application dependencies.
- [mix.lock](../1-build/mix.lock) — resolved dependencies.
- [config/config.exs](../1-build/config/config.exs) — shared configuration.
- [config/dev.exs](../1-build/config/dev.exs) — development database and endpoint.
- [config/prod.exs](../1-build/config/prod.exs) — production HTTPS setting.
- [config/runtime.exs](../1-build/config/runtime.exs) — port and production secrets.
- [lib/conduit/application.ex](../1-build/lib/conduit/application.ex) — supervision tree.
- [lib/conduit/repo.ex](../1-build/lib/conduit/repo.ex) — PostgreSQL repository.
- [lib/conduit/accounts.ex](../1-build/lib/conduit/accounts.ex) — credentials, tokens, and follows.
- [lib/conduit/accounts/user.ex](../1-build/lib/conduit/accounts/user.ex) — user schema and validation.
- [lib/conduit/content.ex](../1-build/lib/conduit/content.ex) — article, comment, favorite, feed, and tag operations.
- [lib/conduit/content/article.ex](../1-build/lib/conduit/content/article.ex) — article schema, validation, and slugs.
- [lib/conduit/content/comment.ex](../1-build/lib/conduit/content/comment.ex) — comment schema and validation.
- [lib/conduit_web.ex](../1-build/lib/conduit_web.ex) — Phoenix router and controller setup.
- [lib/conduit_web/endpoint.ex](../1-build/lib/conduit_web/endpoint.ex) — HTTP plugs.
- [lib/conduit_web/router.ex](../1-build/lib/conduit_web/router.ex) — API routes.
- [lib/conduit_web/auth.ex](../1-build/lib/conduit_web/auth.ex) — optional and required authentication.
- [lib/conduit_web/presenter.ex](../1-build/lib/conduit_web/presenter.ex) — RealWorld response shapes.
- [lib/conduit_web/controllers/user_controller.ex](../1-build/lib/conduit_web/controllers/user_controller.ex) — registration, login, and current user.
- [lib/conduit_web/controllers/profile_controller.ex](../1-build/lib/conduit_web/controllers/profile_controller.ex) — profiles and follows.
- [lib/conduit_web/controllers/article_controller.ex](../1-build/lib/conduit_web/controllers/article_controller.ex) — articles, feed, favorites, and tags.
- [lib/conduit_web/controllers/comment_controller.ex](../1-build/lib/conduit_web/controllers/comment_controller.ex) — comments.
- [lib/conduit_web/controllers/fallback_controller.ex](../1-build/lib/conduit_web/controllers/fallback_controller.ex) — validation and resource errors.
- [lib/conduit_web/controllers/error_json.ex](../1-build/lib/conduit_web/controllers/error_json.ex) — framework errors.
- [priv/repo/migrations/.formatter.exs](../1-build/priv/repo/migrations/.formatter.exs) — migration formatting.
- [priv/repo/migrations/20260927021412_create_conduit.exs](../1-build/priv/repo/migrations/20260927021412_create_conduit.exs) — tables, keys, and indexes.

**What you did toward the goal:**

- **Pass 1:** Removed unused generator features and dependencies, added CORS and expiring JWT claims, and reduced configuration to what the API uses.
- **Pass 2:** Declared follows and favorites as Ecto associations and removed duplicate article lookup and list rendering code.
- **Pass 3:** Tightened malformed token handling, validation messages, CORS settings, and comment ID handling. Stopped after the required third fully green pass.

**Spec decisions:** Slugs have a random suffix; article tags keep input order while the global list is distinct and sorted. Follow and favorite operations are idempotent, and self follow is allowed. JWTs expire after two hours. Lists default to limit 20 and offset 0 and omit bodies. Deletes return 204; invalid comment IDs return 404.

**Run counts:** `bin/check`: 5 runs, with 4 fully green. Narrower Hurl runs: 0. Local formatter/compile preparation commands: 8. Compile failures: 2; build failures: 0.

**Friction log:**

- The generator required confirmation for the existing directory; the first invocation stopped at its prompt.
- A password binding failed compilation because of Elixir expression scope.
- Removing generator code exposed a stale `code_reloading?` call, causing the second compile failure.
- A null `tagList` reached PostgreSQL’s non-null constraint; explicit changeset validation fixed the initial 12/13 Hurl result.

**Agent-friendliness notes:** Phoenix routes and Ecto schemas make the API and relationships easy to locate. The generated scaffold contained substantial unused surface, and the Docker-only toolchain slowed feedback. The presenter performs per-article relationship and count queries, which is simple to read but could cost more at larger scale.