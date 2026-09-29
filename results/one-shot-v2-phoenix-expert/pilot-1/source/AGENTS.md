# Conduit backend rule map

Phoenix 1.8 JSON API with PostgreSQL, Oban exports, and a raw WebSocket endpoint. The shared client and checks are frozen under `realworld_spec/`, `security/`, and `harness/`.

- `lib/conduit/accounts.ex` owns registration, login, token verification, follow state, and caller identity. `accounts/user.ex` owns user field and password validation; `accounts/login_limiter.ex` owns the 15-minute failed-login window.
- `lib/conduit/articles.ex` owns draft visibility, discovery and page queries, edit authority, slug generation, revision checks, publication, favorites, comments, and article projections. `articles/article.ex` and `articles/comment.ex` own persistence validation.
- `lib/conduit/shares.ex` owns key generation, hashed capability checks, rotation, and revocation. Shared and author edits both enter `Articles.commit/2`; share authority is rechecked inside its locked transaction.
- `lib/conduit/live/room.ex` owns atomic admission, presence, and the 100-socket cap. `live/socket.ex` speaks raw JSON WebSocket frames. Rooms are process-local to the one-instance production topology and deliver frames through socket processes.
- `lib/conduit/exports.ex` owns the snapshot and atomic export/job request; `exports/worker.ex` runs durable jobs through Oban.
- `lib/conduit_web/router.ex`, `plugs/caller.ex`, `api.ex`, and controllers own routes, wire shape, status codes, and JSON delivery. The share live route uses WebSockAdapter because the fixed client does not speak Phoenix Channel envelopes.
- `priv/repo/migrations/` owns database references, uniqueness, state, and revision constraints. Add a migration for persistent rule changes.

Start PostgreSQL with `harness/db.sh start 4108`, migrate with `harness/phoenix.sh run mix ecto.migrate`, then start the watched server with `harness/phoenix.sh start`. Check a change with `harness/quick-smoke.sh 4108` and project tests via `harness/phoenix.sh test`. Run `harness/phoenix.sh run mix format --check-formatted` and `harness/phoenix.sh run mix compile --warnings-as-errors`.

Final gates: `harness/check-all.sh 4108`; stop dev with `harness/phoenix.sh stop`; then `harness/check-production.sh 4108` against a fresh PostgreSQL database and the Mix release. The release migrates on boot; it receives only `DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT`.
