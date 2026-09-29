# Environment

- Stack: Phoenix 1.8 and Ecto, JSON API-only, with PostgreSQL. A generated, product-free scaffold is already in this directory; do not rerun `phx.new`.
- Port: 4102. Bind the backend to `0.0.0.0` in its container and publish port 4102 to the host.
- Toolchain: Elixir runs through the pinned `elixir:1.18.4-otp-27` image by `harness/phoenix.sh run mix COMMAND`. This mounts only your workspace at `/work/app`, works in `/work/app/conduit`, runs as the host user, and keeps Mix and Hex caches in your workspace. `harness/phoenix.sh start` starts `mix phx.server` in a development container; `logs` and `stop` inspect or remove it. You may pass another container command to `run` or `start` if needed.
- Formatter/linter: `harness/phoenix.sh run mix format --check-formatted` and `harness/phoenix.sh run mix compile --warnings-as-errors`.
- PostgreSQL 17 is available through `harness/db.sh start 4102` and `harness/db.sh stop 4102`. The container receives `DATABASE_URL` pointing to `host.docker.internal:54102`, plus `PGHOST` and `PGPORT`. Configure the development Repo to use that URL. The agent has no host Docker socket.
- Browser and Hurl dependencies are prepared by the harness. Run `harness/check-all.sh 4102` after starting the backend. All fixture inputs listed in `PROMPT.md` must remain unchanged.
