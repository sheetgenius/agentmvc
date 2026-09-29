FROM elixir:1.18.4-otp-27@sha256:8f2dc555c30ca656694f6b91a5747a89de412fd69b1c6ca6fd7c63c56b729ef6 AS build

ENV MIX_ENV=prod
WORKDIR /app

RUN mix local.hex --force && mix local.rebar --force
COPY mix.exs mix.lock ./
COPY config config
RUN mix deps.get --only prod && mix deps.compile

COPY lib lib
COPY priv priv
COPY .formatter.exs .formatter.exs
RUN mix format --check-formatted && mix compile --warnings-as-errors && mix release

FROM debian:bookworm-slim@sha256:3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251

ENV LANG=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libatomic1 libncurses6 libssl3 libstdc++6 \
    && apt-get clean && rm -r /var/lib/apt/lists/* \
    && groupadd --system conduit && useradd --system --gid conduit conduit

WORKDIR /app
COPY --from=build --chown=conduit:conduit /app/_build/prod/rel/conduit ./
USER conduit

CMD ["/bin/sh", "-c", "bin/conduit eval 'Conduit.Release.migrate()' && exec bin/conduit start"]
