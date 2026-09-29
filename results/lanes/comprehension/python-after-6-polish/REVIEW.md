# Python after step 6: comprehension review

**12/12** under the original rubric: each answer states the source behavior and cites its implementation location.

The fresh source-derived key was saved before the reader started, and its SHA-256 matches the archived key. All seven isolation checks passed. The published source identity and the complete read-only source inventory were unchanged after the reader. This is a qualitative source review, not a runtime acceptance test.

| Question | Score | Source-supported finding |
| --- | --- | --- |
| 1 | 1 | Slug generation and regeneration — `conduit/models.py: Article.set_title; conduit/articles.py: update_article` |
| 2 | 1 | Duplicate identity error — `conduit/accounts.py: unique_user, register; conduit/http.py: api_error` |
| 3 | 1 | Published followed-author feed — `conduit/articles.py: feed; conduit/models.py: ArticleQuerySet.published, Article.Meta` |
| 4 | 1 | Favorite count calculation — `conduit/models.py: ArticleQuerySet.with_viewer; conduit/articles.py: article_data` |
| 5 | 1 | Comment ownership error — `conduit/articles.py: delete_comment, owned; conduit/http.py: api_error` |
| 6 | 1 | Empty bio becomes null — `conduit/accounts.py: update_user` |
| 7 | 1 | Array tags and global tag response — `conduit/models.py: Article.tags; conduit/articles.py: list_tags` |
| 8 | 1 | List limit bounds — `conduit/articles.py: list_articles, feed, user_drafts; conduit/http.py: PageSize` |
| 9 | 1 | Token claims and expiry — `conduit/accounts.py: token_for` |
| 10 | 1 | Article author enforcement — `conduit/articles.py: owned, update_article, delete_article` |
| 11 | 1 | Omitted versus null tags — `conduit/articles.py: update_article; conduit/http.py: api_error` |
| 12 | 1 | Password hashing — `conduit/accounts.py: register, update_user; conduit/models.py: User; config/settings.py: PASSWORD_HASHERS; pyproject.toml: dependencies` |

The favorite-count answer identifies the implemented annotation and relation-count fallback; its comprehension score does not resolve the separately reviewed favorite-filter behavior.

[Reader answer](answer.md) · [Pre-saved key](answer-key.md) · [Key preparation](key-preparation.json) · [Itemized grade](grades.json) · [Run and tokens](run.json) · [Isolation proof](isolation.json)
