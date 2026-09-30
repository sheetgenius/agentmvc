# Clojure expert environment

Clojure 1.12.6, CLI 1.12.5.1664, Temurin JDK 25, Ring 1.15.5 / Jetty 12.1.13,
Reitit 0.11.0, Malli 0.20.2, Muuntaja 0.6.12, Integrant 1.0.1,
next.jdbc 1.3.1118, HoneySQL 2.7.1479, HikariCP 7.1.0, Migratus 1.6.8,
Proletarian 1.0.115, Buddy hashers 2.0.167 / sign 3.6.1-359 with Bouncy Castle 1.86, PostgreSQL 17.
Serve port 4112 on `0.0.0.0`. This Kit-inspired foundation contains a health
route and generic infrastructure. The complete product must be implemented
from the supplied contract. Direct dependencies are pinned in `deps.edn`;
preflight records the resolved runtime basis and JAR hashes. Add libraries
where useful.

Use `harness/db.sh start 4112`, then `harness/clojure.sh start|logs|stop` for
`bin/dev`. `harness/clojure.sh run COMMAND...` runs bounded toolchain commands;
`test`, `lint`, and `build` run the test runner, clj-kondo/cljfmt, and production
packaging. Use the running development server for small checks, then run
`harness/check-all.sh 4112`. Stop development before
`harness/check-production.sh 4112`. The orchestrator owns Docker and persistent
services. Do not start a second server using the bounded `run` command.

Represent domain facts as ordinary immutable maps; use qualified keywords
where they clarify ownership. Keep the contract's JSON field names explicit
in public projections. Use destructuring and named functions to make each
policy, transition, query, and projection clear. Keep one owner for each rule. Use namespaces to
separate those owners and keep HTTP handlers thin. Avoid macros or generic
repository abstractions unless they remove real repeated complexity. Maintain
a concise `AGENTS.md` map linking rules to their tests.

Use actual Reitit route data, Malli schemas, and Muuntaja JSON middleware for
boundary handling. Place authentication before body decoding and coercion
where the contract requires that precedence. Reitit's default coercion errors
use HTTP 400; adapt `:reitit.coercion/request-coercion` centrally to the
required status and error envelope. Missing, null, false, empty, and zero can
have different contract meanings. Use `contains?` when presence matters.
Reitit/Malli strips extra keys by default. On routes requiring strict shared
inputs, use the appropriate closed schema with a route/group coercion override
`(reitit.coercion.malli/create {:strip-extra-keys false})`; preserve the
contract's behavior on ordinary routes. Test the serialized wire boundary.

next.jdbc returns qualified column keys by default; choose result builders
explicitly when a query needs another representation. Parameterize SQL with
HoneySQL or JDBC placeholders. Keep filtering, ordering, pagination, and
counts in PostgreSQL. Load associations and viewer flags for a page in bounded
set queries, and reuse public projections across endpoints. Database
constraints should enforce invariants for every writer. Avoid runtime keyword
creation from arbitrary user keys and keep timestamp conversion explicit.

Migratus runs packaged SQL migrations before serving; put new numbered
`.up.sql` / `.down.sql` files in `resources/migrations/`, separating statements
with `--;;`. Use `next.jdbc/with-transaction` and pass that same transaction
Connection to `proletarian.job/enqueue!` so application changes and queued work
commit or roll back together. Register a handler `[job-type payload]` using the
queue factory and own its start/stop with Integrant. `worker/start!` returns a
boolean; retain the worker object for shutdown. Workers claim jobs in their
own transaction and run handlers while holding a connection. Give the pool
spare connections for handler queries, make effects idempotent, and do not
assume the handler receives the claim transaction. Stop HTTP admission, drain
workers, then close the pool. Test enqueue rollback and process restart.

Ring 1.15.5 and Jetty support the client's raw WebSocket JSON directly. Return
`:ring.websocket/listener` with `:on-open`, `:on-message`, `:on-close`, and
`:on-error` as needed; send and close through `ring.websocket`. Keep room state
and each connection's membership explicit. Functions passed to `swap!` may run
more than once, so keep them pure; perform sends and other effects outside
atom updates or locks. Bound outgoing queues, preserve message ordering,
handle disconnects on every path, and use the same authority checks as HTTP.
Process-local rooms are acceptable under the single-instance contract;
document that deployment limit.

Buddy provides password hashing and signed JWTs. An explicit `:argon2id`
algorithm uses the JVM implementation. `buddy.hashers/verify` returns a map;
check its `:valid` field, since even a failed verification map is truthy.
Use `buddy.sign.jwt/unsign` with an explicit allowed algorithm, validate your
required claims, and require expiry where the contract calls for it. A missing
`exp` is not automatically rejected by the library. Use the production secret
and share authentication logic between HTTP and WebSocket entrypoints.

`bin/dev` watches `src/` and `resources/`, refreshes namespaces, and resets the
Integrant system. Restart after editing `deps.edn` or `dev/`. For a REPL use
`clojure -M:dev`, require `dev`, and call `integrant.repl/go`, `reset`, or `halt`.
Use `clojure -M:test` and `bin/lint` in the feedback loop; format with
`clojure -M:format fix src dev test build.clj`. Inspect installed APIs through
`clojure.repl/doc` and the cached source jars when unfamiliar.

`bin/dependency-scan` emits `target/resolved-basis.edn`, artifact hashes,
resolved Maven/Clojars coordinates, and the OSV-Scanner 2.6.0 report. Its scan
covers runtime dependencies from the same basis as the production jar; it does
not claim dev/build dependency coverage. Exit 1 means advisory findings, while
scanner failures are errors. No dedicated Clojure security static analyzer or
reachability tool is supplied. Report that limitation; clj-kondo is not SAST.

The Dockerfile compiles a JVM AOT uberjar and copies it into a pinned Temurin
JRE image running as UID 10001. Its only application settings are
`DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT`. It must migrate, start workers,
and serve HTTP and WebSocket in one application container. The packaged jar
includes migrations and resources and does not require the source checkout.
