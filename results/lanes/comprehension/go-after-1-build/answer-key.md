# Go after step 1: source-derived comprehension answer key

Prepared from published `stacks/go/1-build` source before the reader was launched or any reader answer was consulted. Source snapshot SHA-256: `ae1eb48dee777acd34d455c203bf06fb61c1343000f57d6e57a5d1d5ded43078`. This is a qualitative source review, not an executed behavior probe. Grading: 1 point for correct behavior and location, 0.5 for correct behavior with wrong or missing location, 0 otherwise. Equivalent descriptions and sufficient neighboring implementation citations are accepted.

## 1
Answer: The slug helper lowercases the title, replaces runs outside ASCII `a-z0-9` with hyphens, trims edge hyphens, and uses `article` if empty. It appends eight cryptographically random bytes encoded as 16 hex characters. Creation invokes it; update regenerates the slug only when a supplied valid title differs from the stored title.
Where: `internal/conduit/articles.go` — `slug`, `nonSlug`, `App.createArticle`, `App.updateArticle`.

## 2
Answer: PostgreSQL's unique constraints reject duplicate username/email values. Registration passes insert errors to `userConflict`, which maps SQLSTATE 23505 to HTTP 409 with `{"errors":{"username":["has already been taken"]}}` or the `email` key when the constraint name contains `email`; `route` renders the JSON error envelope.
Where: `internal/conduit/users.go` — `App.register`, `userConflict`; `internal/conduit/http.go` — `App.route`; `internal/platform/migrations/00001_conduit.sql` — `users` unique columns.

## 3
Answer: The authenticated user's feed includes articles whose author IDs are followed IDs in the `follows` rows where the viewer is the follower. Results are ordered by `created_at DESC, id DESC` before pagination.
Where: `internal/conduit/articles.go` — `App.feed`, `App.articleList`; `internal/conduit/http.go` — `New` registers the feed as authenticated.

## 4
Answer: `articleView` counts rows in the `favorites` table for that article ID. The composite primary key on `(user_id, article_id)` limits each user to one favorite for the article.
Where: `internal/conduit/models.go` — `App.articleView`, `Favorite`; `internal/platform/migrations/00001_conduit.sql` — `favorites`.

## 5
Answer: For a comment belonging to the requested article, a different authenticated author gets HTTP 403 with `{"errors":{"comment":["forbidden"]}}`. `deleteComment` compares the comment author ID with the viewer and returns the `forbidden` error that the route wrapper serializes.
Where: `internal/conduit/comments.go` — `App.deleteComment`; `internal/conduit/http.go` — `forbidden`, `App.route`.

## 6
Answer: Explicit empty `bio` becomes a nil pointer, is saved as SQL NULL, and is serialized as JSON null. An omitted `bio` leaves the previous pointer untouched; explicit JSON null also sets it to nil.
Where: `internal/conduit/users.go` — `App.updateUser`, `App.userResponse`; `internal/conduit/http.go` — `nullableString`; `internal/conduit/models.go` — `User.Bio`.

## 7
Answer: Tags are stored in `article_tags` rows with article ID, text tag, and position; `(article_id, tag)` is the primary key. Input tags are deduplicated while preserving their first occurrence and article serialization reads them by position. `GET /api/tags` selects distinct tag values across the table ordered by tag ascending.
Where: `internal/platform/migrations/00001_conduit.sql` — `article_tags`; `internal/conduit/articles.go` — `tagField`, `App.replaceTags`, `App.tags`; `internal/conduit/models.go` — `ArticleTag`, `App.articleView`.

## 8
Answer: The default limit is 20 for missing, invalid, or negative input. There is no upper clamp in this application; the parsed value is passed to Bun's query `Limit`. The code also defaults missing/invalid/negative offset to zero.
Where: `internal/conduit/articles.go` — `pagination`, `App.articleList`.

## 9
Answer: `App.token` builds a `golang-jwt/jwt/v5` HS256 JWT signed with the application's secret. Its registered claims contain `sub` as the decimal user ID and an expiration 30 times 24 hours after issuance. `authenticate` accepts a `Token` header, checks the signing method, parses claims, and resolves the subject to a user.
Where: `internal/conduit/http.go` — `App.token`, `App.authenticate`, `New`; `internal/conduit/users.go` — `App.userResponse`.

## 10
Answer: Update and delete both call `ownedArticle`, which loads by slug and compares `Article.AuthorID` with `viewer(r).ID`; a mismatch returns a 403 article-forbidden error before mutation.
Where: `internal/conduit/articles.go` — `App.ownedArticle`, `App.updateArticle`, `App.deleteArticle`; `internal/conduit/http.go` — `forbidden`.

## 11
Answer: Omitting `tagList` makes `tagField` return `present=false`, so update does not replace tags. Explicit null yields a nil slice and returns `invalid("tagList")`, resulting in HTTP 422 with `{"errors":{"tagList":["can't be blank"]}}`. A supplied empty list is valid and clears the tags.
Where: `internal/conduit/articles.go` — `tagField`, `App.updateArticle`, `App.replaceTags`; `internal/conduit/http.go` — `invalid`, `App.route`.

## 12
Answer: The app SHA-256 hashes the password, hex-encodes that digest, then bcrypt-hashes the 64-character result at `bcrypt.DefaultCost` using `golang.org/x/crypto/bcrypt`. It stores the resulting bcrypt string in `users.password_hash`; login checks the same digest with `CompareHashAndPassword`. This preprocessing avoids bcrypt's 72-byte input limit for multibyte passwords.
Where: `internal/conduit/users.go` — `passwordDigest`, `passwordHash`, `App.register`, `App.updateUser`, `App.login`; `internal/conduit/models.go` — `User.PasswordHash`; `internal/platform/migrations/00001_conduit.sql` — `users.password_hash`.
