## Status: DONE

## Gate result

All **15/15 Hurl files** passed. Formatter and linter are clean. Final `bin/check` exit code: **0**.

## Where the feature landed

- [conduit/models.py](/work/app/conduit/models.py): added article status, publication time, revision, publishing, and a published article QuerySet.
- [conduit/api.py](/work/app/conduit/api.py): added draft visibility, routes, response fields, and revision conflict handling.
- [conduit/migrations/0002_article_published_at_article_revision_article_status.py](/work/app/conduit/migrations/0002_article_published_at_article_revision_article_status.py): added the three article fields.
- [README.md](/work/app/README.md): documented routes, rules, and spec choices.

## Passes

1. Centralized the published article filter and moved update field validation after access and revision checks; `bin/check` passed.
2. Reviewed the changed code and found nothing further worth changing; the final `bin/check` passed.

## Spec decisions

The author can list a draft’s comments as an empty list. Boolean revisions are invalid. Existing articles receive a `publishedAt` value when the migration runs because their original publication time was not recorded.

## Run counts

`bin/check`: **4 runs**—three green, one transient startup failure. Narrower Hurl runs: **0**; local validation and formatting commands: **9**. Compile or build failures: **0**.

## Friction log

- Ninja validates typed request fields before route code, so update fields needed validation inside the route to preserve the specified check order.
- Migration generation warned while the disposable database was unavailable, though it generated the migration.
- One final gate attempt failed during database and container startup; an immediate retry passed.

## Agent-friendliness notes

Django’s QuerySet, migration, and transaction conventions kept the domain rules easy to locate. Ninja’s early schema validation required care for the edit conflict precedence.