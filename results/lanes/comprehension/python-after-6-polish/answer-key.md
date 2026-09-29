# Python after step 6: source-derived answer key

Prepared from `stacks/python/6-polish/` before launching or consulting the fresh reader. Source snapshot SHA-256: `3925c29c4b236bd4c23ff0aee54551fef8851d26c77d651a197b15930f6d1723`.

## 1
`Article.set_title` sets the title and regenerates the slug as Django `slugify(title)[:220]` (fallback `article`), a hyphen, and the first 12 hex characters of a new UUID4. Creation calls it; an update calls it whenever the title field is supplied, including an unchanged title, so a supplied title regenerates the slug.
Where: `conduit/models.py` — `Article.set_title`; `conduit/articles.py` — `create_article`, `update_article`.

## 2
Ordinary duplicate registration returns 409 with `{"errors":{"username":["has already been taken"]}}` or the corresponding `email` key. `register` invokes `unique_user`, which checks username before email and raises `APIError`; the shared handler constructs the body. This is the explicit pre-insert duplicate check, not a claim about an unhandled concurrent uniqueness race.
Where: `conduit/accounts.py` — `register`, `unique_user`; `conduit/http.py` — `APIError`, `api_error`.

## 3
The authenticated feed selects published articles whose author is followed by the requesting user, ordered by descending creation time and then descending ID. It applies the requested offset/limit through `article_page`; ordering comes from the model default, not publication time.
Where: `conduit/articles.py` — `feed`, `article_page`; `conduit/models.py` — `ArticleQuerySet.published`, `Article.Meta`, `User.following`.

## 4
`article_data` uses an existing `favorites_count` annotation, otherwise `article.favorites.count()`. Queryset rendering adds that annotation with `Count("favorites")` in `with_viewer`; favorites are a many-to-many relation. This describes the actual query/serializer calculation without assuming every filtered query produces the same aggregate.
Where: `conduit/articles.py` — `article_data`, `article_page`, `article_or_404`; `conduit/models.py` — `ArticleQuerySet.with_viewer`, `Article.favorites`.

## 5
For an existing comment on an accessible published article, a nonauthor gets 403 and `{"errors":{"comment":["forbidden"]}}`. `delete_comment` calls `owned`, which compares `author_id` with the requesting user's primary key and raises `APIError`; no deletion occurs. Earlier article visibility/draft and missing-comment checks can return their own errors.
Where: `conduit/articles.py` — `delete_comment`, `owned`; `conduit/http.py` — `api_error`.

## 6
An explicitly empty bio is converted to Python `None`, saved as database NULL, and returned as JSON null. Omitted fields are excluded from the update.
Where: `conduit/accounts.py` — `update_user`, `user_data`; `conduit/models.py` — `User.bio`.

## 7
Tags are stored per article in a PostgreSQL `ArrayField` of `CharField(max_length=255)` values; create/update assigns the supplied list. `GET /api/tags` flattens only published articles' arrays, collects them in a set, and returns a sorted list, so the endpoint deduplicates and sorts tags even if stored arrays contain duplicates.
Where: `conduit/models.py` — `Article.tags`; `conduit/articles.py` — `create_article`, `update_article`, `list_tags`.

## 8
Article lists, feed, and user drafts default to limit 20. The shared `PageSize` annotation enforces a minimum of 0 and maximum of 1000; out-of-range input is rejected with 422 through the validation handler rather than clamped.
Where: `conduit/articles.py` — `list_articles`, `feed`, `user_drafts`; `conduit/http.py` — `PageSize`, `validation_error`.

## 9
PyJWT encodes an HS256 JWT signed with Django's configured secret. Claims are `sub` containing the user primary key as a string and `exp` set to current UTC time plus 30 days. `user_data` generates a token for returned user representations; `viewer` decodes using HS256. The secret is read from the environment variable `SECRET_KEY_BASE`.
Where: `conduit/accounts.py` — `token_for`, `user_data`, `viewer`; `config/settings.py` — `SECRET_KEY`; `pyproject.toml` — PyJWT dependency.

## 10
`update_article` and `delete_article` authenticate the user, fetch the article, and call `owned(article, request.auth, "article")`; it compares the article's `author_id` with the user's primary key and raises 403 if different. `article_or_404` also hides another user's draft with 404 before that author check.
Where: `conduit/articles.py` — `update_article`, `delete_article`, `owned`, `article_or_404`.

## 11
Updates use `model_dump(exclude_unset=True)`, so omitted `tagList` is absent and preserves existing tags. Explicit null is present and fails the list-of-strings validation, producing 422 with `{"errors":{"tagList":["is invalid"]}}`; an empty list is accepted and clears the tags.
Where: `conduit/articles.py` — `ArticleChanges`, `update_article`; `conduit/http.py` — `api_error`.

## 12
Passwords are stored as Django password hashes using `create_user` on registration and `set_password` on changes; login uses `check_password`. `Argon2PasswordHasher` is first in `PASSWORD_HASHERS`, so new hashes use Argon2 through `argon2-cffi`; Django's PBKDF2 hasher is also configured for checking compatible stored hashes.
Where: `conduit/accounts.py` — `register`, `update_user`, `login`; `conduit/models.py` — `User(AbstractUser)`; `config/settings.py` — `PASSWORD_HASHERS`; `pyproject.toml` — `argon2-cffi` dependency.
