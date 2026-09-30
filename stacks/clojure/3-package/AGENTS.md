# Product map

- `src/conduit/http.clj`: RealWorld routes, JSON, CORS, and error responses.
- `src/conduit/users.clj`: registration, login, current user, profiles, and follows.
- `src/conduit/articles.clj`: articles, feed, tags, comments, and favorites.
- `src/conduit/domain.clj`: validation, not found, and ownership rules.
- `src/conduit/store.clj`: next.jdbc result mapping.
- `resources/migrations/001-conduit.*.sql`: PostgreSQL relationships and constraints.
- `src/conduit/{config,database,migrations,system,main}.clj`: application lifecycle.
- `bin/check`: fresh database, official Hurl suite, formatter, linter, and tests via the supplied harness.
- `test/conduit/http_test.clj`: route smoke test; the official Hurl suite covers product behavior.
