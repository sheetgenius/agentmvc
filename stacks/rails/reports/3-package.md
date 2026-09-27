**Status:** DONE.

**Gate result:** `bin/check` exited 0: 15/15 Hurl files passed; RuboCop inspected 41 files with no offenses. `bin/check-production` exited 0: 15/15 Hurl files passed.

**What you added:**

- [Dockerfile](../3-package/Dockerfile): builds a production image in two stages.
- .dockerignore: excludes local dependencies, generated files, and test fixtures from the build context.
- [bin/check-production](../3-package/bin/check-production): builds the image, tests it with fresh PostgreSQL, and cleans up.
- [README.md](../3-package/README.md): documents how to build and run the image.

**Production choices:** Puma serves on `0.0.0.0:$PORT` with the existing three-thread default; the database pool remains five connections. Rails logs tagged requests to stdout at info level. Startup runs `db:prepare` so an empty PostgreSQL database gets its schema. The image uses `ruby:3.3.2-slim-bookworm`, matching the project Ruby version, with build tools kept out of the runtime stage.

**Run counts:** `bin/check`: 2; `bin/check-production`: 3; narrower runs: 1 interrupted manual build probe; build failures hit: 1.

**Friction log:**

- Buildx first tried to write state outside the writable workspace; the script now stores that state under `tmp/`.
- The image’s Bundler version differed from the lockfile, requiring Bundler to download the locked version.
- Removing apt indexes invalidated the gem build cache, so the cleanup pass required a second full gem install.

**Agent-friendliness notes:** Rails conventions kept production startup to `db:prepare` and Puma. The existing production settings already covered eager loading and stdout logging; no application behavior needed changing.