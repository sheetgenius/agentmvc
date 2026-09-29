FROM agentmvc-servant-v2-toolchain:preflight AS build
WORKDIR /work/app
COPY . .
RUN cabal build exe:conduit && \
    install -Dm755 "$(cabal list-bin exe:conduit)" /out/conduit && \
    ldd /out/conduit

FROM debian:bookworm-slim@sha256:3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libffi8 libgmp10 libnuma1 libpq5 libssl3 libtinfo6 zlib1g && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /out/conduit /app/conduit
COPY migrations /app/migrations
EXPOSE 4105
CMD ["/app/conduit"]
