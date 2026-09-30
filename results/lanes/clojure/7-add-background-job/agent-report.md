## Status

DONE.

## Gate result

`bin/check` and `bin/check-production` both exited **0**. Each passed **16/16 Hurl files** and **13/13 security checks**. The development gate also passed formatting, linting, and tests.

## Where the feature landed

- [deps.edn](/work/app/deps.edn): added Proletarian.
- [src/conduit/exports.clj](/work/app/src/conduit/exports.clj): creates exports, builds snapshots, and presents results.
- [src/conduit/http.clj](/work/app/src/conduit/http.clj): added authenticated export routes.
- [src/conduit/system.clj](/work/app/src/conduit/system.clj): starts and stops the worker with the app.
- [src/conduit/store.clj](/work/app/src/conduit/store.clj): shares timestamp formatting.
- [src/conduit/articles.clj](/work/app/src/conduit/articles.clj): uses the shared timestamp formatter.
- [003-proletarian.up.sql](/work/app/resources/migrations/003-proletarian.up.sql): creates the durable queue schema.
- [003-proletarian.down.sql](/work/app/resources/migrations/003-proletarian.down.sql): removes that schema on rollback.
- [004-exports.up.sql](/work/app/resources/migrations/004-exports.up.sql): creates export storage.
- [004-exports.down.sql](/work/app/resources/migrations/004-exports.down.sql): removes export storage on rollback.
- [proletarian-MIT.txt](/work/app/resources/licenses/proletarian-MIT.txt): preserves the queue schema’s license.
- [README.md](/work/app/README.md): documents routes, jobs, and spec choices.

## The job system

[Proletarian](https://github.com/msolli/proletarian) stores jobs in PostgreSQL. Export creation and enqueueing share a transaction. Integrant starts one worker after migrations and before HTTP; development and the single production container run it in the web process. It polls every 250 ms and gives handler failures three delayed retries.

## Passes

1. Added retries and made repeated jobs skip completed exports; both gates remained green.
2. Reviewed the final code and README, found no worthwhile further change, and stopped.

## Spec decisions

IDs are numeric. An author with no articles gets an empty array. The snapshot reflects articles when the job reads them, ordered by creation time and ID. Deleting a user removes their exports.

## Run counts

`bin/check`: 2; `bin/check-production`: 2. Narrower toolchain runs: 5. Compile failures: 0; production build failures: 0.

## Friction log

- The earlier snapshot had removed the queue, so its dependency, schema, and lifecycle needed restoring.
- Proletarian’s connection and retry API needed checking to keep enqueueing atomic and failures retryable.
- Muuntaja encodes JSON as a stream, requiring conversion before JSONB storage.
- `git status` was unavailable because the local developer tools path was invalid; final files were inspected directly.

## Agent-friendliness notes

The small domain namespaces, Integrant dependency graph, and numbered migrations made the feature easy to locate and wire. The PostgreSQL JSONB boundary and queue library API required the most inspection.