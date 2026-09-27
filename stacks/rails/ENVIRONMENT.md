# Environment

- **Stack:** Ruby on Rails 8.1, API-only, with PostgreSQL.
- **Port:** 4101.
- **Toolchain:** Ruby 3.3.2 through rbenv, with the `rails` 8.1.3.1 command installed. The global gem directories are read-only, so install gems locally with `bundle config set --local path vendor/bundle`.
- **Generator:** `rails new . --name conduit --api --database=postgresql --skip-bundle --skip-git`, plus any other skip flags that suit an API. `--name` is required because this directory's name can't be a Rails application name.
- **Scaffold snapshot**, taken right after generating and before any change:
  ```
  rsync -a --exclude .scaffold --exclude realworld_spec --exclude deps --exclude _build --exclude target --exclude vendor --exclude node_modules --exclude tmp --exclude log ./ .scaffold/
  ```
- **Formatter and linter:** `bin/rubocop` with the default Rails Omakase configuration.
- **Services:** Docker works, and the images `postgres:17-alpine` and `ghcr.io/orange-opensource/hurl:latest` are already pulled. Network access to package registries works.
- **Sandbox:** you can only write inside this directory, plus any locations listed above. Everything else is read-only. `.git` is read-only, so don't use git.
- **Deleting files:** commands containing `rm -f` are rejected by this environment's policy. Use plain `rm`.
