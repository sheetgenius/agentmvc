# syntax=docker/dockerfile:1
FROM conduit-v9-toolchain:3d66ee698bdf AS build
ARG CASE
WORKDIR /build
COPY ${CASE}/ ./
RUN spin build -- --cc=clang --jobs=8 \
 && mkdir -p /runtime/static /runtime/public /runtime/db /runtime/config /runtime/storage \
 && set -- build/bin/* && test "$#" -eq 1 && install -m755 "$1" /runtime/server && strip /runtime/server \
 && for dir in static public db config; do if [ -d "$dir" ]; then cp -a "$dir/." "/runtime/$dir/"; fi; done
FROM conduit-v9-app:compiled
COPY --from=build --chown=10001:10001 /runtime/ /app/
