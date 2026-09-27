# syntax=docker/dockerfile:1
FROM rust:1.95-bookworm AS build
WORKDIR /app
COPY conduit/ .
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/app/target \
    cargo build --release --locked && cp target/release/conduit-cli /conduit-cli

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates libssl3 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /conduit-cli ./conduit-cli
COPY --from=build /app/config/production.yaml ./config/production.yaml
USER 10001:10001
CMD ["sh", "-c", "./conduit-cli db migrate --environment production && exec ./conduit-cli start --environment production --server-and-worker"]
