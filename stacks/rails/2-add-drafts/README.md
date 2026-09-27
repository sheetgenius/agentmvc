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

Set `SECRET_KEY_BASE` and `DATABASE_URL` in production. Run `bin/check` for a fresh database, all 15 Hurl files, and Omakase RuboCop. It stops its server and database on exit.

## Drafts and revisions

`POST /api/articles` accepts `status: "draft"` or `"published"`; omitted status means published. Every article response includes `status`, `publishedAt` (null for drafts), and `revision` (initially 1). A published article receives its publication time once.

Drafts appear only in their author's `GET /api/articles/:slug` response and `GET /api/user/drafts` list. The drafts list requires a token, orders newest first, supports `limit` and `offset`, and omits article bodies. Public lists, feeds, counts, and tags include published articles only. Other users see a draft as a 404. The author can read the draft's empty comments list, but cannot create comments or favorite the draft (422).

The author publishes with `POST /api/articles/:slug/publish`. Publishing a draft sets `publishedAt` and increments `revision`; publishing it again leaves both unchanged. Other users receive 403 for a published article and 404 for a draft. Authentication is required.

`PUT /api/articles/:slug` accepts an optional integer `revision`. A matching revision, or an omitted revision, applies the update and increments the revision. A stale revision returns 409 with the current article; an invalid revision returns 422. Authentication, visibility, and ownership are checked before the revision. Article status cannot be changed through this route.

## Libraries and code

Rails provides routing, controllers, validations, associations, migrations, and JSON views. `pg` connects Active Record to PostgreSQL; `puma` serves HTTP; `bootsnap` speeds boot; `bcrypt` backs `has_secure_password`; `jwt` signs authentication tokens; `jbuilder` renders the contract's JSON shapes; `rack-cors` handles cross-origin requests; `rubocop-rails-omakase` checks the default Rails style.

Models in `app/models` hold the domain relationships and validations. `ApplicationController` handles token authentication and common errors; controllers in `app/controllers/api` handle endpoint flow. Jbuilder views in `app/views/api` define responses. `db/migrate` defines the schema, and `bin/check` is the acceptance gate. The unused deployment, CI, and generated framework files were removed after generating the scaffold.

## Spec choices

Article slugs use the title plus a random suffix so duplicate titles remain distinct; changing a title changes its slug. Tokens expire after 30 days. Tags keep their article order; `/api/tags` lists tags attached to a currently published article, so draft-only and orphaned tags are omitted. Email and username uniqueness are case sensitive. Article lists default to 20 entries and omit `body`. Empty `bio` and `image` values become `null`. Duplicate email or username returns 409, as the Hurl suite requires. For protected comment and favorite routes without a token, authentication takes precedence over article visibility, matching the original suite.
