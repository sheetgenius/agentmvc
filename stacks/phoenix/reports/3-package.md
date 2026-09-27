## Status: DONE

## Gate result

- `bin/check`: exit 0; 15/15 Hurl files passed; formatting passed; compilation passed with warnings treated as errors.
- `bin/check-production`: exit 0; 15/15 Hurl files passed against the production image.

## What you added

- [Dockerfile](../3-package/Dockerfile): builds an Elixir release in a slim runtime image.
- .dockerignore: limits the build context to release inputs.
- [bin/check-production](../3-package/bin/check-production): builds, tests, and cleans up the image and fresh database.
- [lib/conduit/release.ex](../3-package/lib/conduit/release.ex): runs Ecto migrations from the release.
- [config/runtime.exs](../3-package/config/runtime.exs): starts the production server using the three supplied variables.
- [config/prod.exs](../3-package/config/prod.exs): removes the HTTPS redirect from the plain HTTP container endpoint.
- [README.md](../3-package/README.md): documents how to build and run the image.

## Production choices

Bandit serves the API, with its and the BEAM’s default concurrency; Ecto uses a pool of 10. Logger stays at `:info` on the console. The container applies pending migrations before starting. A Debian Bookworm slim runtime carries the release without source mounts or build tools.

## Run counts

`bin/check`: 2; `bin/check-production`: 4; narrower acceptance runs: 0. One build failed before the Dockerfile ran; one legacy-builder attempt was interrupted after stalling. No Dockerfile build step failed.

## Friction log

- Buildx tried to write under the host home directory, which the sandbox forbids.
- Moving all Docker config hid the Buildx plugin and invoked a stalled legacy builder; moving only Buildx state fixed it.
- The existing production HTTPS redirect conflicted with the required HTTP container endpoint.
- A release needs an explicit migration command because Mix is absent at run time.

## Agent-friendliness notes

Phoenix runtime config and Ecto’s release migration support kept production changes small. Docker’s plugin discovery and writable state were the main packaging obstacles.