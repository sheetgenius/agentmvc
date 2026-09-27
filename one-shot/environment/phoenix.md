# Environment

- Stack: Phoenix 1.8 and Ecto, JSON API-only, with PostgreSQL. A generated, product-free scaffold is already in this directory; do not rerun `phx.new`.
- Port: 4102. Bind the backend to `0.0.0.0` in its container and publish port 4102 to the host.
- Toolchain: Elixir runs through the available `elixir:1.18.4-otp-27` Docker image. Use it for Mix commands; run containers as the host user with `--user "$(id -u):$(id -g)"`. Keep `MIX_HOME` and `HEX_HOME` in this directory or the container.
- Formatter/linter: `mix format --check-formatted` and `mix compile --warnings-as-errors`.
- Docker and PostgreSQL 17 are available. `harness/db.sh start 4102` starts a disposable local database and prints its `DATABASE_URL`; `harness/db.sh stop 4102` removes it. A containerized development app can reach that host database through `host.docker.internal`.
- Browser and Hurl dependencies are prepared by the harness. Run `harness/check-all.sh 4102` after starting the backend. All fixture inputs listed in `PROMPT.md` must remain unchanged.
