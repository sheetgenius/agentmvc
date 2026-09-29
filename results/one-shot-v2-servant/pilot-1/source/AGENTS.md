# Conduit backend rule map

- `app/Main.hs` owns Servant routes, status codes, CORS, WebSocket upgrade, and startup.
- `app/Domain.hs` owns input validation, slug normalization, error shape, and draft visibility.
- `app/Users.hs` owns registration, login limits, profile updates, follows, and their error order.
- `app/Auth.hs` owns bcrypt password handling and signed JWT issuance and verification.
- `app/Articles.hs` owns lists, feeds, tags, publication, favorites, comments, ownership, and revision checks.
- `app/Shares.hs` owns capability rotation, key hashing, admission, presence, revocation, and edit broadcasts.
- `app/Exports.hs` owns queued export creation, snapshot building, and access control.
- `app/Db.hs` owns the Hasql connection and single JSON parameter/result statement boundary.
- `migrations/001_init.sql` owns constraints, indexes, and JSON projections used by HTTP and jobs.

Follow a rule from its domain function into one SQL statement; transport handlers only bind routes and response codes. Add a migration for new cross-entrance invariants, then cover the transition in `tests/rules.py`. Article and share edits both call `Articles.updateChecked`; draft visibility is shared through `Articles.visibleArticle`.

Local development (port 4105):

1. `harness/db.sh start 4105` (note the printed `DATABASE_URL`).
2. `harness/hs.sh start` starts the watched Servant server with the fixture environment.
3. `harness/quick-smoke.sh 4105` checks a running build in seconds.
4. `python3 tests/rules.py 4105` exercises shared transitions.
5. `harness/hs.sh run fourmolu -i app/*.hs` and `harness/hs.sh run hlint app`.
6. `harness/check-all.sh 4105` runs the fixed API, socket, browser, and security suite.
7. `harness/hs.sh stop`, then `harness/check-production.sh 4105` runs a fresh database and image.

`DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT` are the only production inputs. Startup applies the migration and starts the export worker in the same process. The production image carries the SQL file. The shared frontend and acceptance inputs are read only.
