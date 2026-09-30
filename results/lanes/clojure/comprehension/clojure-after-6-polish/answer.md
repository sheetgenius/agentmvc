## 1
Answer: The title is lowercased, runs of non-alphanumeric characters become hyphens, and the first eight characters of a random UUID are appended. Updating the title generates a new slug.
Where: `src/conduit/articles.clj` — `slug`, `create!`, `update!`
Confidence: high

## 2
Answer: Registration returns HTTP 409 with `{"errors":{"email":["has already been taken"]}}` or the same body keyed by `username`. The availability check raises the error, and the HTTP wrapper turns it into the response.
Where: `src/conduit/users.clj` — `available!`, `register!`; `src/conduit/http.clj` — `wrap-api`
Confidence: high

## 3
Answer: The feed contains published articles by authors the authenticated user follows, subject to any supplied author, tag, or favorited filters. It is ordered by creation time descending, then article ID descending.
Where: `src/conduit/http.clj` — `handler`; `src/conduit/articles.clj` — `listing`, `article-page`
Confidence: high

## 4
Answer: `favoritesCount` is the count of rows in `favorites` for that article.
Where: `src/conduit/articles.clj` — `present-many`, `article-response`
Confidence: high

## 5
Answer: Once the comment is found, a user who is not its author gets HTTP 403 with `{"errors":{"comment":["forbidden"]}}`.
Where: `src/conduit/articles.clj` — `delete-comment!`; `src/conduit/domain.clj` — `owned`; `src/conduit/http.clj` — `wrap-api`
Confidence: high

## 6
Answer: An empty string for `bio` is converted to `nil`, so the update stores SQL `NULL`.
Where: `src/conduit/users.clj` — `update!`
Confidence: high

## 7
Answer: Tags are stored as rows in `article_tags` with an article ID, tag text, and position; duplicate tags in an article’s input are removed. `GET /api/tags` returns distinct tags from published articles, ordered by tag.
Where: `resources/migrations/001-conduit.up.sql` — `article_tags` table; `src/conduit/articles.clj` — `replace-tags!`, `all-tags`
Confidence: high

## 8
Answer: The default `limit` is 20. There is no maximum in the code; negative values are clamped to zero.
Where: `src/conduit/articles.clj` — `page-size`, `article-page`
Confidence: high

## 9
Answer: The token is a JWT signed with the configured secret using `buddy.sign.jwt`. It contains the user’s ID and an `exp` timestamp 30 days after creation.
Where: `src/conduit/users.clj` — `token`
Confidence: high

## 10
Answer: Both update and delete compare the article’s author ID with the current user’s ID before changing it.
Where: `src/conduit/articles.clj` — `update!`, `delete!`; `src/conduit/domain.clj` — `owned`
Confidence: high

## 11
Answer: Omitting `tagList` leaves the article’s tags unchanged. Sending `"tagList": null` fails validation with HTTP 422 and `{"errors":{"tagList":["is invalid"]}}`.
Where: `src/conduit/articles.clj` — `update!`, `valid-tags`; `src/conduit/http.clj` — `wrap-api`
Confidence: high

## 12
Answer: Passwords are stored in `users.password_hash` using `buddy.hashers/derive`; login checks them with `buddy.hashers/check`.
Where: `src/conduit/users.clj` — `register!`, `update!`, `login!`
Confidence: high

Files read: 7.