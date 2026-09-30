# syntax=docker/dockerfile:1
FROM eclipse-temurin:25-jdk-noble@sha256:f6366ccac38ceae180280ad7012d18a15e8031548a430dc2bae06631d9e88ed0 AS build
RUN apt-get update -qq && apt-get install --no-install-recommends -y curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*
RUN curl -fsSL --retry 5 https://github.com/clojure/brew-install/releases/download/1.12.5.1664/clojure-tools-1.12.5.1664.tar.gz -o /tmp/clojure.tar.gz && \
    echo '77dd6868948074adcc93e83a796f8e8f15a1a92bcb1b9002d715fd2210e476f3  /tmp/clojure.tar.gz' | sha256sum -c - && \
    tar xzf /tmp/clojure.tar.gz -C /tmp && \
    mkdir -p /usr/local/lib/clojure/libexec && \
    cp /tmp/clojure-tools/deps.edn /tmp/clojure-tools/example-deps.edn /tmp/clojure-tools/tools.edn /usr/local/lib/clojure/ && \
    cp /tmp/clojure-tools/*.jar /usr/local/lib/clojure/libexec/ && \
    sed 's@PREFIX@/usr/local/lib/clojure@g' /tmp/clojure-tools/clojure > /usr/local/bin/clojure && \
    chmod +x /usr/local/bin/clojure && rm -rf /tmp/clojure-tools /tmp/clojure.tar.gz
ENV JAVA_TOOL_OPTIONS="-XX:ActiveProcessorCount=2 -XX:MaxRAMPercentage=70"
WORKDIR /src
COPY deps.edn ./
RUN --mount=type=cache,target=/root/.m2 clojure -P -T:build && clojure -P
COPY . .
RUN --mount=type=cache,target=/root/.m2 clojure -T:build uber

FROM eclipse-temurin:25-jre-noble@sha256:693fdaf83831eeeefd9709eae44c8b8706622652f972cf5903bd0e481bbf6ad3
WORKDIR /app
COPY --from=build --chown=10001:10001 /src/target/conduit.jar /app/conduit.jar
USER 10001:10001
EXPOSE 4112
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=70", "-XX:ActiveProcessorCount=2", "-jar", "/app/conduit.jar"]
