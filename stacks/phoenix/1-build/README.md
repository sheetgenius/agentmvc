# Conduit API

Phoenix and Ecto implementation of the [RealWorld API](realworld_spec/docs/endpoints.md). `bin/check` starts a fresh PostgreSQL, runs all 13 official Hurl files, checks formatting and compiles with warnings treated as errors.

## Run

```sh
export HOST_UID=$(id -u) HOST_GID=$(id -g)
docker compose up -d --wait db
docker compose run --rm app sh -lc 'mix deps.get && mix ecto.create && mix ecto.migrate'
docker compose up app
```

The API listens on `http://localhost:4102/api`. Stop it with `docker compose down -v`.

## Libraries and code

- Phoenix routes requests and renders JSON; Bandit serves HTTP; Jason encodes JSON.
- Ecto SQL and Postgrex persist users, articles, comments, follows and favorites in PostgreSQL.
- Bcrypt hashes passwords; Joken signs and validates JWTs; CORSPlug handles browser preflights.

`Conduit.Accounts` owns users, credentials and follows. `Conduit.Content` owns articles, comments, favorites and tags. Their schemas hold validation. `ConduitWeb.Router` names the API; controllers handle HTTP; `Presenter` shapes responses; `Auth` and `FallbackController` handle shared authentication and errors.

## Spec choices

Slugs are title based with a random suffix, so duplicate titles remain distinct. Tags are stored in article order; the global tag list is distinct and sorted. JWTs expire after two hours; malformed tokens return 401. Follow and favorite operations are idempotent, and self follow is allowed. Lists default to 20 articles at offset zero and omit article bodies. Deletes return 204; invalid comment IDs return 404. CORS allows any origin. The Hurl suite settles behavior where the prose is ambiguous.
