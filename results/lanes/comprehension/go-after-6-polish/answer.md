## 1
Answer: The title is lowercased, runs of non-alphanumeric characters become hyphens, and leading or trailing hyphens are removed; an empty result becomes `article`. An 8-byte random hex suffix is added. Changing the title generates a new slug; an update that leaves the title unchanged does not.
Where: internal/conduit/articles.go — `slug`, `createArticle`, `updateArticle`
Confidence: high

## 2
Answer: A database uniqueness violation returns HTTP 409 with `{"errors":{"email":["has already been taken"]}}` or `{"errors":{"username":["has already been taken"]}}`. The constraint name determines the field, and the route wrapper formats the body.
Where: internal/conduit/users.go — `userConflict`, `register`; internal/conduit/http.go — `route`
Confidence: high

## 3
Answer: The feed contains published articles by users the authenticated requester follows. It is ordered by `created_at` descending, then article ID descending, with pagination applied.
Where: internal/conduit/articles.go — `feed`, `articleList`
Confidence: high

## 4
Answer: `favoritesCount` is the count of rows in `favorites` for that article; it is zero when there are no rows.
Where: internal/conduit/views.go — `articleViews`
Confidence: high

## 5
Answer: Deleting another user's comment returns HTTP 403 with `{"errors":{"comment":["forbidden"]}}`.
Where: internal/conduit/comments.go — `deleteComment`; internal/conduit/http.go — `forbidden`, `route`
Confidence: high

## 6
Answer: An empty string sets `bio` to `nil`, so it is stored as SQL `NULL` and returned as JSON `null`.
Where: internal/conduit/users.go — `updateUser`; internal/conduit/http.go — `nullableString`
Confidence: high

## 7
Answer: Tags are rows in `article_tags`, keyed by article ID and tag, with a `position` recording their order. `GET /api/tags` returns distinct tags from published articles in ascending tag order.
Where: internal/platform/migrations/00001_conduit.sql — `article_tags` table; internal/conduit/articles.go — `addTags`, `tags`
Confidence: high

## 8
Answer: The default `limit` is 20 when it is missing, invalid, or negative. There is no maximum enforced by this code.
Where: internal/conduit/articles.go — `pagination`, `articleList`
Confidence: high

## 9
Answer: The token is a JWT signed with HS256 using the app secret. Its registered claims contain the user's numeric ID as `sub` and an `exp` set to 30 days after creation.
Where: internal/conduit/http.go — `token`
Confidence: high

## 10
Answer: `ownedArticle` compares the article's `AuthorID` with the requester's ID and returns a forbidden error if they differ; both update and delete call it.
Where: internal/conduit/articles.go — `ownedArticle`, `updateArticle`, `deleteArticle`
Confidence: high

## 11
Answer: Omitting `tagList` leaves the existing tags unchanged. Sending `"tagList": null` is rejected with HTTP 422 and `{"errors":{"tagList":["can't be blank"]}}`.
Where: internal/conduit/articles.go — `tagField`, `updateArticle`; internal/conduit/http.go — `invalid`, `route`
Confidence: high

## 12
Answer: Passwords are SHA-256 hashed, hex encoded, then hashed with bcrypt at its default cost; the resulting bcrypt hash is stored in `password_hash`. Bcrypt comes from `golang.org/x/crypto/bcrypt`.
Where: internal/conduit/users.go — `passwordDigest`, `passwordHash`; internal/conduit/models.go — `User`
Confidence: high

Files read: 8.