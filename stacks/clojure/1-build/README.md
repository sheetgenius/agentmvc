# Conduit API

Set `DATABASE_URL` (a PostgreSQL URL), `SECRET_KEY_BASE`, and optionally `PORT` (default 4112). Run `bin/dev` for reload on save, or `bin/serve` for a steady server. `bin/check` runs a fresh database, all 13 official Hurl files, lint, formatting, and tests. Production: `clojure -T:build uber`, then `java -jar target/conduit.jar`.

## Libraries

- Clojure is the application language. Ring and Jetty serve HTTP; Reitit routes it, with its middleware and Muuntaja handling parameters and JSON.
- Integrant owns startup and shutdown. next.jdbc handles queries, HoneySQL builds partial updates, HikariCP pools PostgreSQL connections, the PostgreSQL driver connects, and Migratus runs the schema.
- Buddy hashers stores password hashes; Buddy sign issues and verifies JWTs. Pinned Bouncy Castle overrides Buddy's older transitive versions. SLF4J Simple logs.
- Development uses integrant.repl and tools.namespace. Cognitect test runner, clj-kondo, cljfmt, and tools.build are development and build tools.

## Code

`http.clj` names the routes and response shapes. `users.clj` owns accounts, login, profiles, and follows; `articles.clj` owns articles, tags, comments, favorites, and feeds. `domain.clj` holds shared validation and authorization failures; `store.clj` is the small next.jdbc adapter. `system.clj`, `config.clj`, `database.clj`, `migrations.clj`, and `main.clj` start the service. `resources/migrations/` defines the relational schema.

## Spec choices

Slugs use a readable title prefix and a short random suffix so duplicate titles work. Article lists omit `body`; single articles include it. Counts precede pagination (default limit 20, offset 0). Tags exist while an article uses them, preserving each article's tag order; article and tag changes commit together. A supplied `tagList` must be an array of strings. Empty `bio` and `image` become null. JWTs identify the stable user ID and expire after 30 days. Passwords require at least 8 characters without composition rules. Errors follow the suite's field-specific `errors` object and status codes.

The scaffold's unused durable queue, queue tables, and Malli dependencies were removed so the files describe this product.
