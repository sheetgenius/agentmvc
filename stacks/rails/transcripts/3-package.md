# rails · 3-package

| | |
| --- | --- |
| Codex session | `01a0e0d3-8302-7381-a623-4baf25f35af4` |
| Started, finished (UTC) | 2026-09-27T03:05:53Z, 2026-09-27T03:15:20Z (567 s) |
| Exit code | 0 |
| Agent tokens (uncached input + output) | 76,620 |
| Prompt | [steps/3-package.md](../../../steps/3-package.md) |
| Raw events | [3-package.jsonl](3-package.jsonl) |

Outputs longer than 40 lines are cut here; the `.jsonl` file next to this one has them in full.

**Agent:**

I’ll read `ENVIRONMENT.md` and the app’s current production settings, then add the image and check script. I’ll track full and narrower check runs against your return limits.

```sh
$ /bin/zsh -lc "rg --files -g '"'!vendor/**'"' -g '"'!realworld_spec/**'"' -g '"'!.scaffold/**'"' -g '"'!tmp/**'"' -g '"'!log/**'"' -g '"'!coverage/**'"' | sort"
```
<details><summary>output (exit 0)</summary>

```
ENVIRONMENT.md
Gemfile
Gemfile.lock
README.md
Rakefile
app/controllers/api/articles_controller.rb
app/controllers/api/comments_controller.rb
app/controllers/api/profiles_controller.rb
app/controllers/api/sessions_controller.rb
app/controllers/api/tags_controller.rb
app/controllers/api/users_controller.rb
app/controllers/application_controller.rb
app/models/application_record.rb
app/models/article.rb
app/models/article_tag.rb
app/models/comment.rb
app/models/favorite.rb
app/models/follow.rb
app/models/tag.rb
app/models/user.rb
app/views/api/articles/_article.json.jbuilder
app/views/api/articles/conflict.json.jbuilder
app/views/api/articles/index.json.jbuilder
app/views/api/articles/show.json.jbuilder
app/views/api/comments/_comment.json.jbuilder
app/views/api/comments/index.json.jbuilder
app/views/api/comments/show.json.jbuilder
app/views/api/profiles/_profile.json.jbuilder
app/views/api/profiles/show.json.jbuilder
app/views/api/tags/index.json.jbuilder
app/views/api/users/show.json.jbuilder
bin/check
bin/rails
bin/rubocop
compose.yaml
config.ru
config/application.rb
config/boot.rb
config/database.yml
config/environment.rb
[... 10 more lines]
```

</details>

```sh
$ /bin/zsh -lc 'cat Gemfile config/database.yml config/puma.rb config/environments/production.rb config/application.rb bin/check compose.yaml README.md .dockerignore 2>/dev/null'
```
<details><summary>output (exit 1)</summary>

```
source "https://rubygems.org"

gem "rails", "~> 8.1.3"
gem "pg"
gem "puma"
gem "bootsnap", require: false
gem "bcrypt"
gem "jwt"
gem "jbuilder"
gem "rack-cors"

group :development, :test do
  gem "rubocop-rails-omakase", require: false
end
default: &default
  adapter: postgresql
  encoding: unicode
  pool: <%= ENV.fetch("RAILS_MAX_THREADS", 5) %>

development:
  <<: *default
  database: conduit_development

test:
  <<: *default
  database: conduit_test

production:
  <<: *default
  url: <%= ENV.fetch("DATABASE_URL") %>
threads_count = ENV.fetch("RAILS_MAX_THREADS", 3)
threads threads_count, threads_count
port ENV.fetch("PORT", 3000)
Rails.application.configure do
  config.enable_reloading = false
  config.eager_load = true
  config.consider_all_requests_local = false
  config.log_tags = [ :request_id ]
  config.logger = ActiveSupport::TaggedLogging.logger(STDOUT)
  config.log_level = ENV.fetch("RAILS_LOG_LEVEL", "info")
[... 94 more lines]
```

</details>

```sh
$ /bin/zsh -lc "ls -la && cat config/boot.rb bin/rails config/environments/development.rb config/environments/test.rb app/controllers/application_controller.rb .bundle/config 2>/dev/null && docker version --format '{{.Server.Version}}'"
```
<details><summary>output (exit 0)</summary>

