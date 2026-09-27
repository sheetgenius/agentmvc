# Environment

- **Stack:** Rust with Loco (loco-rs 1.2, SeaORM 2, Axum), a JSON API only, with PostgreSQL.
- **Port:** 4103.
- **Toolchain on the host:** `cargo` 1.95, the `loco` CLI 1.2.0 and `sea-orm-cli` 2.0.3, all in `~/.cargo/bin`. Beyond this directory you can also write to `~/.cargo/registry` and `~/.cargo/git`.
- **Generator:** `loco new --path . --name conduit --db postgres --bg async --assets none`. See `loco new --help` for other starters.
- **Scaffold snapshot**, taken right after generating and before any change:
  ```
  rsync -a --exclude .scaffold --exclude realworld_spec --exclude deps --exclude _build --exclude target --exclude vendor --exclude node_modules --exclude tmp --exclude log ./ .scaffold/
  ```
- **Formatter and linter:** `cargo fmt --all -- --check` and `cargo clippy --all-targets -- -D warnings`.
- **Guidance:** read the generated `AGENTS.md` and the bundled Loco skill.
- **Services:** Docker works, and the images `postgres:17-alpine` and `ghcr.io/orange-opensource/hurl:latest` are already pulled. Network access to package registries works.
- **Sandbox:** you can only write inside this directory, plus any locations listed above. Everything else is read-only. `.git` is read-only, so don't use git.
- **Deleting files:** commands containing `rm -f` are rejected by this environment's policy. Use plain `rm`.
