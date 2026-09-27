**Status:** DONE.

**Gate result:** Final `bin/check` passed 15/15 Hurl acceptance files, formatting, and compilation with warnings treated as errors; exit code 0. Final `bin/check-production` passed 15/15 acceptance files and 13/13 security checks; exit code 0.

**Code map:**

- [README.md](../6-polish/README.md): domain map, behavior, and run instructions.
- ENVIRONMENT.md: toolchain and sandbox instructions.
- [AGENTS.md](../6-polish/AGENTS.md): repository working conventions.
- [mix.exs](../6-polish/mix.exs): application and dependencies.
- [mix.lock](../6-polish/mix.lock): locked dependency versions.
- [.formatter.exs](../6-polish/.formatter.exs): Elixir formatter scope.
- [.gitignore](../6-polish/.gitignore): local build and cache exclusions.
- .dockerignore: production build context.
- [Dockerfile](../6-polish/Dockerfile): production release image.
- [compose.yml](../6-polish/compose.yml): local app and PostgreSQL services.
- [bin/check](../6-polish/bin/check): acceptance, formatting, and compile gate.
- [bin/check-production](../6-polish/bin/check-production): production image and security gate.
- [config/config.exs](../6-polish/config/config.exs): shared Phoenix configuration.
- [config/dev.exs](../6-polish/config/dev.exs): development database and endpoint settings.
- [config/prod.exs](../6-polish/config/prod.exs): production logging.
- [config/runtime.exs](../6-polish/config/runtime.exs): runtime port, database, and secret configuration.
- [lib/conduit_web.ex](../6-polish/lib/conduit_web.ex): Phoenix router and controller setup.
- [lib/conduit/application.ex](../6-polish/lib/conduit/application.ex): supervision tree.
- [lib/conduit/repo.ex](../6-polish/lib/conduit/repo.ex): PostgreSQL repository.
- [lib/conduit/release.ex](../6-polish/lib/conduit/release.ex): release migrations.
- [lib/conduit/accounts.ex](../6-polish/lib/conduit/accounts.ex): credentials, profiles, tokens, and follows.
- [lib/conduit/accounts/user.ex](../6-polish/lib/conduit/accounts/user.ex): user schema, validation, and password hashing.
- [lib/conduit/content.ex](../6-polish/lib/conduit/content.ex): article, comment, favorite, and tag operations.
- [lib/conduit/content/article.ex](../6-polish/lib/conduit/content/article.ex): article schema, validation, slugs, and revisions.
- [lib/conduit/content/comment.ex](../6-polish/lib/conduit/content/comment.ex): comment schema and validation.
- [lib/conduit_web/endpoint.ex](../6-polish/lib/conduit_web/endpoint.ex): HTTP plugs.
- [lib/conduit_web/router.ex](../6-polish/lib/conduit_web/router.ex): API routes and authentication pipelines.
- [lib/conduit_web/auth.ex](../6-polish/lib/conduit_web/auth.ex): token authentication plug.
- [lib/conduit_web/login_limiter.ex](../6-polish/lib/conduit_web/login_limiter.ex): login rate limiter.
- [lib/conduit_web/presenter.ex](../6-polish/lib/conduit_web/presenter.ex): response JSON shapes.
- [lib/conduit_web/controllers/article_controller.ex](../6-polish/lib/conduit_web/controllers/article_controller.ex): article HTTP actions.
- [lib/conduit_web/controllers/comment_controller.ex](../6-polish/lib/conduit_web/controllers/comment_controller.ex): comment HTTP actions.
- [lib/conduit_web/controllers/user_controller.ex](../6-polish/lib/conduit_web/controllers/user_controller.ex): registration, login, and account HTTP actions.
- [lib/conduit_web/controllers/profile_controller.ex](../6-polish/lib/conduit_web/controllers/profile_controller.ex): profile and follow HTTP actions.
- [lib/conduit_web/controllers/fallback_controller.ex](../6-polish/lib/conduit_web/controllers/fallback_controller.ex): domain and changeset error responses.
- [lib/conduit_web/controllers/error_json.ex](../6-polish/lib/conduit_web/controllers/error_json.ex): Phoenix error JSON.
- [priv/repo/migrations/20260927021412_create_conduit.exs](../6-polish/priv/repo/migrations/20260927021412_create_conduit.exs): core tables and indexes.
- [priv/repo/migrations/20260927030000_add_article_drafts.exs](../6-polish/priv/repo/migrations/20260927030000_add_article_drafts.exs): draft and revision columns.
- [priv/repo/migrations/20260927040000_index_favorites_by_article.exs](../6-polish/priv/repo/migrations/20260927040000_index_favorites_by_article.exs): favorite count index.
- [priv/repo/migrations/.formatter.exs](../6-polish/priv/repo/migrations/.formatter.exs): migration formatter scope.

**What each pass changed:**

1. Moved article and comment ownership checks into `Content`, leaving controllers focused on HTTP.
2. Put shared identity and password rules in one place in the user schema, and moved profile lookup results into `Accounts`.
3. Reused the known author when creating comments and made comment listing easier to read. Stopped at the three pass limit and updated the README to match.

**Run counts:** 3 `bin/check` runs; 3 `bin/check-production` runs; 3 narrower formatter runs; 0 build failures.

**Friction log:**

- Elixir is Docker only, so even formatting required a container run.
- Ownership checks were embedded in controllers, which obscured where that rule lived.
- Existing article list query batching constrained changes to response shaping; preserving its query behavior mattered.
- The acceptance and security suites specify precise error responses, so validation cleanup required both gates.

**Agent-friendliness notes:** Ecto schemas, Phoenix routes, and the two contexts make most rules easy to locate. The Docker only toolchain and some database reads initiated during presentation make a cold read slower.