## **Status:** DONE

## **Gate result:** 13/13 Hurl files passed. The Omakase formatter and linter check is clean. Final `bin/check` exit code: **0**.

## **Libraries:**

- Rails — API routing, models, validation, migrations, and views.
- `pg` — PostgreSQL connection.
- Puma — HTTP server.
- Bootsnap — faster boot.
- `bcrypt` — hashed passwords.
- `jwt` — signed authentication tokens.
- Jbuilder — JSON responses.
- `rack-cors` — CORS requests.
- Rails Omakase RuboCop — default style and lint check.

## **Code map:**

- [`.bundle/config`](../1-build/.bundle/config) — local gem installation path.
- [`.rubocop.yml`](../1-build/.rubocop.yml) — default Omakase rules.
- [`.ruby-version`](../1-build/.ruby-version) — Ruby version.
- [`Gemfile`](../1-build/Gemfile) — direct dependencies.
- [`Gemfile.lock`](../1-build/Gemfile.lock) — resolved dependencies.
- [`README.md`](../1-build/README.md) — run instructions, code layout, and spec choices.
- [`Rakefile`](../1-build/Rakefile) — Rails tasks.
- [`application_controller.rb`](../1-build/app/controllers/application_controller.rb) — token authentication and common errors.
- [`articles_controller.rb`](../1-build/app/controllers/api/articles_controller.rb) — articles, feed, tags on articles, and favorites.
- [`comments_controller.rb`](../1-build/app/controllers/api/comments_controller.rb) — article comments.
- [`profiles_controller.rb`](../1-build/app/controllers/api/profiles_controller.rb) — profiles and follows.
- [`sessions_controller.rb`](../1-build/app/controllers/api/sessions_controller.rb) — login.
- [`tags_controller.rb`](../1-build/app/controllers/api/tags_controller.rb) — tag list.
- [`users_controller.rb`](../1-build/app/controllers/api/users_controller.rb) — registration and current user.
- [`application_record.rb`](../1-build/app/models/application_record.rb) — Active Record base.
- [`article.rb`](../1-build/app/models/article.rb) — article relationships, filters, validation, and slugs.
- [`article_tag.rb`](../1-build/app/models/article_tag.rb) — article–tag relationship.
- [`comment.rb`](../1-build/app/models/comment.rb) — comment validation and relationships.
- [`favorite.rb`](../1-build/app/models/favorite.rb) — user–article favorite.
- [`follow.rb`](../1-build/app/models/follow.rb) — user–user follow.
- [`tag.rb`](../1-build/app/models/tag.rb) — tag validation and relationships.
- [`user.rb`](../1-build/app/models/user.rb) — user relationships, password hashing, and tokens.
- [`articles/_article.json.jbuilder`](../1-build/app/views/api/articles/_article.json.jbuilder) — article JSON shape.
- [`articles/index.json.jbuilder`](../1-build/app/views/api/articles/index.json.jbuilder) — article list response.
- [`articles/show.json.jbuilder`](../1-build/app/views/api/articles/show.json.jbuilder) — single article response.
- [`comments/_comment.json.jbuilder`](../1-build/app/views/api/comments/_comment.json.jbuilder) — comment JSON shape.
- [`comments/index.json.jbuilder`](../1-build/app/views/api/comments/index.json.jbuilder) — comment list response.
- [`comments/show.json.jbuilder`](../1-build/app/views/api/comments/show.json.jbuilder) — single comment response.
- [`profiles/_profile.json.jbuilder`](../1-build/app/views/api/profiles/_profile.json.jbuilder) — profile JSON shape.
- [`profiles/show.json.jbuilder`](../1-build/app/views/api/profiles/show.json.jbuilder) — profile response.
- [`tags/index.json.jbuilder`](../1-build/app/views/api/tags/index.json.jbuilder) — tag response.
- [`users/show.json.jbuilder`](../1-build/app/views/api/users/show.json.jbuilder) — authenticated user response.
- [`bin/check`](../1-build/bin/check) — fresh database, server, Hurl, and RuboCop gate.
- [`bin/rails`](../1-build/bin/rails) — Rails command entry point.
- [`bin/rubocop`](../1-build/bin/rubocop) — RuboCop command entry point.
- [`compose.yaml`](../1-build/compose.yaml) — PostgreSQL service.
- [`config.ru`](../1-build/config.ru) — Rack entry point.
- [`config/application.rb`](../1-build/config/application.rb) — API-only Rails setup.
- [`config/boot.rb`](../1-build/config/boot.rb) — Bundler and Bootsnap setup.
- [`config/database.yml`](../1-build/config/database.yml) — PostgreSQL environments.
- [`config/environment.rb`](../1-build/config/environment.rb) — Rails initialization.
- [`development.rb`](../1-build/config/environments/development.rb) — development settings and Docker host access.
- [`production.rb`](../1-build/config/environments/production.rb) — production settings.
- [`test.rb`](../1-build/config/environments/test.rb) — test environment settings.
- [`cors.rb`](../1-build/config/initializers/cors.rb) — API CORS policy.
- [`filter_parameter_logging.rb`](../1-build/config/initializers/filter_parameter_logging.rb) — sensitive log filtering.
- [`config/puma.rb`](../1-build/config/puma.rb) — server threads and port.
- [`config/routes.rb`](../1-build/config/routes.rb) — RealWorld endpoints.
- [`create_conduit.rb`](../1-build/db/migrate/20260927000000_create_conduit.rb) — database tables and constraints.
- [`db/schema.rb`](../1-build/db/schema.rb) — Rails-generated schema used for database preparation.

## **What you did toward the goal:**

- **Build:** Generated Rails, saved the untouched `.scaffold/`, and implemented the API.
- **Pass 1:** Removed unused generator deployment, CI, and framework files; shortened configuration.
- **Pass 2:** Made tag order explicit, validated tag input, made article filters composable, and removed an empty controller layer.
- **Pass 3:** Consolidated registration and current-user actions into the conventional `UsersController`; clarified follow association names. Stopped at the requested three-pass limit. Every pass ended with a green `bin/check`.

## **Spec decisions:** Slugs include a random suffix; tokens expire after 30 days; tags remain listed after their last article is deleted; email and username uniqueness are case sensitive. Empty bio and image values become `null`. The README records these choices.

## **Run counts:** `bin/check`: **8** runs, with the final four fully green. Narrower RuboCop runs: **2**. Compile or build failures: **0**.

## **Friction log:**

- Rails blocked `host.docker.internal` requests with 403 until the development host was allowed.
- Docker reported PostgreSQL healthy before the host connection was consistently ready; schema preparation now retries.
- The singular `/api/user` resource initially routed to the plural controller, exposing a missing current-user action.
- RuboCop tried to write its cache under a read-only home directory; `bin/check` now uses `tmp/`.
- The generator supplied deployment and CI files that referred to unused tools; they were removed.

## **Agent-friendliness notes:** Rails associations, routes, and Jbuilder partials make most domain relationships and response shapes easy to locate. Generator output and the singular-resource routing convention required the most careful reading.