```
total 80
drwxr-xr-x  24 user  staff   768 Sep 27 10:33 .
drwxr-xr-x  21 user  staff   672 Sep 27 11:05 ..
drwxr-xr-x   3 user  staff    96 Sep 27 10:13 .bundle
-rw-r--r--   1 user  staff    52 Sep 27 10:21 .rubocop.yml
-rw-r--r--   1 user  staff     6 Sep 27 10:12 .ruby-version
drwxr-xr-x  21 user  staff   672 Sep 27 10:12 .scaffold
-rw-r--r--   1 user  staff  1334 Sep 27 10:11 ENVIRONMENT.md
-rw-r--r--   1 user  staff   240 Sep 27 10:13 Gemfile
-rw-r--r--   1 user  staff  7057 Sep 27 10:14 Gemfile.lock
-rw-r--r--   1 user  staff  3536 Sep 27 10:57 README.md
-rw-r--r--   1 user  staff    67 Sep 27 10:19 Rakefile
drwxr-xr-x   5 user  staff   160 Sep 27 10:16 app
drwxr-xr-x   5 user  staff   160 Sep 27 10:21 bin
-rw-r--r--   1 user  staff   128 Sep 27 10:16 compose.yaml
drwxr-xr-x  11 user  staff   352 Sep 27 10:19 config
-rw-r--r--   1 user  staff    90 Sep 27 10:19 config.ru
drwxr-xr-x   4 user  staff   128 Sep 27 10:19 db
drwxr-xr-x   3 user  staff    96 Sep 27 10:12 lib
drwxr-xr-x   4 user  staff   128 Sep 27 10:16 log
drwxr-xr-x   2 user  staff    64 Sep 27 10:19 public
drwxr-xr-x   7 user  staff   224 Sep 27 10:33 realworld_spec
drwxr-xr-x   2 user  staff    64 Sep 27 10:19 script
drwxr-xr-x  12 user  staff   384 Sep 27 10:59 tmp
drwxr-xr-x   4 user  staff   128 Sep 27 10:13 vendor
ENV["BUNDLE_GEMFILE"] ||= File.expand_path("../Gemfile", __dir__)
require "bundler/setup"
require "bootsnap/setup"
#!/usr/bin/env ruby
APP_PATH = File.expand_path("../config/application", __dir__)
require_relative "../config/boot"
require "rails/commands"
Rails.application.configure do
  config.hosts << "host.docker.internal"
  config.enable_reloading = true
  config.eager_load = false
  config.consider_all_requests_local = true
  config.active_record.migration_error = :page_load
end
Rails.application.configure do
[... 48 more lines]
```

</details>

```sh
$ /bin/zsh -lc 'tail -25 Gemfile.lock && du -sh vendor/bundle && cat .ruby-version && cat db/schema.rb | head -25 && ls -la bin public'
```
<details><summary>output (exit 0)</summary>

```
PLATFORMS
  aarch64-linux
  aarch64-linux-gnu
  aarch64-linux-musl
  arm-linux-gnu
  arm-linux-musl
  arm64-darwin
  x86_64-darwin
  x86_64-linux
  x86_64-linux-gnu
  x86_64-linux-musl

DEPENDENCIES
  bcrypt
  bootsnap
  jbuilder
  jwt
  pg
  puma
  rack-cors
  rails (~> 8.1.3)
  rubocop-rails-omakase

BUNDLED WITH
   2.5.23
119M	vendor/bundle
3.3.2
# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[8.1].define(version: 2026_09_27_000001) do
[... 24 more lines]
```

</details>

**Agent:**

This is an API-only Rails app with Puma and a production `DATABASE_URL` setting already in place. I’ll package the gems in a build stage, run `db:prepare` at container startup, and use a fresh Docker network and PostgreSQL container for the production check.

```sh
$ /bin/zsh -lc "cat realworld_spec/bin/run-hurl && cat config/initializers/cors.rb && cat config/routes.rb | head -60 && docker image inspect ruby:3.3.2-slim-bookworm --format '{{.Id}}'"
```
<details><summary>output (exit 1)</summary>

