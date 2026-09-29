# Reviewer database readiness correction

The initial independent production check failed before acceptance requests:
the native server connected to `db:5432` and received connection refused.
Its image had built successfully, the measured agent's production gate had
passed, and the independent development gate passed.

The frozen coordinator called `pg_isready` without a host. The actual
`postgres:17-alpine` image entrypoint's `docker_temp_server_start` function
starts its setup server with `listen_addresses=''` (line 297), then stops it
before normal startup. A Unix socket can therefore report ready before the
database accepts the TCP connection used by the application. The fast cached
Go binary exposed this race.

`tools/lane_review.py` changes reviewer readiness to
`pg_isready -h 127.0.0.1`, preserving all acceptance checks. The previous failed
verification and log remain recorded, alongside the review adapter's identity.

The application source SHA-256 is
`01c08c987a01acfba0c11abb76241e51b245d27b1eb7e719bd57a6d3bc46c104`.
No application code, measured session, prompt, or frozen fixture was changed;
the coding agent was not rerun. This is an independent reviewer infrastructure
correction, not an application repair.
