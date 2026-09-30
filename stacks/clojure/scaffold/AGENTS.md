# Project map

- `src/conduit/http.clj`: Reitit/Malli/Muuntaja HTTP composition and health route.
- `src/conduit/config.clj`: the three application environment settings.
- `src/conduit/database.clj`: PostgreSQL URL and HikariCP connection pool.
- `src/conduit/migrations.clj`, `resources/migrations/`: Migratus lifecycle and SQL.
- `src/conduit/queue.clj`: Proletarian worker factory; add application handlers and lifecycle ownership when needed.
- `src/conduit/system.clj`, `main.clj`: Integrant lifecycle, Jetty, ordered shutdown.
- `dev/dev.clj`, `bin/dev`: tools.namespace refresh and Integrant restart loop.
- `clojure -M:test`, `bin/lint`: Cognitect test runner, clj-kondo, and cljfmt.
- `build.clj`, `Dockerfile`: JVM AOT uberjar with packaged resources, nonroot JRE runtime.
- `bin/dependency-scan`: resolved runtime basis/JAR inventory and OSV advisory scan.
- This scaffold has no product models, auth flow, workers, or socket protocol.
- Replace this map with product rule owners and focused tests as the application grows.
