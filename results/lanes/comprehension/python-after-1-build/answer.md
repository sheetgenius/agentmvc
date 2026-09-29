## 1
Answer: The slug is the slugified title, truncated to 220 characters, followed by a hyphen and 12 hexadecimal characters from a UUID. Updating the title calls `set_title` again, so the slug changes.
Where: `conduit/models.py` — `Article.set_title`; `conduit/api.py` — `create_article`, `update_article`
Confidence: high

## 2
Answer: Registration returns HTTP 409 with `{"errors":{"email":["has already been taken"]}}` or the same body with `username` as the key. `unique_user` detects the duplicate, and `api_error` formats the response.
Where: `conduit/api.py` — `register`, `unique_user`, `api_error`
Confidence: high

## 3
Answer: The feed contains articles by users the authenticated user follows. Articles are ordered by newest `created_at` first, then highest ID first.
Where: `conduit/api.py` — `feed`, `article_page`; `conduit/models.py` — `Article.Meta`
Confidence: high

## 4
Answer: `favoritesCount` is the count of users in the article’s `favorites` relationship.
Where: `conduit/api.py` — `article_data`; `conduit/models.py` — `Article.favorites`
Confidence: high

## 5
Answer: The request returns HTTP 403 with `{"errors":{"comment":["forbidden"]}}`.
Where: `conduit/api.py` — `delete_comment`, `owned`, `api_error`
Confidence: high

## 6
Answer: An empty string for `bio` is converted to `None`, saved as null, and returned as `null` in the user response.
Where: `conduit/api.py` — `update_user`, `user_data`; `conduit/models.py` — `User.bio`
Confidence: high

## 7
Answer: Each article stores its tags in a PostgreSQL array of strings, defaulting to an empty list. `GET /api/tags` returns all tags across articles, sorted and without duplicates.
Where: `conduit/models.py` — `Article.tags`; `conduit/api.py` — `list_tags`
Confidence: high

## 8
Answer: Both article list endpoints default `limit` to 20. The code sets no maximum; a negative limit yields an empty page.
Where: `conduit/api.py` — `list_articles`, `feed`, `article_page`
Confidence: high

## 9
Answer: PyJWT creates an HS256 token signed with the configured secret key. It contains the user’s ID as a string in `sub` and an `exp` timestamp 30 days after creation.
Where: `conduit/api.py` — `token_for`; `config/settings.py` — `SECRET_KEY`
Confidence: high

## 10
Answer: Both update and delete call `owned`, which rejects a user whose ID differs from the article author’s ID.
Where: `conduit/api.py` — `owned`, `update_article`, `delete_article`
Confidence: high

## 11
Answer: Omitting `tagList` leaves the existing tags unchanged. Sending `"tagList": null` returns HTTP 422 with `{"errors":{"tagList":["is invalid"]}}`.
Where: `conduit/api.py` — `update_article`, `api_error`
Confidence: high

## 12
Answer: Passwords are stored as hashes through Django’s authentication system: registration uses `create_user`, and password updates use `set_password`. The configured primary hasher is Django’s Argon2 password hasher, backed by `argon2-cffi`, with PBKDF2 also configured.
Where: `conduit/api.py` — `register`, `update_user`; `config/settings.py` — `PASSWORD_HASHERS`; `pyproject.toml` — `dependencies`
Confidence: high

Files read: 5.