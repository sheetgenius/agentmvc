Implemented the Conduit backend, including the RealWorld API, drafts, exports, editing links, revision conflicts, WebSocket updates, presence, and the 100-editor room cap.

The main API and live editing rules are in [server.rs](/work/app/conduit/src/bin/server.rs). [schema.sql](/work/app/conduit/src/bin/schema.sql) prepares PostgreSQL at startup; [Dockerfile](/work/app/Dockerfile) packages the single production container.

**Checks are green:** the development and production gates each passed all 17 API files (237 requests), the socket protocol check, four browser tests, and all 13 security files (52 requests). `cargo fmt --all -- --check` and `cargo clippy --all-targets -- -D warnings` passed. The first development run found that an empty bio needed to become `null`; I fixed that and reran the full suite.

Known limit: exports are durable in PostgreSQL and processed outside requests, but their polling worker is custom rather than Loco’s built-in job queue.