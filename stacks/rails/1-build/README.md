# Conduit API

Rails 8.1 API implementation of the pinned RealWorld contract in `realworld_spec/`.

## Run

Ruby 3.3.2 and Docker are required. Install gems locally, start PostgreSQL, prepare the database, and start Puma:

```sh
bundle config set --local path vendor/bundle
bundle install
docker compose -p rails-fresh-dev up -d
export DATABASE_URL=postgres://postgres:conduit@127.0.0.1:55401/conduit_development
bin/rails db:prepare
bin/rails server -b 127.0.0.1 -p 4101
```

Set `SECRET_KEY_BASE` and `DATABASE_URL` in production. Run `bin/check` for a fresh database, all 13 official Hurl files, and Omakase RuboCop. It stops its server and database on exit.

## Libraries and code

Rails provides routing, controllers, validations, associations, migrations, and JSON views. `pg` connects Active Record to PostgreSQL; `puma` serves HTTP; `bootsnap` speeds boot; `bcrypt` backs `has_secure_password`; `jwt` signs authentication tokens; `jbuilder` renders the contract's JSON shapes; `rack-cors` handles cross-origin requests; `rubocop-rails-omakase` checks the default Rails style.

Models in `app/models` hold the domain relationships and validations. `ApplicationController` handles token authentication and common errors; controllers in `app/controllers/api` handle endpoint flow. Jbuilder views in `app/views/api` define responses. `db/migrate` defines the schema, and `bin/check` is the acceptance gate. The unused deployment, CI, and generated framework files were removed after generating the scaffold.

## Spec choices

Article slugs use the title plus a random suffix so duplicate titles remain distinct; changing a title changes its slug. Tokens expire after 30 days. Tags keep their article order and remain available in `/api/tags` after their last article is deleted. Email and username uniqueness are case sensitive. Article lists default to 20 entries and omit `body`. Empty `bio` and `image` values become `null`. Duplicate email or username returns 409, as the Hurl suite requires.
