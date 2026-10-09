# syntax=docker/dockerfile:1
FROM ruby:4.0.7-slim AS base
WORKDIR /rails
ENV RAILS_ENV=production BUNDLE_DEPLOYMENT=1 BUNDLE_PATH=/usr/local/bundle \
    BUNDLE_WITHOUT=development:test RUBY_YJIT_ENABLE=1
RUN apt-get update -qq && apt-get install --no-install-recommends -y \
    libpq5 ca-certificates && rm -rf /var/lib/apt/lists/*

FROM base AS build
RUN apt-get update -qq && apt-get install --no-install-recommends -y \
    build-essential libpq-dev git && rm -rf /var/lib/apt/lists/*
COPY Gemfile Gemfile.lock ./
RUN bundle install && rm -rf /usr/local/bundle/ruby/*/cache
COPY . .
RUN bundle exec bootsnap precompile -j 1 --gemfile && \
    bundle exec bootsnap precompile -j 1 app/ lib/

FROM base
RUN groupadd --system --gid 1000 rails && \
    useradd rails --uid 1000 --gid 1000 --create-home
COPY --from=build --chown=rails:rails /usr/local/bundle /usr/local/bundle
COPY --from=build --chown=rails:rails /rails /rails
USER rails:rails
EXPOSE 4109
ENTRYPOINT ["/rails/bin/docker-entrypoint"]
CMD ["./bin/rails", "server", "-b", "0.0.0.0"]
