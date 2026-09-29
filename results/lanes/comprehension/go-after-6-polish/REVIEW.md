# Go after step 6: comprehension review

**12/12** under the original rubric: each answer states the source behavior and cites its implementation location.

The fresh source-derived key was saved before the reader started, and its SHA-256 matches the archived key. All seven isolation checks passed. The published source identity and the complete read-only source inventory were unchanged after the reader. This is a qualitative source review, not a runtime acceptance test.

| Question | Score | Source-supported finding |
| --- | --- | --- |
| 1 | 1 | Slug generation and title-change behavior — `internal/conduit/articles.go: slug, createArticle, updateArticle` |
| 2 | 1 | Duplicate identity error — `internal/conduit/users.go: userConflict, register; internal/conduit/http.go: route` |
| 3 | 1 | Published followed-author feed — `internal/conduit/articles.go: feed, articleList` |
| 4 | 1 | Favorite count aggregation — `internal/conduit/views.go: articleViews` |
| 5 | 1 | Comment ownership error — `internal/conduit/comments.go: deleteComment; internal/conduit/http.go: forbidden, route` |
| 6 | 1 | Empty bio becomes null — `internal/conduit/users.go: updateUser; internal/conduit/http.go: nullableString` |
| 7 | 1 | Normalized tags and tag listing — `internal/platform/migrations/00001_conduit.sql: article_tags; internal/conduit/articles.go: addTags, tags` |
| 8 | 1 | List limit behavior — `internal/conduit/articles.go: pagination, articleList` |
| 9 | 1 | Token claims and expiry — `internal/conduit/http.go: token` |
| 10 | 1 | Article author enforcement — `internal/conduit/articles.go: ownedArticle, updateArticle, deleteArticle` |
| 11 | 1 | Omitted versus null tags — `internal/conduit/articles.go: tagField, updateArticle; internal/conduit/http.go: invalid, route` |
| 12 | 1 | Password prehashing and bcrypt — `internal/conduit/users.go: passwordDigest, passwordHash; internal/conduit/models.go: User` |

[Reader answer](answer.md) · [Pre-saved key](answer-key.md) · [Key preparation](key-preparation.json) · [Itemized grade](grades.json) · [Run and tokens](run.json) · [Isolation proof](isolation.json)
