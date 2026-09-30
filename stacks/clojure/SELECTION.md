# Why this Clojure stack

Decision prepared 2026-09-30, before the implementation runs: a Kit-inspired
assembly of Ring, Reitit, Malli, Muuntaja, Integrant, next.jdbc, HoneySQL,
HikariCP, Migratus, Proletarian and Buddy. It targets the fixed PostgreSQL,
JSON and raw WebSocket contract. This is a focused library assembly, with
application-owned integration and domain functions; it is not a single
framework supplying Rails-style models, associations, jobs and channels.
Its relative source density and performance remain to be measured.

| Layer | Selection | Reason and practical cost |
| --- | --- | --- |
| Runtime | Clojure 1.12.6; CLI 1.12.5.1664; Java 25 | Persistent collections, ordinary functions and a resident REPL suit compact domain code. Production uses an AOT uberjar on a JVM; startup, warmup and heap use remain measurable costs. |
| HTTP and sockets | Ring core and official Jetty adapter 1.15.5; Jetty 12.1.13 | One HTTP server with Ring's raw WebSocket interface matches the supplied client. Application code owns room policy and event envelopes. |
| Routing and validation | Reitit 0.11.0, Malli 0.20.2, Muuntaja 0.6.12 | Route data, compiled schemas and JSON codecs avoid repeated parsing logic. Strict input and error conventions need explicit configuration. |
| Lifecycle | Integrant 1.0.1 | Dependency data governs initialization and reverse-order shutdown of pool, server and workers. Application lifecycle methods are owned source. |
| Persistence | next.jdbc 1.3.1118, HoneySQL 2.7.1479, HikariCP 7.1.0, PostgreSQL JDBC 42.7.13 | SQL as composable data, ordinary result maps and explicit transaction connections. There is no ORM relation loader; bounded association queries and projections are application responsibilities. |
| Migrations | Migratus 1.6.8 | Versioned SQL with an explicit migration history. Schema constraints remain visible in owned migration files. |
| Jobs | Proletarian 1.0.115 | PostgreSQL queue, retries and transactionally coupled enqueue. Delivery is at least once; handlers must be idempotent. |
| Authentication | buddy-hashers 2.0.167, buddy-sign 3.6.1-359; BouncyCastle 1.86 | Library password hashing and signed tokens; product identity and authorization policy remain application code. |
| Development and build | tools.build 0.10.14, integrant/repl 0.5.1, tools.namespace 1.5.1 | Reload namespaces and restart resources through the lifecycle; compile and package separately for production. |
| Checks and logging | clj-kondo 2026.08.04, cljfmt 0.16.6, Cognitect test-runner v0.5.1, SLF4J simple 2.0.20 | Static analysis, formatting and ordinary clojure.test. The test-runner git SHA is `dfb30dd6605cb6c0efc275e1df1736f6e90d4d73`. |
| Dependency security | OSV-Scanner 2.6.0 | Scan an inventory of the actual resolved Maven coordinates, including transitives. This does not provide Clojure code reachability or a dedicated application security analysis. |

