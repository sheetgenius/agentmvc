# Conduit API — unscored reference

A Clojure backend for RealWorld users, profiles, articles, feeds, tags, comments,
and favorites, plus private drafts, revision conflicts, durable article exports,
and revocable live editing links. The shared browser editor is a separate client.
This copy contains reviewer repairs; the original measured output is preserved.

## Run

Set `DATABASE_URL` to a PostgreSQL URL, `SECRET_KEY_BASE` to a private signing
secret, and `PORT` to the listening port (default 4112). Run `bin/dev` for reload
on save or `bin/serve` for the normal server. Startup runs Migratus migrations
and starts the Proletarian worker in the same process as Jetty.

`clojure -T:build uber` builds `target/conduit.jar`; run it with
`java -jar target/conduit.jar`. The Dockerfile packages that jar and migrations
in a nonroot Temurin JRE image. The container needs the same three environment
settings and an existing PostgreSQL database.

## Rules and code

- `rules.clj`: visibility, ownership, publication restrictions, revisions, and
  slug normalization. Drafts are visible only to their author and cannot receive
  comments or favorites.
- `users.clj`: JWTs, Argon2id passwords, account/profile changes, follows, and
  login admission. Two password operations run at once across registration,
  login, and password changes; an email admits at most 20 attempts per minute
  until a successful login resets its counter.
- `articles.clj`: article changes, tags, comments, favorites, and query
  projections. Article edits lock a stable article ID, validate revisions, and
  increment the revision once. Public lists exclude drafts, omit bodies, and
  default to 20 items; limits above 100 are rejected.
- `shares.clj`: capability creation, rotation, revocation, and WebSocket rooms.
  Only key hashes are stored. Shared saves accept title, body, and revision;
  capability revalidation and link changes coordinate on the article lock.
  Rooms admit 100 editors, preserve revision order, and disconnect clients whose
  bounded output queue fills. Rooms are local to this single backend instance.
- `exports.clj` and `queue.clj`: atomically enqueue an export with its row, then
  store an immutable snapshot of the author's articles and tags. Repeatable Read
  keeps the snapshot coherent; completed exports are not rebuilt. Transient job
  failures have three delayed retries.
- `http.clj`: routes, authentication precedence, JSON, CORS, and error envelopes.
  Reitit/Muuntaja handle routing and codecs; Malli checks the registration
  envelope, while field and domain validation is explicit in application code.
- `db.clj`, `database.clj`, `migrations.clj`, and `system.clj`: next.jdbc result
  mapping, HikariCP, schema migration, and Integrant lifecycle. Migrations under
  `resources/migrations/` contain schema, constraints, and indexes.

## Checks and reference changes

Run `bin/lint` and the default `clojure -M:format check src dev test build.clj`.
`clojure -M:test` requires `DATABASE_URL` pointing to a disposable test database:
the integration fixture migrates it and creates test records. The surrounding
evaluation harness also runs the frozen HTTP, security, socket, and browser
checks. `bin/dependency-scan` scans the resolved runtime Maven graph.

Reference repairs bound password work without reducing Argon2id cost, reserve
login attempts atomically, recheck capabilities inside save transactions,
coordinate link rotation/revocation, make exports coherent and retryable, clean
up socket senders on close/overflow, and notify subscribers after publishing or
deletion. Focused tests exercise lock waits, concurrent export edits, transient
job failure, bounded password admission, socket cleanup, and route notifications.
Verification results are recorded separately from the original measurements.
