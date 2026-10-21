# syntax=docker/dockerfile:1
FROM conduit-v9-toolchain:62835d93aa0a
COPY case/ /case/
RUN roundhouse --target spinel -o /build /case
WORKDIR /build
RUN spin build -- --cc=clang --jobs=8
ENV PORT=8080 SPINEL_WORKERS=4
ENTRYPOINT ["sh", "-c", "set -- build/bin/*; exec \"$1\" --binding 0.0.0.0"]
