# Conduit Rails rule map

This Rails 8 API app serves the frozen `realworld_spec/` contract. The shared client is external.

- `app/models/user.rb`: account validation, password policy and nullable profile normalization. `UsersController` owns Token JWT issuance and login responses; `LoginThrottle` owns failed login limits.
- `ApplicationController`: token verification, visibility and author gates, response shapes, and bounded article pagination. Apply `article!` before draft sensitive operations; use `author_article!` for owner mutations.
- `app/models/article.rb`: lifecycle, public scope, slug generation and shared representation. `ArticlesController` owns list filters and publication routes.
- `ArticleCommit`: the one revision checked content mutation for owner and capability entrances. It locks the article, rechecks a share key, commits once, then publishes to `LiveRooms`.
- `ArticleShare`: key generation, hashing and rotation under the article lock. `SharesController` handles capability HTTP; `LiveSocket` handles raw Faye WebSocket admission; `LiveRooms` owns presence, ordering, revocation and the 100 member cap.
- `ArticleExport` and `ExportArticlesJob`: pending export recovery and idempotent PostgreSQL backed snapshots through GoodJob. The entrypoint requeues pending exports after schema preparation.
- `db/migrate/20260929000001_create_conduit.rb`: uniqueness, references, lifecycle, revision and export state constraints.
- Controllers handle HTTP only; add new policy in the named owner above and route through it. Keep article list filters SQL based, then page and preload authors, follows and favorite counts.

Development: `harness/db.sh start 4109`, `harness/rails.sh run bundle exec rails db:migrate`, `harness/rails.sh start`, `harness/quick-smoke.sh 4109`. Use `harness/rails.sh logs|stop`.

Checks: `harness/rails.sh test`, `harness/rails.sh run bundle exec rails zeitwerk:check`, `harness/rails.sh run bundle exec rubocop`, `harness/check-all.sh 4109`. Stop development before `harness/check-production.sh 4109`.

Presence and rate limits are process local. Keep one Puma worker; multiworker deployment needs a shared room and throttle coordinator. Exports and articles live in PostgreSQL.