```
#!/bin/sh
# Run the official RealWorld Hurl suite (pinned in ../api) plus every feature suite in ../features/*/hurl
# against a local backend.
#   bin/run-hurl PORT [path/to/file.hurl ...]   -> http://host.docker.internal:PORT (files call {{host}}/api/...)
#   BASE_URL=https://example bin/run-hurl - [files...]   -> any server root
# Paths are relative to the spec root, e.g. api/hurl/articles.hurl or features/drafts/hurl/drafts.hurl.
# The backend may bind 127.0.0.1; Docker Desktop routes host.docker.internal to it.
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:?usage: bin/run-hurl PORT [hurl files...]}"; shift
BASE_URL="${BASE_URL:-http://host.docker.internal:$PORT}"
UID_VAL="${UID_VAL:-$(date +%s)$$}"
cd "$ROOT"
[ $# -eq 0 ] && set -- api/hurl/*.hurl $(ls features/*/hurl/*.hurl 2>/dev/null)
exec docker run --rm -v "$ROOT:/spec:ro" -w /spec ghcr.io/orange-opensource/hurl:latest \
  --test --jobs 1 --variable "host=$BASE_URL" --variable "uid=$UID_VAL" "$@"
Rails.application.config.middleware.insert_before 0, Rack::Cors do
  allow do
    origins "*"
    resource "/api/*", headers: :any, methods: [ :get, :post, :put, :delete, :options ]
  end
end
Rails.application.routes.draw do
  namespace :api do
    post "users/login", to: "sessions#create"
    resources :users, only: :create
    resource :user, only: [ :show, :update ]
    get "user/drafts", to: "articles#drafts"
    resources :profiles, only: :show, param: :username do
      post :follow, on: :member
      delete :follow, on: :member, action: :unfollow
    end
    resources :articles, only: [ :index, :show, :create, :update, :destroy ], param: :slug do
      get :feed, on: :collection
      post :publish, on: :member
      post :favorite, on: :member
      delete :favorite, on: :member, action: :unfavorite
      resources :comments, only: [ :index, :create, :destroy ]
    end
    resources :tags, only: :index
[... 4 more lines]
```

</details>

```sh
$ /bin/zsh -lc "rg --files lib script config db -g '"'!*.log'"' | sort && cat config/database.yml && docker info --format '{{.OSType}} {{.Architecture}}'"
```
<details><summary>output (exit 0)</summary>

```
config/application.rb
config/boot.rb
config/database.yml
config/environment.rb
config/environments/development.rb
config/environments/production.rb
config/environments/test.rb
config/initializers/cors.rb
config/initializers/filter_parameter_logging.rb
config/puma.rb
config/routes.rb
db/migrate/20260927000000_create_conduit.rb
db/migrate/20260927000001_add_drafts_to_articles.rb
db/schema.rb
default: &default
  adapter: postgresql
  encoding: unicode
  pool: <%= ENV.fetch("RAILS_MAX_THREADS", 5) %>

development:
  <<: *default
  database: conduit_development

test:
  <<: *default
  database: conduit_test

production:
  <<: *default
  url: <%= ENV.fetch("DATABASE_URL") %>
linux aarch64
```

</details>

*Files changed:* `/work/app/.dockerignore` (add), `/work/app/Dockerfile` (add), `/work/app/bin/check-production` (add)

```sh
$ /bin/zsh -lc 'chmod +x bin/check-production && bin/check-production'
```
<details><summary>output (exit 1)</summary>

```
ERROR: failed to build: failed to update builder last activity time: open ~/.docker/buildx/activity/.tmp-orbstack3836213918: operation not permitted
```

</details>

**Agent:**

The first production check stopped before the image build: Docker tried to update Buildx state outside this workspace, where writes are blocked. I’m pointing Docker’s client state into `tmp/` and will rerun the check.

```sh
$ /bin/zsh -lc "docker context inspect --format '{{.Endpoints.docker.Host}}' && docker context show && docker buildx ls"
```
<details><summary>output (exit 0)</summary>

```
NAME/NODE                                             DRIVER/ENDPOINT                                           STATUS     BUILDKIT   PLATFORMS
default                                               docker                                                                          
 \_ default                                            \_ default                                               running    v0.29.0    linux/amd64 (+2), linux/arm64, linux/arm (+2), linux/ppc64le, (4 more)
orbstack*                                             docker                                                                          
 \_ orbstack                                           \_ orbstack                                              running    v0.29.0    linux/amd64 (+2), linux/arm64, linux/arm (+2), linux/ppc64le, (4 more)

[21 lines of unrelated output removed]
```

