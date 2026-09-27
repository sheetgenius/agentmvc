## Status: DONE

## Gate result

Final runs: **15/15** Hurl acceptance files, **13/13** production security checks, and **41 files inspected with no RuboCop offenses**. `bin/check` and `bin/check-production` both exited **0**.

## Code map

- ENVIRONMENT.md — Stack, toolchain, and workspace constraints.
- [README.md](../6-polish/README.md) — Setup, behavior, and current code structure.
- [Gemfile](../6-polish/Gemfile) — Direct gem dependencies.
- [Gemfile.lock](../6-polish/Gemfile.lock) — Resolved dependencies.
- [.bundle/config](../6-polish/.bundle/config) — Local bundle path.
- [.ruby-version](../6-polish/.ruby-version) — Ruby version.
- [.rubocop.yml](../6-polish/.rubocop.yml) — Rails Omakase lint configuration.
- .dockerignore — Files excluded from image builds.
- [Dockerfile](../6-polish/Dockerfile) — Production image.
- [compose.yaml](../6-polish/compose.yaml) — Local PostgreSQL service.
- [Rakefile](../6-polish/Rakefile) — Rails tasks.
- [config.ru](../6-polish/config.ru) — Rack entry point.
- [bin/rails](../6-polish/bin/rails) — Rails command entry point.
- [bin/rubocop](../6-polish/bin/rubocop) — Linter command.
- [bin/check](../6-polish/bin/check) — Local acceptance and lint gate.
- [bin/check-production](../6-polish/bin/check-production) — Production acceptance and security gate.
- [config/application.rb](../6-polish/config/application.rb) — API-only Rails application setup.
- [config/boot.rb](../6-polish/config/boot.rb) — Bundler and Bootsnap setup.
- [config/environment.rb](../6-polish/config/environment.rb) — Application initialization.
- [config/database.yml](../6-polish/config/database.yml) — PostgreSQL connections.
- [config/puma.rb](../6-polish/config/puma.rb) — Server threads and port.
- [config/routes.rb](../6-polish/config/routes.rb) — API routes.
- [config/environments/development.rb](../6-polish/config/environments/development.rb) — Development settings.
- [config/environments/production.rb](../6-polish/config/environments/production.rb) — Production settings.
- [config/environments/test.rb](../6-polish/config/environments/test.rb) — Test settings.
- [config/initializers/cors.rb](../6-polish/config/initializers/cors.rb) — API CORS policy.
- [config/initializers/filter_parameter_logging.rb](../6-polish/config/initializers/filter_parameter_logging.rb) — Sensitive log filtering.
- [db/migrate/20260927000000_create_conduit.rb](../6-polish/db/migrate/20260927000000_create_conduit.rb) — Core tables and constraints.
- [db/migrate/20260927000001_add_drafts_to_articles.rb](../6-polish/db/migrate/20260927000001_add_drafts_to_articles.rb) — Draft and revision columns.
- [db/schema.rb](../6-polish/db/schema.rb) — Rails schema snapshot.
- [app/controllers/application_controller.rb](../6-polish/app/controllers/application_controller.rb) — Authentication and shared error responses.
- [app/controllers/api/articles_controller.rb](../6-polish/app/controllers/api/articles_controller.rb) — Article requests, access, filters, and responses.
- [app/controllers/api/comments_controller.rb](../6-polish/app/controllers/api/comments_controller.rb) — Comment endpoints.
- [app/controllers/api/profiles_controller.rb](../6-polish/app/controllers/api/profiles_controller.rb) — Profiles and follows.
- [app/controllers/api/sessions_controller.rb](../6-polish/app/controllers/api/sessions_controller.rb) — Login and rate limiting.
- [app/controllers/api/tags_controller.rb](../6-polish/app/controllers/api/tags_controller.rb) — Published article tags.
- [app/controllers/api/users_controller.rb](../6-polish/app/controllers/api/users_controller.rb) — Registration and current user.
- [app/models/application_record.rb](../6-polish/app/models/application_record.rb) — Active Record base class.
- [app/models/article.rb](../6-polish/app/models/article.rb) — Article relationships, publication, revisions, tags, and queries.
- [app/models/article_tag.rb](../6-polish/app/models/article_tag.rb) — Article–tag join.
- [app/models/comment.rb](../6-polish/app/models/comment.rb) — Comment relationships and validation.
- [app/models/favorite.rb](../6-polish/app/models/favorite.rb) — User–article favorite.
- [app/models/follow.rb](../6-polish/app/models/follow.rb) — User follow relationship.
- [app/models/tag.rb](../6-polish/app/models/tag.rb) — Tag relationships and validation.
- [app/models/user.rb](../6-polish/app/models/user.rb) — User relationships, password, and token.
- [app/views/api/articles/_article.json.jbuilder](../6-polish/app/views/api/articles/_article.json.jbuilder) — Article JSON fields.
- [app/views/api/articles/conflict.json.jbuilder](../6-polish/app/views/api/articles/conflict.json.jbuilder) — Stale revision response.
- [app/views/api/articles/index.json.jbuilder](../6-polish/app/views/api/articles/index.json.jbuilder) — Article list response.
- [app/views/api/articles/show.json.jbuilder](../6-polish/app/views/api/articles/show.json.jbuilder) — Single article response.
- [app/views/api/comments/_comment.json.jbuilder](../6-polish/app/views/api/comments/_comment.json.jbuilder) — Comment JSON fields.
- [app/views/api/comments/index.json.jbuilder](../6-polish/app/views/api/comments/index.json.jbuilder) — Comment list response.
- [app/views/api/comments/show.json.jbuilder](../6-polish/app/views/api/comments/show.json.jbuilder) — Single comment response.
- [app/views/api/profiles/_profile.json.jbuilder](../6-polish/app/views/api/profiles/_profile.json.jbuilder) — Profile JSON fields.
- [app/views/api/profiles/show.json.jbuilder](../6-polish/app/views/api/profiles/show.json.jbuilder) — Profile response.
- [app/views/api/tags/index.json.jbuilder](../6-polish/app/views/api/tags/index.json.jbuilder) — Tag list response.
- [app/views/api/users/show.json.jbuilder](../6-polish/app/views/api/users/show.json.jbuilder) — User and token response.

## What each pass changed

- **Pass 1:** Moved locked revision updates and tag replacement into `Article`, where those domain rules now sit beside publication. The first check exposed a duplicate-tag conflict; restoring lookup before creation fixed it. Both gates then passed.
- **Pass 2:** Reread the owned files and found no further change that clearly improved clarity or terseness. Both gates passed again. Updated the README afterward to describe the model boundary and remove stale benchmark figures.

## Run counts

`bin/check`: **3** runs, including one failed run; `bin/check-production`: **2** runs. Narrower runs: **0**. Build failures: **0**.

## Friction log

- Tag creation returned 409 because `create_or_find_by!` attempted insertion before the tag’s uniqueness validation could find the existing row.
- Each local gate needed a fresh PostgreSQL container and database, making full acceptance runs the main verification cost.
- Production verification rebuilt the image and ran a separate security suite, so it had to follow the local gate on the shared port.
- The README contained historical scan and benchmark claims; they needed pruning to describe the current code accurately.

## Agent-friendliness notes

Rails associations, callbacks, scopes, `has_secure_password`, and Jbuilder made the domain easy to locate by file. The strict RealWorld error shapes and draft revision rules required explicit controller input checks; moving persistence rules to `Article` kept those HTTP concerns separate.