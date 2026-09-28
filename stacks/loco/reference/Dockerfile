FROM rust:1.95-bookworm AS build
WORKDIR /app
COPY conduit/ .
RUN cargo build --release --bin conduit-cli

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /app/target/release/conduit-cli /app/conduit-cli
COPY --from=build /app/config /app/config
ENV LOCO_ENV=production
CMD ["/app/conduit-cli", "start", "--server-and-worker"]