</details>

```sh
$ /bin/zsh -lc "docker image ls --format '{{.Repository}}:{{.Tag}}' | head -20 && docker ps --format '{{.Names}} {{.Status}}'"
```
<details><summary>output (exit 0)</summary>

```
[27 lines of unrelated output removed]
```

</details>

```sh
$ /bin/zsh -lc 'mkdir -p tmp/buildx && BUILDX_CONFIG="$PWD/tmp/buildx" docker buildx version'
```
<details><summary>output (exit 0)</summary>

```
github.com/docker/buildx v0.33.0 f7897eba028583e0071642db3c011e860444f8cf
```

</details>

```sh
$ /bin/zsh -lc 'mkdir -p tmp/docker-config && DOCKER_HOST="$(docker context inspect --format '"'{{.Endpoints.docker.Host}}')\" DOCKER_CONFIG=\""'$PWD/tmp/docker-config" docker build -t conduit-production-probe .'
```

*Files changed:* `/work/app/bin/check-production` (update)

**Agent:**

The Buildx state change worked; the image build is now installing the locked production gems. The build stage will compile native gems, while the runtime stage will carry only the app, installed gems, and PostgreSQL client library.

```sh
$ /bin/zsh -lc bin/check-production
```
<details><summary>output (exit 0)</summary>

```
#0 building with "orbstack" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 1.06kB done
#1 DONE 0.0s

#2 [internal] load metadata for docker.io/library/ruby:3.3.2-slim-bookworm
#2 DONE 4.2s

#3 [internal] load .dockerignore
#3 transferring context: 100B done
#3 DONE 0.0s

#4 [build  1/11] FROM docker.io/library/ruby:3.3.2-slim-bookworm@sha256:4d611590cb3dc3211dc2e42c87347970c0ae9f7ad9c3db17a121d5996296f8ff
#4 CACHED

#5 [internal] load build context
#5 transferring context: 31.37kB done
#5 DONE 0.1s

#6 [stage-1 2/6] RUN apt-get update && apt-get install -y --no-install-recommends libpq5 &&     useradd --create-home rails
#6 ...

#7 [build  2/11] WORKDIR /app
#7 DONE 0.1s

#8 [build  3/11] RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev
#8 0.624 Get:1 http://deb.debian.org/debian bookworm InRelease [151 kB]
#8 1.454 Get:2 http://deb.debian.org/debian bookworm-updates InRelease [55.4 kB]
#8 1.791 Get:3 http://deb.debian.org/debian-security bookworm-security InRelease [34.8 kB]
#8 2.930 Get:4 http://deb.debian.org/debian bookworm/main arm64 Packages [8689 kB]
#8 4.687 Get:5 http://deb.debian.org/debian bookworm-updates/main arm64 Packages [6936 B]
#8 4.860 Get:6 http://deb.debian.org/debian-security bookworm-security/main arm64 Packages [343 kB]
#8 5.189 Fetched 9280 kB in 5s (1832 kB/s)
#8 5.189 Reading package lists...
#8 5.403 Reading package lists...
#8 5.610 Building dependency tree...
#8 5.675 Reading state information...
#8 5.749 The following additional packages will be installed:
#8 5.749   binutils binutils-aarch64-linux-gnu binutils-common cpp cpp-12 dpkg dpkg-dev
[... 569 more lines]
```

</details>

**Agent:**

The container started with only `DATABASE_URL`, `SECRET_KEY_BASE`, and `PORT`, prepared a fresh schema, and passed all 15 Hurl files. I’m running the existing development and lint gate now. Then I’ll make the requested cleanup pass and rerun both gates.

```sh
$ /bin/zsh -lc bin/check
```
<details><summary>output (exit 0)</summary>

