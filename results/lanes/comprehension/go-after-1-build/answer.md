## 1
Answer: The title is lowercased, runs of non-alphanumeric characters become hyphens, and leading or trailing hyphens are removed. An 8-byte random hex suffix is added; updating the title to a different value generates a new slug.
Where: `internal/conduit/articles.go` — `slug`, `updateArticle`
Confidence: high

## 2
Answer: A duplicate email or username returns HTTP 409 with `{"errors":{"email":["has already been taken"]}}` or the same body with `username` as the key. The database uniqueness error is classified by `userConflict`, and `route` formats the response.
Where: `internal/conduit/users.go` — `userConflict`, `register`; `internal/conduit/http.go` — `route`
Confidence: high

## 3
Answer: The feed contains articles by users the authenticated viewer follows, ordered by creation time descending, then article ID descending. Pagination applies.
Where: `internal/conduit/articles.go` — `feed`, `articleList`
Confidence: high

## 4
Answer: `favoritesCount` is the number of rows in `favorites` for that article.
Where: `internal/conduit/models.go` — `articleView`
Confidence: high

## 5
Answer: The request returns HTTP 403 with `{"errors":{"comment":["forbidden"]}}`.
Where: `internal/conduit/comments.go` — `deleteComment`; `internal/conduit/http.go` — `forbidden`, `route`
Confidence: high

## 6
Answer: An empty string sets `bio` to null in the database and returns `"bio": null`.
Where: `internal/conduit/users.go` — `updateUser`; `internal/conduit/http.go` — `nullableString`
Confidence: high

## 7
Answer: Tags are stored as separate `article_tags` rows with an article ID, tag text, and position; duplicate tags for one article are removed. `GET /api/tags` returns distinct tag strings ordered ascending by tag.
Where: `internal/platform/migrations/00001_conduit.sql` — `article_tags` table; `internal/conduit/articles.go` — `tagField`, `replaceTags`, `tags`
Confidence: high

## 8
Answer: The default `limit` is 20, including when the value is invalid or negative. There is no maximum enforced by this code.
Where: `internal/conduit/articles.go` — `pagination`
Confidence: high

## 9
Answer: The token is an HS256-signed JWT using the app secret. Its subject is the user’s numeric ID, and it expires 30 days after creation.
Where: `internal/conduit/http.go` — `token`
Confidence: high

## 10
Answer: `ownedArticle` compares the article’s author ID with the viewer’s ID; both update and delete call it.
Where: `internal/conduit/articles.go` — `ownedArticle`, `updateArticle`, `deleteArticle`
Confidence: high

## 11
Answer: Omitting `tagList` leaves the existing tags untouched. Sending `"tagList": null` returns HTTP 422 with `{"errors":{"tagList":["can't be blank"]}}`.
Where: `internal/conduit/articles.go` — `tagField`, `updateArticle`; `internal/conduit/http.go` — `invalid`, `route`
Confidence: high

## 12
Answer: Passwords are SHA-256 hashed, hex encoded, then hashed with bcrypt at its default cost; the bcrypt result is stored in `password_hash`. The bcrypt implementation is `golang.org/x/crypto/bcrypt`.
Where: `internal/conduit/users.go` — `passwordDigest`, `passwordHash`
Confidence: high

Files read: 6.