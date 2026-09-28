# Conduit backend map

- `lib/conduit/accounts.ex` owns registration, login, tokens, profiles, and follows. `user.ex` owns account validation and password hashing.
- `lib/conduit/content.ex` owns article lifecycle, visibility, revisions, comments, favorites, tags, and editing capabilities. Its Ecto schemas are `article.ex`, `comment.ex`, and `share.ex`.
- `lib/conduit/exports.ex` defines export snapshots; `export_worker.ex` runs them through PostgreSQL-backed Oban.
- `lib/conduit/rooms.ex` atomically admits up to 100 sockets per article and broadcasts presence, committed edits, and revocation. `lib/conduit_web/live_socket.ex` owns the WebSocket protocol.
- `lib/conduit_web/controllers/api_controller.ex` translates HTTP requests and domain results to JSON. `router.ex` is the route map.
- `priv/repo/migrations/` owns PostgreSQL tables, constraints, and the Oban job schema.

Change a rule in its owning domain module, then run `mix precommit` and the fixed `harness/check-all.sh 4102`. The production gate is `harness/check-production.sh 4102`; it builds the one-container image and migrates a fresh database at startup.