```
time="2026-09-27T11:11:22+08:00" level=warning msg="Warning: No resource found to remove for project \"app-check\"."
 Network app-check_default Creating 
 Network app-check_default Created 
 Container app-check-db-1 Creating 
 Container app-check-db-1 Created 
 Container app-check-db-1 Starting 
 Container app-check-db-1 Started 
 Container app-check-db-1 Waiting 
 Container app-check-db-1 Healthy 
Success api/hurl/articles.hurl (17 request(s) in 430 ms)
Success api/hurl/auth.hurl (20 request(s) in 507 ms)
Success api/hurl/comments.hurl (13 request(s) in 323 ms)
Success api/hurl/errors_articles.hurl (20 request(s) in 316 ms)
Success api/hurl/errors_auth.hurl (20 request(s) in 1888 ms)
Success api/hurl/errors_authorization.hurl (9 request(s) in 489 ms)
Success api/hurl/errors_comments.hurl (10 request(s) in 273 ms)
Success api/hurl/errors_profiles.hurl (6 request(s) in 228 ms)
Success api/hurl/favorites.hurl (9 request(s) in 303 ms)
Success api/hurl/feed.hurl (12 request(s) in 533 ms)
Success api/hurl/pagination.hurl (7 request(s) in 279 ms)
Success api/hurl/profiles.hurl (7 request(s) in 461 ms)
Success api/hurl/tags.hurl (4 request(s) in 255 ms)
Success features/drafts/hurl/drafts.hurl (23 request(s) in 691 ms)
Success features/drafts/hurl/errors_drafts.hurl (24 request(s) in 598 ms)
--------------------------------------------------------------------------------
Executed files:    15
Executed requests: 201 (26.4/s)
Succeeded files:   15 (100.0%)
Failed files:      0 (0.0%)
Duration:          7602 ms (0h:0m:7s:602ms)


41 files inspected, no offenses detected
 Container app-check-db-1 Stopping 
 Container app-check-db-1 Stopped 
 Container app-check-db-1 Removing 
 Container app-check-db-1 Removed 
 Network app-check_default Removing 
 Network app-check_default Removed
```

</details>

**Agent:**

Both gates are green: 15/15 Hurl files in each, with 41 files linted and no offenses in `bin/check`. In the cleanup pass, I found one useful image change: remove apt package indexes after installing packages in each stage. I’ll make that change, rerun both gates, then document the production command.

*Files changed:* `/work/app/Dockerfile` (update)

**Agent:**

The cleanup build is still running; removing apt indexes invalidated Docker’s cached gem layer, so Bundler is reinstalling the locked gems. Once it finishes, the script will start fresh PostgreSQL and run the full Hurl suite.

```sh
$ /bin/zsh -lc bin/check-production
```
<details><summary>output (exit 0)</summary>

```
#0 building with "orbstack" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 1.12kB done
#1 DONE 0.0s

#2 [internal] load metadata for docker.io/library/ruby:3.3.2-slim-bookworm
#2 DONE 1.8s

#3 [internal] load .dockerignore
#3 transferring context: 100B done
#3 DONE 0.0s

#4 [build  2/11] WORKDIR /app
#4 CACHED

#5 [build  1/11] FROM docker.io/library/ruby:3.3.2-slim-bookworm@sha256:4d611590cb3dc3211dc2e42c87347970c0ae9f7ad9c3db17a121d5996296f8ff
#5 CACHED

#6 [internal] load build context
#6 transferring context: 2.92kB done
#6 DONE 0.0s

#7 [stage-1 2/6] RUN apt-get update && apt-get install -y --no-install-recommends libpq5 &&     rm -rf /var/lib/apt/lists/* && useradd --create-home rails
#7 0.587 Get:1 http://deb.debian.org/debian bookworm InRelease [151 kB]
#7 1.421 Get:2 http://deb.debian.org/debian bookworm-updates InRelease [55.4 kB]
#7 1.635 Get:3 http://deb.debian.org/debian-security bookworm-security InRelease [34.8 kB]
#7 1.971 Get:4 http://deb.debian.org/debian bookworm/main arm64 Packages [8689 kB]
#7 3.703 Get:5 http://deb.debian.org/debian bookworm-updates/main arm64 Packages [6936 B]
#7 3.879 Get:6 http://deb.debian.org/debian-security bookworm-security/main arm64 Packages [343 kB]
#7 4.476 Fetched 9280 kB in 4s (2160 kB/s)
#7 4.476 Reading package lists...
#7 4.821 Reading package lists...
#7 5.176 Building dependency tree...
#7 5.296 Reading state information...
#7 5.449 The following additional packages will be installed:
#7 5.449   libldap-2.5-0 libsasl2-2 libsasl2-modules-db
#7 5.449 Recommended packages:
#7 5.449   libldap-common libsasl2-modules
#7 5.475 The following NEW packages will be installed:
[... 566 more lines]
```

