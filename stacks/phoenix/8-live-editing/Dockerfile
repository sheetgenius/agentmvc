FROM elixir:1.18.4-otp-27 AS build

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

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libatomic1 libncurses6 libssl3 libstdc++6 \
    && apt-get clean && rm -r /var/lib/apt/lists/* \
    && groupadd --system conduit && useradd --system --gid conduit conduit

WORKDIR /app
COPY --from=build --chown=conduit:conduit /app/_build/prod/rel/conduit ./
USER conduit

CMD ["/bin/sh", "-c", "bin/conduit eval 'Conduit.Release.migrate()' && exec bin/conduit start"]
