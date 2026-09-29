# Go after step 6: source-derived answer key

Prepared from `stacks/go/6-polish/` before launching or consulting the fresh reader. Source snapshot SHA-256: `89cfb6da7535d4f61ca60ff579591f652a080dd15fb919c89350cabdffddeb36`.

## 1
`slug` lowercases the title, replaces runs outside ASCII `a-z0-9` with hyphens, trims edge hyphens, and uses `article` if the base is empty. It appends a hyphen and 8 cryptographically random bytes as 16 hex digits. Creation generates the slug; updating it regenerates only when a supplied title differs from the stored title, not for an omitted or identical title.
Where: `internal/conduit/articles.go` — `nonSlug`, `slug`, `createArticle`, `updateArticle`.

## 2
Duplicate registration fails the database UNIQUE constraint and returns HTTP 409 with `{"errors":{"email":["has already been taken"]}}` or the corresponding `username` key. `userConflict` recognizes PostgreSQL error code `23505`, selects email when the constraint name contains `email` and otherwise username; `route` serializes the resulting API error.
Where: `internal/conduit/users.go` — `register`, `userConflict`; `internal/conduit/http.go` — `App.route`; `internal/platform/migrations/00001_conduit.sql` — unique user columns.

## 3
The authenticated feed selects published articles whose author ID is in the requesting user's followed IDs in `follows`. It orders by `created_at DESC, id DESC` and applies pagination; it does not order by publication time.
Where: `internal/conduit/articles.go` — `feed`, `articleList` (`followedArticles` scope); `internal/conduit/http.go` — `New` feed route.

## 4
`articleViews` queries all favorite rows for the returned article IDs, groups by `article_id`, and uses `count(*) AS favorites_count`. It copies that aggregate into each view's `FavoritesCount`; articles without a group get zero from the missing map entry. The composite primary key on favorites permits one favorite per user/article pair.
Where: `internal/conduit/views.go` — `App.articleViews`, `App.articleView`; `internal/platform/migrations/00001_conduit.sql` — favorites table.

## 5
For an existing comment on an accessible article, a requester with a different author ID receives HTTP 403 and `{"errors":{"comment":["forbidden"]}}`, and the comment is not deleted. Parent-article visibility and missing-comment checks occur first.
Where: `internal/conduit/comments.go` — `App.deleteComment`; `internal/conduit/http.go` — `forbidden`, `App.route`.

## 6
An explicitly empty bio string becomes a nil pointer, is stored as SQL NULL, and is returned as JSON null. Omitted bio is untouched; `nullableString` also accepts explicit null as nil.
Where: `internal/conduit/users.go` — `App.updateUser`; `internal/conduit/http.go` — `nullableString`; `internal/conduit/models.go` — `User.Bio`, `UserView.Bio`.

## 7
Tags are normalized into `article_tags` rows with `article_id`, `tag`, and input `position`, with primary key `(article_id, tag)`. Input parsing removes duplicate tags while retaining first occurrence order; article responses sort rows by position. `GET /api/tags` joins published articles, selects distinct tag values, and orders by tag ascending, excluding tags found only on drafts.
Where: `internal/platform/migrations/00001_conduit.sql` — article_tags table; `internal/conduit/articles.go` — `tagField`, `addTags`, `replaceTags`, `App.tags`; `internal/conduit/views.go` — `App.articleViews`.

## 8
The default limit is 20, used when the value is absent, fails integer parsing, or is negative. There is no explicit maximum limit enforced by application code; the parsed nonnegative value is passed to Bun's `Limit`.
Where: `internal/conduit/articles.go` — `pagination`, `App.articleList`.

## 9
The application uses `github.com/golang-jwt/jwt/v5` to sign an HS256 JWT with the application secret. Its registered claims contain the user ID as a decimal string subject and expiry 30 days after token creation. `userView` issues the token; startup obtains the secret from `SECRET_KEY_BASE` and `New` stores its bytes for signing.
Where: `internal/conduit/http.go` — `App.token`, `New`, `App.authenticate`; `internal/conduit/views.go` — `App.userView`; `cmd/server/main.go` — `run`; `go.mod` — JWT dependency.

## 10
Both `updateArticle` and `deleteArticle` call `ownedArticle`, which first loads a visible article and then rejects a mismatched article `AuthorID` and requesting user ID with 403. Another user's draft may already be hidden by `visibleArticle` with 404.
Where: `internal/conduit/articles.go` — `App.ownedArticle`, `App.updateArticle`, `App.deleteArticle`, `App.visibleArticle`; `internal/conduit/http.go` — `forbidden`.

## 11
Omitted `tagList` returns `present=false` from `tagField`, so update preserves stored tag rows. Explicit null decodes to a nil slice and is rejected with HTTP 422 and `{"errors":{"tagList":["can't be blank"]}}`; an empty array is valid and replaces tags with none.
Where: `internal/conduit/articles.go` — `tagField`, `App.updateArticle`, `replaceTags`; `internal/conduit/http.go` — `invalid`, `App.route`.

## 12
The stored `users.password_hash` is a bcrypt hash from `golang.org/x/crypto/bcrypt` at `bcrypt.DefaultCost`. Before bcrypt, the application computes SHA-256 of the password bytes and hex-encodes the digest; login compares the same prehash against the stored bcrypt hash. Registration and password updates both call `passwordHash`, which also requires at least eight Unicode characters.
Where: `internal/conduit/users.go` — `passwordDigest`, `passwordHash`, `App.register`, `App.updateUser`, `App.authenticateCredentials`; `internal/conduit/models.go` — `User.PasswordHash`; `internal/platform/migrations/00001_conduit.sql` — users.password_hash; `go.mod` — crypto dependency.
