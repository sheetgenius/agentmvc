# Clojure foundation

A product-free, Kit-inspired Clojure CLI application. It serves only `GET
/health`. PostgreSQL migration and pooling, a durable queue factory, automatic
development reload, and JVM AOT packaging are ready for application work.

Set `DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT` (4112 by default), then run
`bin/dev`. Use `clojure -M:test`, `bin/lint`, and `clojure -T:build uber`.
Production runs `java -jar target/conduit.jar`; the Dockerfile packages the
jar and its migrations in a nonroot Temurin JRE image.

`bin/dependency-scan` scans the exact resolved runtime graph with OSV-Scanner.
The toolchain installs the pinned scanner; the production image contains only
the JRE and application jar. Add new migration files under
`resources/migrations/`; no product implementation or fixtures are included.
