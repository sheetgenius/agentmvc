# Environment

- Stack: Rust with Loco 1.2, SeaORM 2, Axum, and PostgreSQL. A generated, product-free scaffold is already in `conduit/`; do not rerun `loco new`.
- Port: 4103. Bind the backend so it is reachable at `127.0.0.1:4103` from the host and browser harness.
- Toolchain: Cargo 1.95, Loco CLI 1.2.0, and SeaORM CLI 2.0.3 are available on the host. The existing generated `conduit/AGENTS.md` describes Loco conventions.
- Formatter/linter: from `conduit/`, run `cargo fmt --all -- --check` and `cargo clippy --all-targets -- -D warnings`.
- Docker and PostgreSQL 17 are available. `harness/db.sh start 4103` starts a disposable local database and prints its `DATABASE_URL`; `harness/db.sh stop 4103` removes it.
- Browser and Hurl dependencies are prepared by the harness. Run `harness/check-all.sh 4103` after starting the backend. All fixture inputs listed in `PROMPT.md` must remain unchanged.
