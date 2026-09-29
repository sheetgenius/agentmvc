# Go after step 1: comprehension review

**12/12** under the original rubric: each answer states the source behavior and cites its implementation location.

The answer key was saved before the fresh reader started, and its recorded SHA-256 matches the archived key. This is a qualitative review of source-supported answers, not a runtime acceptance test.

| Question | Score | Source-supported finding |
| --- | --- | --- |
| 1 | 1 | Normalized title, random suffix, regenerated on changed title — `internal/conduit/articles.go: slug, updateArticle` |
| 2 | 1 | Unique constraint produces 409 identity error — `internal/conduit/users.go: register, userConflict; internal/conduit/http.go: route` |
| 3 | 1 | Followed-author feed, creation and ID descending — `internal/conduit/articles.go: feed, articleList` |
| 4 | 1 | Favorite rows counted for article — `internal/conduit/models.go: articleView` |
| 5 | 1 | Non-author comment deletion returns 403 — `internal/conduit/comments.go: deleteComment; internal/conduit/http.go: forbidden, route` |
| 6 | 1 | Empty bio becomes database and JSON null — `internal/conduit/users.go: updateUser; internal/conduit/http.go: nullableString` |
| 7 | 1 | article_tags rows, per-article deduplication, global distinct sorting — `internal/conduit/articles.go: tagField, replaceTags, tags; internal/platform/migrations/00001_conduit.sql: article_tags` |
| 8 | 1 | Default 20, no upper clamp — `internal/conduit/articles.go: pagination` |
| 9 | 1 | HS256 token, user ID subject, 30-day expiration — `internal/conduit/http.go: token` |
| 10 | 1 | Shared article author check on update/delete — `internal/conduit/articles.go: ownedArticle, updateArticle, deleteArticle` |
| 11 | 1 | Omitted tags unchanged; null returns 422 blank error — `internal/conduit/articles.go: tagField, updateArticle; internal/conduit/http.go: invalid, route` |
| 12 | 1 | SHA-256 hex digest then x/crypto bcrypt at DefaultCost — `internal/conduit/users.go: passwordDigest, passwordHash` |

[Reader answer](answer.md) · [Pre-saved key](answer-key.md) · [Itemized grade](grades.json) · [Run and tokens](run.json) · [Isolation proof](isolation.json)

All seven isolation checks passed before this fresh reader ran. The source copy was unchanged afterward. Total and cached input are retained beside uncached-plus-output so cache variation is visible.
