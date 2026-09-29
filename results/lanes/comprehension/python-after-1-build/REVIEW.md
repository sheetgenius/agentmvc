# Python after step 1: comprehension review

**12/12** under the original rubric: each answer states the source behavior and cites its implementation location.

The answer key was saved before the fresh reader started, and its recorded SHA-256 matches the archived key. This is a qualitative review of source-supported answers, not a runtime acceptance test.

| Question | Score | Source-supported finding |
| --- | --- | --- |
| 1 | 1 | Slug construction and regeneration — `conduit/models.py: Article.set_title; conduit/api.py: create_article, update_article` |
| 2 | 1 | Duplicate identity status and body — `conduit/api.py: register, unique_user, api_error` |
| 3 | 1 | Followed-author feed and descending order — `conduit/api.py: feed; conduit/models.py: Article.Meta` |
| 4 | 1 | Favorite relation count — `conduit/api.py: article_data; conduit/models.py: Article.favorites` |
| 5 | 1 | Comment ownership error — `conduit/api.py: delete_comment, owned, api_error` |
| 6 | 1 | Empty bio becomes null — `conduit/api.py: update_user, user_data` |
| 7 | 1 | PostgreSQL array; sorted distinct global tags — `conduit/models.py: Article.tags; conduit/api.py: list_tags` |
| 8 | 1 | Default 20, no maximum, negative clamped to zero — `conduit/api.py: list_articles, feed, article_page` |
| 9 | 1 | HS256, user subject and 30-day expiry — `conduit/api.py: token_for; config/settings.py: SECRET_KEY` |
| 10 | 1 | Article author check on update/delete — `conduit/api.py: owned, update_article, delete_article` |
| 11 | 1 | Omitted tags preserved; null returns 422 — `conduit/api.py: update_article, api_error` |
| 12 | 1 | Django Argon2 via argon2-cffi; PBKDF2 also configured — `conduit/api.py: register, update_user; config/settings.py: PASSWORD_HASHERS; pyproject.toml: dependencies` |

[Reader answer](answer.md) · [Pre-saved key](answer-key.md) · [Itemized grade](grades.json) · [Run and tokens](run.json) · [Isolation proof](isolation.json)

One earlier preparation probe exposed writable dummy files when the permission profile inherited workspace access. It was stopped before a comprehension reader launched. Its record is preserved in `../python-after-1-build-isolation-attempt1/`; the measured reader used a fresh home extending the read-only profile and passed all seven isolation checks.
