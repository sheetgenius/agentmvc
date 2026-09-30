# Clojure environment

- Stack: Clojure 1.12.6, CLI 1.12.5.1664, Temurin JDK 25, Ring 1.15.5 / Jetty 12.1.13,
  Reitit 0.11.0, Malli 0.20.2, Muuntaja 0.6.12, Integrant 1.0.1,
  next.jdbc 1.3.1118, HoneySQL 2.7.1479, HikariCP 7.1.0, Migratus 1.6.8,
  Proletarian 1.0.115, Buddy hashers 2.0.167 / sign 3.6.1-359 with Bouncy Castle 1.86, PostgreSQL 17.
- Serve port 4112 on `0.0.0.0`. `deps.edn` pins direct dependencies; the
  preflight publishes the resolved runtime basis and JAR hashes. Dependencies
  may be added with normal Clojure CLI coordinates.
- This is a maintainer-authored, product-free prepared scaffold. It contains
  only `GET /health`, PostgreSQL pooling, migration startup, a queue factory,
  and JVM AOT release packaging. At step 1, implement the base product from
  the supplied contract. Step 1 begins from this disclosed foundation;
  steps 2–8 evolve the independently verified snapshot from the preceding step.
  `.scaffold/` is the frozen foundation size baseline.
- `harness/db.sh start 4112` starts disposable PostgreSQL.
  `harness/clojure.sh start|logs|stop` manages the foreground `bin/dev` loop.
  `harness/clojure.sh run COMMAND...` executes bounded toolchain commands.
  Use `harness/clojure.sh test`, `harness/clojure.sh lint`, and supplied checks.
- `clojure -M:test` runs Cognitect's test runner; `bin/lint` runs clj-kondo and
  cljfmt. `clojure -M:format fix src dev test build.clj` formats source.
  `clojure -T:build uber` produces `target/conduit.jar`. `clojure -M -e` and
  `clojure.repl/doc` inspect installed APIs. The toolchain includes git, curl,
  ripgrep, PostgreSQL client, Python, and a warmed Maven dependency cache.
- `bin/dev` refreshes changed `src/` namespaces using tools.namespace and
  restarts the Integrant system; migrations and resources are reloaded with it.
  Save edits and use the same process for feedback. Restart after changing
  `deps.edn` or `dev/`. You can use `clojure -M:dev` for an interactive REPL,
  then require `dev` and call `integrant.repl/go`, `reset`, and `halt`.
- `bin/dependency-scan` writes the exact runtime dependency inventory and
  OSV-Scanner 2.6.0 advisory report under `target/`. Exit 1 means findings;
  scanner/network errors must be reported as failures. This scans known Maven
  advisories for Clojars/Maven coordinates; absence of an advisory is limited
  coverage. No dedicated Clojure security static analyzer or reachability
  analysis is supplied. clj-kondo is correctness/style lint, not a security scan.
- Production is a JVM AOT uberjar in a pinned Temurin JRE image, running as
  nonroot UID 10001. Only `DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT` configure
  the application. Migrations are packaged in the jar and run before HTTP starts.
- The orchestrator owns Docker, disposable databases, and gate containers.
  Do not start persistent services through the bounded `run` action. Frozen
  specs, client, and harness files are read-only; work in your application tree.
