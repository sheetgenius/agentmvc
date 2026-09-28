# Environment

- Stack: Rails 8.1 API-only with PostgreSQL. A generated, product-free scaffold is already in this directory; do not rerun `rails new`.
- Port: 4101. Bind the backend so it is reachable at `127.0.0.1:4101` from the host and browser harness.
- Toolchain: Ruby 3.3.2 through rbenv, Rails 8.1.3.1. Global gem directories are read-only; install gems locally with `bundle config set --local path vendor/bundle`.
- Formatter/linter: `bin/rubocop` with Rails Omakase configuration.
- PostgreSQL 17 is available through the fixed coordinator commands. `harness/db.sh start 4101` starts a disposable local database and prints its `DATABASE_URL`; `harness/db.sh stop 4101` removes it. Do not call Docker directly; the agent has no host Docker socket.
- Browser and Hurl dependencies are prepared by the harness. Run `harness/check-all.sh 4101` after starting the backend. All fixture inputs listed in `PROMPT.md` must remain unchanged.
