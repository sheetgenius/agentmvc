# Feature: article exports, built in a background job

This extends the RealWorld backend spec and the drafts feature. Everything in both still holds, and the 15 existing Hurl files must keep passing. The acceptance tests for this feature are in `hurl/exports.hurl`. As with the base spec, where the prose and the suite disagree, the suite wins.

An export is a stored snapshot of all of the current user's articles, drafts included. A background job builds it.

## How exports run

- **Outside the request.** Building an export happens in a background job, never inside the HTTP request that asks for it.
- **The stack's standard, durable job system,** backed by the app's own PostgreSQL database. A queued export must survive an app restart. Don't add Redis or any other service.
- **One production container.** It runs the web server and processes jobs, with the same environment as before: only `DATABASE_URL`, `SECRET_KEY_BASE` and `PORT`. `bin/check-production` must pass, including this feature's tests.

## Starting an export

`POST /api/user/exports` requires authentication and takes no body.

| Case | Response |
| --- | --- |
| Authenticated | `202` with the new export: `status: "pending"`, `completedAt: null`, `articles: null` |
| No token | `401` with `{"errors": {"token": ["is missing"]}}` |

## Reading an export

`GET /api/user/exports/:id` requires authentication. It returns `200` with `{"export": {...}}`:

| Field | Meaning |
| --- | --- |
| `id` | An opaque identifier, a string or an integer. |
| `status` | `"pending"` until the job finishes, then `"done"`. |
| `createdAt` | When the export was requested, as ISO 8601. |
| `completedAt` | When the job finished, as ISO 8601. `null` while pending. |
| `articles` | `null` while pending. Once done: every article the user had authored when the job ran, drafts included, oldest first. |

Each exported article has exactly these fields:
- `slug`, `title`, `description`, `body`;
- `tagList`;
- `status`;
- `commentsCount`: the number of comments on the article when the job ran.

A finished export is a snapshot. Articles created, changed or deleted afterwards don't change it.

| Case | Response |
| --- | --- |
| Another user's export, or any `:id` that doesn't identify one of the current user's exports, including a malformed one | `404` with `{"errors": {"export": ["not found"]}}` |
| No token | `401` with `{"errors": {"token": ["is missing"]}}` |
