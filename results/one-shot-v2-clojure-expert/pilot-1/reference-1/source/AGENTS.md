# Conduit backend rule map

- `src/conduit/rules.clj`: canonical visibility, ownership, publication interaction, revision, and slug rules. Change shared policies here first; see `test/conduit/rules_test.clj`.
- `src/conduit/users.clj`: credentials, JWT validation, password policy, profiles, follows, and login throttling.
- `src/conduit/articles.clj`: article transitions, comments, favorites, public projections, tags, and bounded list/filter/count queries.
- `src/conduit/shares.clj`: editing capability keys, rotation, revocation, WebSocket admission, ordered updates, presence, and 100 editor cap. Rooms are process local for the single instance deployment.
- `src/conduit/exports.clj`: durable export request and immutable snapshot. `src/conduit/queue.clj` registers the Proletarian handler.
- `resources/migrations/002-conduit.up.sql`: persistent identities, references, uniqueness, lifecycle checks, and indexes. Add numbered Migratus migrations for schema changes.
- `src/conduit/http.clj`: Reitit routes, Muuntaja JSON, Malli boundary schema, auth and capability precedence, CORS, and error envelope. Keep handlers thin and call domain owners.
- `src/conduit/system.clj`: Integrant order for migrations, worker, Jetty, and shutdown. `src/conduit/config.clj` owns the three environment settings.

Development: `harness/db.sh start 4112`, `harness/clojure.sh start`; inspect `harness/clojure.sh logs`, then `harness/clojure.sh stop` and `harness/db.sh stop 4112`.

Verify: `harness/clojure.sh run clojure -M:format fix src dev test build.clj`, `harness/clojure.sh lint`, `harness/clojure.sh test`. With development server running, use `harness/check-all.sh 4112`. Stop development before `harness/check-production.sh 4112`.

Frozen contracts and checks live under `realworld_spec/`, `security/`, and `harness/`; do not edit them. The shared client is served outside the backend image.
