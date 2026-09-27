# Feature: article drafts, publishing and edit conflicts

This extends the RealWorld backend spec. Everything in the base spec still holds, and the original 13 Hurl files must keep passing. The acceptance tests for this feature are in `hurl/drafts.hurl` and `hurl/errors_drafts.hurl`. As with the base spec, where the prose and the suite disagree, the suite wins.

## Article fields

Every article representation (single article, list entries, create and update responses) gains three fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `status` | `"draft"` or `"published"` | The article's lifecycle state. |
| `publishedAt` | ISO 8601 string, or `null` | When the article was first published. `null` while it is a draft. |
| `revision` | integer | Starts at `1`. Increases by 1 on every successful update and on publishing a draft. |

## Creating an article

`POST /api/articles` accepts an optional `status` in the `article` object:
- It may be `"draft"` or `"published"`, and defaults to `"published"`, so existing clients are unaffected.
- A published article gets `publishedAt` set at creation. A draft has `publishedAt: null`.
- Any other `status` value fails with `422`: `{"errors": {"status": ["is invalid"]}}`.

## Who can see a draft

A draft is visible only to its author. To anyone else, including anonymous requests, it does not exist:

- `GET`, `PUT` and `DELETE /api/articles/:slug` return `404` with `{"errors": {"article": ["not found"]}}`.
- Its comments endpoints, its favorite endpoints and its publish endpoint return that same `404`.

**Lists never include drafts, for any viewer, the author included.** This covers:
- `GET /api/articles` with any filters;
- `GET /api/articles/feed`;
- the `articlesCount` in both.

`GET /api/tags` omits tags that appear only on drafts.

The author can read, update and delete their own draft as usual.

A draft can't be commented on or favorited, even by its author. The author gets `422` with `{"errors": {"article": ["is a draft"]}}`.

## Publishing

`POST /api/articles/:slug/publish` requires authentication:

| Case | Response |
| --- | --- |
| Author publishes a draft | `200` with the article: `status: "published"`, `publishedAt` set, `revision` increased by 1 |
| Author publishes an already published article | `200` with the article unchanged: same `publishedAt`, same `revision` |
| Another user, article is a draft | `404` (the draft is invisible) |
| Another user, article is published | `403` with `{"errors": {"article": ["forbidden"]}}` |
| No token | `401` with `{"errors": {"token": ["is missing"]}}` |
| Unknown slug | `404` with `{"errors": {"article": ["not found"]}}` |

Once published, the article appears in lists, feeds and tags like any other. There is no unpublishing.

## The current user's drafts

`GET /api/user/drafts` requires authentication and returns only the current user's drafts:
- The response shape is the same as `GET /api/articles`: `{"articles": [...], "articlesCount": n}`, with `body` omitted from each entry.
- Newest first.
- It supports `limit` and `offset` like the article list.
- Without a token it returns `401`.

## Edit conflicts

`PUT /api/articles/:slug` accepts an optional integer `revision` in the `article` object:

- **No `revision`:** the update applies as before, and the revision increases by 1.
- **`revision` equals the current revision:** the update applies, and the revision increases by 1.
- **`revision` differs from the current revision:** nothing changes. The response is `409` with the error and the current article:

  ```json
  {"errors": {"revision": ["is stale"]}, "article": { "...": "the current article" }}
  ```
- **`revision` is not an integer:** `422` with `{"errors": {"revision": ["is invalid"]}}`.

The checks run in this order, and the first failure wins:
1. authentication (`401`);
2. the article exists and is visible (`404`);
3. ownership (`403`);
4. revision (`409` or `422`);
5. field validation (`422`).
