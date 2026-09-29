## 1
Answer: The slug is the first 220 characters of the slugified title (or `article` if empty), followed by a 12-character UUID suffix. Supplying a title in an update generates a new slug, even if the title is unchanged.
Where: `conduit/models.py` — `Article.set_title`; `conduit/articles.py` — `update_article`
Confidence: high

## 2
Answer: A duplicate email or username returns HTTP 409 with `{"errors":{"email":["has already been taken"]}}` or the same body with `username` as the key.
Where: `conduit/accounts.py` — `unique_user`, `register`; `conduit/http.py` — `api_error`
Confidence: high

## 3
Answer: The feed contains published articles by users the requester follows, ordered by newest `created_at` first, then highest article ID first.
Where: `conduit/articles.py` — `feed`; `conduit/models.py` — `ArticleQuerySet.published`, `Article.Meta`
Confidence: high

## 4
Answer: `favoritesCount` counts users in the article’s `favorites` relationship. List responses use an annotated `Count("favorites")`; otherwise the response helper calls `article.favorites.count()`.
Where: `conduit/models.py` — `ArticleQuerySet.with_viewer`; `conduit/articles.py` — `article_data`
Confidence: high

## 5
Answer: For an existing comment on a published article, a user who is not its author gets HTTP 403 with `{"errors":{"comment":["forbidden"]}}`.
Where: `conduit/articles.py` — `delete_comment`, `owned`; `conduit/http.py` — `api_error`
Confidence: high

## 6
Answer: An empty string sent for `bio` is converted to `None`, stored as null, and returned as `null`.
Where: `conduit/accounts.py` — `update_user`
Confidence: high

## 7
Answer: Each article stores its tags as a PostgreSQL array of strings. `GET /api/tags` returns tags from published articles only, sorted with duplicates removed.
Where: `conduit/models.py` — `Article.tags`; `conduit/articles.py` — `list_tags`
Confidence: high

## 8
Answer: Article lists default to `limit=20`; the maximum is `1000`.
Where: `conduit/articles.py` — `list_articles`, `feed`, `user_drafts`; `conduit/http.py` — `PageSize`
Confidence: high

## 9
Answer: The token is a JWT signed with `HS256` using `settings.SECRET_KEY`. It contains the user ID as a string in `sub` and an `exp` set to 30 days after creation.
Where: `conduit/accounts.py` — `token_for`
Confidence: high

## 10
Answer: Both update and delete call `owned`, which rejects a user whose ID differs from the article author’s ID.
Where: `conduit/articles.py` — `owned`, `update_article`, `delete_article`
Confidence: high

## 11
Answer: Omitting `tagList` leaves the existing tags unchanged. Sending `"tagList": null` returns HTTP 422 with `{"errors":{"tagList":["is invalid"]}}`.
Where: `conduit/articles.py` — `update_article`; `conduit/http.py` — `api_error`
Confidence: high

## 12
Answer: Passwords are stored as Django authentication hashes through `create_user` and `set_password`. Django is configured to use its Argon2 hasher first, backed by `argon2-cffi`, with a PBKDF2 hasher also configured.
Where: `conduit/accounts.py` — `register`, `update_user`; `conduit/models.py` — `User`; `config/settings.py` — `PASSWORD_HASHERS` module; `pyproject.toml` — dependencies
Confidence: high

Files read: 7.