Release pins were checked against publisher registries, including the
[Clojars artifact API](https://clojars.org/api/artifacts/metosin/reitit),
[Maven Central metadata](https://repo.maven.apache.org/maven2/com/zaxxer/HikariCP/maven-metadata.xml),
[pgJDBC releases](https://jdbc.postgresql.org/),
[tools.build](https://github.com/clojure/tools.build), and
[Clojure CLI release assets](https://github.com/clojure/brew-install/releases/tag/1.12.5.1664).
The scaffold records actual coordinates, image digests and tool checksums.
Stable releases are selected; a registry's newest alpha is not automatically
the selected version. Direct pins alone do not constitute a transitive lock;
preserve the resolved dependency tree and preflight evidence with the run.

[OSV's supported manifests](https://github.com/google/osv-scanner/blob/v2.6.0/docs/supported_languages_and_lockfiles.md)
do not include `deps.edn`. Export the production `tools.build/create-basis`
`:libs` entries into its documented custom package inventory (Maven
`group:artifact`, resolved version), then scan that file. CycloneDX with Maven
PURLs is also [supported](https://github.com/google/osv-scanner/blob/v2.6.0/docs/scan-source.md).
Preserve the basis, dependency input hashes and per-artifact SHA-256 hashes;
label development/build inventories separately and disclose any non-Maven
entries that were not scanned. Do not substitute a fresh Maven resolution for
the Clojure classpath. A clean result means no matched known advisories in the
queried database, not proof that every Clojars artifact is safe.

The initial scan found advisories in upstream-selected Jetty 12.1.8 and
BouncyCastle 1.78.1. Before freezing the baseline, explicit dependencies raise
Ring's four Jetty roots to [12.1.13](https://github.com/jetty/jetty.project/releases/tag/jetty-12.1.13)
and `bcprov-jdk18on`, `bcpkix-jdk18on`, and `bcutil-jdk18on` to
[BouncyCastle 1.86](https://www.bouncycastle.org/download/bouncy-castle-java/).
These versions exceed the reported fixes of Jetty 12.1.9/12.1.10 and
BouncyCastle 1.79/1.84/1.85. The resolved graph must contain a uniform Jetty
12.1.13 family (excluding independently versioned Servlet API artifacts) and
BouncyCastle 1.86 family. Preserve the initial report and verify the patched
graph with a fresh scan, password/token checks and HTTP/WebSocket preflight.

No dedicated Clojure SAST tool is configured for this lane. clj-kondo is a
linter. [clj-holmes](https://github.com/clj-holmes/clj-holmes) is a real Clojure
security analyzer, but its latest tagged binary is from 2022 and has not been
validated in this environment. [clj-watson](https://github.com/clj-holmes/clj-watson)
is a maintained dependency scanner alternative; its default NVD workflow
expects an API key and its GitHub advisory strategy needs a token. The chosen
OSV workflow preserves the common baseline without those credentials.

## Alternatives considered

| Candidate | Fit and tradeoff for this contract |
| --- | --- |
| [Kit template](https://github.com/kit-clj/kit) | Closest starting philosophy: Integrant configuration and composable server/SQL/migration libraries. Its template and optional modules provide useful conventions; this lane chooses the underlying libraries explicitly to keep the product-free baseline small and use the official Ring WebSocket API. Generated Kit source is not being claimed as the implementation. |
| [Pedestal](https://github.com/pedestal/pedestal) | Strong interceptor model, asynchronous handling, Jetty, WebSockets and observability. It is a credible HTTP alternative, but persistence, migrations and durable job integration still need assembly. Reitit's route data and Malli integration fit the chosen schema-oriented approach. |
| [Biff](https://github.com/jacobobryant/biff) | Integrated development and deployment workflow with Ring/Reitit/Jetty. Current upstream includes SQLite, an XTDB alternative, server-rendered Datastar UI, email sign-in and in-memory background jobs. PostgreSQL durability and the fixed JSON/client contract would replace several of those conventions. |
| [Luminus](https://github.com/luminus-framework/luminus-template) | Mature selectable profiles for APIs, PostgreSQL, Buddy and servers, plus standalone JVM packaging. The Leiningen template is a viable baseline; the focused deps.edn assembly gives direct control over current pins and a smaller initial integration surface. |

These are design judgments for this workload, not measurements or claims of
a universally best Clojure framework. The lane must count any integration
code it adds; choosing libraries cannot hide glue as framework behavior.

## Interfaces and contract adaptations

- [Ring WebSockets](https://github.com/ring-clojure/ring/wiki/WebSockets): a
  response carries `:ring.websocket/listener`, with callbacks such as
  `:on-open`, `:on-message` and `:on-close`; `ring.websocket/send` and `close`
  operate on the socket. Use the raw protocol expected by the fixed client.
  Sente's additional client protocol would require an incompatible client
  change. Authentication and admission must finish before upgrade.
- [Reitit Malli coercion source](https://github.com/metosin/reitit/blob/0.11.0/modules/reitit-malli/src/reitit/coercion/malli.cljc):
  the default compiler closes map schemas, but `:strip-extra-keys` defaults
  to true. Use `reitit.coercion.malli/create` with `:strip-extra-keys false`
  on routes where the contract requires rejecting unknown keys; ordinary
  routes can retain their permitted ignore/strip behavior. Malli's
  [closed-schema](https://github.com/metosin/malli/blob/0.20.2/src/malli/util.cljc)
  preserves explicitly open `[:map {:closed false} ...]` schemas, including
  when Reitit's default `:compile` function closes implicit maps. Strict
  shared inputs need closed outer envelopes and inner value schemas with
  unknown keys preserved until validation. Distinguish missing values,
  explicit null and false. Read coerced values from request parameters.
- [Reitit exception source](https://github.com/metosin/reitit/blob/0.11.0/modules/reitit-middleware/src/reitit/ring/middleware/exception.clj):
  default request-coercion failures return 400, and the default body differs
  from Conduit's error envelope. Customize that handler for the required 422
  response, and adapt malformed JSON consistently. Protected-route auth must
  precede body parsing/coercion wherever the shared contract requires auth
  errors to take precedence. Response coercion failures remain server errors.
- [next.jdbc transactions](https://cljdoc.org/d/com.github.seancorfield/next.jdbc/1.3.1118/doc/getting-started/transactions)
  and [Proletarian](https://github.com/msolli/proletarian/tree/v1.0.115): pass
  the `java.sql.Connection` from `jdbc/with-transaction` directly to
  `proletarian.job/enqueue!`. Using the pool there would create a separate
  transaction. Commit/rollback preflight must prove the coupling.
- [Proletarian worker source](https://github.com/msolli/proletarian/blob/v1.0.115/src/proletarian/worker.clj):
  `create-queue-worker` takes a data source, handler and optional options.
  Default handlers take `[job-type payload]`; advanced mode takes one job map,
  without exposing the claim transaction's connection. `start!` returns a
  boolean, so lifecycle initialization must retain and return the worker
  itself. Stop workers before closing their pool. A claimed job holds a
  connection while its handler runs; allow pool capacity for the handler's
  own database transaction. Committed domain effects can precede queue
  acknowledgment, making retry idempotency essential.
- [Buddy hashers source](https://github.com/funcool/buddy-hashers/blob/2.0.167/src/clj/buddy/hashers.clj):
  explicitly select `:argon2id` for `derive`; the implementation uses
  BouncyCastle's JVM Argon2 implementation. `verify` returns a map containing
  `:valid` and `:update`. Test `:valid`, since even an invalid-result map is
  truthy in Clojure. Production hash cost and concurrency affect resource use.
- [Buddy JWT implementation](https://github.com/funcool/buddy-sign/blob/master/src/buddy/sign/jwt.clj)
  and the published 3.6.1-359 jar were inspected: `unsign` verifies signatures
  using the explicitly selected algorithm and validates expiry when present.
  Require the expected expiry and identity claims explicitly; missing expiry
  does not cause the library to reject a token. Share token validation between
  HTTP and sockets and keep signing secrets in runtime configuration.

## Clojure implementation guidance

Use ordinary maps, qualified domain keywords where they clarify ownership,
destructuring and small named functions. Organize namespaces around meaningful
domain operations; keep HTTP adaptation thin. Shared authorization predicates,
visibility scopes, transitions and projections should have one named owner.
Keep SQL scope expressions and in-memory decisions aligned through shared
rules and focused behavior tests. Prefer direct functions to macros, generic
repositories or a new internal framework when the operation is already clear.

Use HoneySQL parameterization and PostgreSQL constraints. Load associations,
counts and viewer flags in bounded set queries for a page; keep pagination
and authorization filters in the database. Reuse the same domain projections
for list/detail/feed outputs. Pass explicit transaction connections through
multi-write operations. Realize JDBC-dependent work before releasing its
connection; do not leak lazy work across transaction boundaries.

Keep socket state changes atomic and network sends outside locks or atom
update functions. Atom update functions can retry and must be free of side
effects. Preserve event ordering with a bounded per-socket send mechanism;
do not let one slow client block room membership or database work. Process-local
rooms fit one application instance; multiple instances need shared delivery
and admission semantics before their results are comparable.

Use Integrant to own resources and close them on reload and shutdown. The
development path should reload code without rebuilding the container; the
production path must execute the AOT uberjar with reload/watch tooling off.
GraalVM native-image and jlink pruning are optional later experiments, not
requirements or unmeasured improvements in this initial JVM lane.

## Fairness and accounting

The historical eight-step run and fresh expert-v2 one-shot start independently
from the same product-free scaffold and preserve their own prompt boundaries.
Keep the shared expert prompt and Conduit JSON, PostgreSQL, raw WebSocket and
client contracts unchanged. Freeze environment guidance separately before
launching measured implementers; do not copy finished code between lanes.

The scaffold may supply health, resource lifecycle, migrations for third-party
queue tables, development tools and packaging. It supplies no product schema,
endpoint, permission rule, article projection, task, room or token code.
Unchanged scaffold and dependency downloads use the existing exclusions.
Application Clojure, SQL, configuration and startup changes count as owned
source. Retain generator inputs and report any generated source separately.
Report semantic clarity, correctness, runtime cost and feedback-loop measures
alongside bytes and tokens; a smaller source count alone does not establish
a better implementation. Preflight results belong in the run evidence and
must not be implied by this selection document.
