## Status

DONE.

## Gate result

| Gate | API Hurl files | Security checks | Formatter and linter | Exit code |
| --- | ---: | ---: | --- | ---: |
| `bin/check` | 16/16 | Not run by this gate | Both clean | 0 |
| `bin/check-production` | 16/16 | 13/13 | Not run by this gate | 0 |

## Where the feature landed

- [mix.exs](../7-add-background-job/mix.exs) and [mix.lock](../7-add-background-job/mix.lock): added and locked Oban.
- [config/config.exs](../7-add-background-job/config/config.exs): configured the PostgreSQL backed `exports` queue.
- [lib/conduit/application.ex](../7-add-background-job/lib/conduit/application.ex): starts Oban with the app.
- [priv/repo/migrations/20260927050000_add_article_exports.exs](../7-add-background-job/priv/repo/migrations/20260927050000_add_article_exports.exs): creates Oban’s tables and stored exports.
- [lib/conduit/exports/export.ex](../7-add-background-job/lib/conduit/exports/export.ex): defines the export record.
- [lib/conduit/exports.ex](../7-add-background-job/lib/conduit/exports.ex): creates requests and builds snapshots.
- [lib/conduit/exports/worker.ex](../7-add-background-job/lib/conduit/exports/worker.ex): runs the snapshot job.
- [lib/conduit_web/router.ex](../7-add-background-job/lib/conduit_web/router.ex) and [lib/conduit_web/controllers/export_controller.ex](../7-add-background-job/lib/conduit_web/controllers/export_controller.ex): expose the authenticated routes and responses.
- [README.md](../7-add-background-job/README.md): documents routes, rules, job operation, and spec choices.

## The job system

[Oban](https://oban.hexdocs.pm/installation.html) stores jobs in the app’s PostgreSQL database. Its `exports` queue processes up to two jobs concurrently. The app starts Oban alongside Phoenix in development and in the single production container; the export row and job are inserted in one transaction.

## Passes

1. Made oversized IDs return 404 and made snapshot write failures trigger job retries; both gates stayed green.
2. Reviewed the changed code and found nothing further worth changing. The README is current.

## Spec decisions

Exports use integer IDs. A job snapshots articles and comment counts when it runs, ordered by creation time then ID. If an author is deleted before its job runs, the cascaded export is gone and the job completes.

## Run counts

`bin/check`: 2; `bin/check-production`: 2; narrower compile and format run: 1. Compile or build failures: 0.

## Friction log

- The host has no Elixir toolchain, so compilation and formatting ran in Docker.
- The first production build fetched and compiled the dependency tree.
- Oban’s migration produced substantial SQL output, making gate logs harder to scan.
- Integer URL IDs needed an overflow guard to preserve the specified 404 response.

## Agent-friendliness notes

Phoenix routes and controllers kept HTTP behavior easy to locate; Ecto schemas and the `Exports` context kept storage and snapshot rules together. Oban supplied durable jobs without a separate service.