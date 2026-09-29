# Phoenix scaffold

This is a product-free Phoenix 1.8 JSON API scaffold. Read `ENVIRONMENT.md` for the stack commands and contract extensions. Replace this file with a concise map of the product rules and their owners as the application takes shape.

Use Phoenix routes, plugs, controllers and JSON renderers for HTTP; Ecto schemas, changesets, queries and migrations for data; Oban for durable PostgreSQL-backed jobs; and Bandit/WebSockAdapter for the fixed raw WebSocket protocol. Keep domain decisions outside transport modules. Confirm package APIs in installed source or official docs before relying on them.

`mix format --check-formatted` and `mix compile --warnings-as-errors` are the local static gates. Run focused tests and requests during development, then the frozen full gates once the app is ready.
