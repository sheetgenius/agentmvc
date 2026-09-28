FROM elixir:1.18.4-otp-27
WORKDIR /app
ENV MIX_ENV=prod
RUN mix local.hex --force && mix local.rebar --force
COPY mix.exs mix.lock ./
RUN mix deps.get --only prod
COPY config config
COPY lib lib
COPY priv priv
RUN mix compile
EXPOSE 4102
CMD ["sh", "-c", "mix ecto.migrate && mix phx.server"]