</details>

```sh
$ /bin/zsh -lc bin/check
```
<details><summary>output (exit 0)</summary>

```
 Network app-check_default Creating 
 Network app-check_default Created 
 Container app-check-db-1 Creating 
 Container app-check-db-1 Created 
 Container app-check-db-1 Starting 
 Container app-check-db-1 Started 
 Container app-check-db-1 Waiting 
 Container app-check-db-1 Healthy 
Success api/hurl/articles.hurl (17 request(s) in 572 ms)
Success api/hurl/auth.hurl (20 request(s) in 705 ms)
Success api/hurl/comments.hurl (13 request(s) in 435 ms)
Success api/hurl/errors_articles.hurl (20 request(s) in 441 ms)
Success api/hurl/errors_auth.hurl (20 request(s) in 2432 ms)
Success api/hurl/errors_authorization.hurl (9 request(s) in 584 ms)
Success api/hurl/errors_comments.hurl (10 request(s) in 333 ms)
Success api/hurl/errors_profiles.hurl (6 request(s) in 276 ms)
Success api/hurl/favorites.hurl (9 request(s) in 375 ms)
Success api/hurl/feed.hurl (12 request(s) in 658 ms)
Success api/hurl/pagination.hurl (7 request(s) in 424 ms)
Success api/hurl/profiles.hurl (7 request(s) in 551 ms)
Success api/hurl/tags.hurl (4 request(s) in 285 ms)
Success features/drafts/hurl/drafts.hurl (23 request(s) in 781 ms)
Success features/drafts/hurl/errors_drafts.hurl (24 request(s) in 727 ms)
--------------------------------------------------------------------------------
Executed files:    15
Executed requests: 201 (20.9/s)
Succeeded files:   15 (100.0%)
Failed files:      0 (0.0%)
Duration:          9602 ms (0h:0m:9s:602ms)


41 files inspected, no offenses detected
 Container app-check-db-1 Stopping 
 Container app-check-db-1 Stopped 
 Container app-check-db-1 Removing 
 Container app-check-db-1 Removed 
 Network app-check_default Removing 
 Network app-check_default Removed
```

</details>

**Agent:**

The final cleanup version passed both gates again: 15/15 Hurl files in each, and RuboCop found no offenses. I’m adding the build and run instructions to the README now.

*Files changed:* `/work/app/README.md` (update)

**Agent:**

**Status:** DONE.

**Gate result:** `bin/check` exited 0: 15/15 Hurl files passed; RuboCop inspected 41 files with no offenses. `bin/check-production` exited 0: 15/15 Hurl files passed.

**What you added:**

- [Dockerfile](/work/app/Dockerfile): builds a production image in two stages.
- [.dockerignore](/work/app/.dockerignore): excludes local dependencies, generated files, and test fixtures from the build context.
- [bin/check-production](/work/app/bin/check-production): builds the image, tests it with fresh PostgreSQL, and cleans up.
- [README.md](/work/app/README.md): documents how to build and run the image.

**Production choices:** Puma serves on `0.0.0.0:$PORT` with the existing three-thread default; the database pool remains five connections. Rails logs tagged requests to stdout at info level. Startup runs `db:prepare` so an empty PostgreSQL database gets its schema. The image uses `ruby:3.3.2-slim-bookworm`, matching the project Ruby version, with build tools kept out of the runtime stage.

**Run counts:** `bin/check`: 2; `bin/check-production`: 3; narrower runs: 1 interrupted manual build probe; build failures hit: 1.

**Friction log:**

- Buildx first tried to write state outside the writable workspace; the script now stores that state under `tmp/`.
- The image’s Bundler version differed from the lockfile, requiring Bundler to download the locked version.
- Removing apt indexes invalidated the gem build cache, so the cleanup pass required a second full gem install.

**Agent-friendliness notes:** Rails conventions kept production startup to `db:prepare` and Puma. The existing production settings already covered eager loading and stdout logging; no application behavior needed changing.

