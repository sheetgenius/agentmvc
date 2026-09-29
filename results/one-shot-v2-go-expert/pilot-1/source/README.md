# Go API scaffold

Product-free Huma/chi application with Bun, pgx, Goose and River infrastructure.
Only `GET /health` exists. No application tables or business rules are supplied.
The server uses `DATABASE_URL`, `SECRET_KEY_BASE` and `PORT`; the health scaffold
does not consume the secret until authentication is implemented.

Run `bin/dev` inside the prepared toolchain for Air reloads. Run `go test ./...`
and `bin/lint` before the supplied acceptance checks. `Dockerfile` builds a
static native release and applies embedded migrations at startup.
