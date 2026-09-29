# Python after step 1: source-derived comprehension answer key

Prepared from the published `stacks/python/1-build` source before the reader was launched or any reader answer was consulted. Source snapshot SHA-256: `1de10bffe6d7ad94a3fae19b21a00ee45e0fca0650a8eb35f51427f8f5ec24ea`. This is a qualitative source review, not an executed behavior probe. Grading: 1 point for correct behavior and location, 0.5 for correct behavior with wrong or missing location, 0 otherwise. Equivalent descriptions and sufficient neighboring implementation citations are accepted.

## 1
Answer: The slug is Django `slugify(title)` truncated to 220 characters (or `article` if empty), followed by a hyphen and the first 12 hex characters of a fresh UUID4. Creation calls `set_title`; an update containing `title` calls it again, regenerating the slug even if the supplied title text is unchanged.
Where: `conduit/models.py` — `Article.set_title`; `conduit/api.py` — `create_article`, `update_article`.

## 2
Answer: Registration calls `unique_user` before creation. A duplicate username or email returns HTTP 409 with `{"errors":{"username":["has already been taken"]}}` or the corresponding `email` key; username is checked first if both collide. `APIError` carries the status/field/message, and its exception handler renders that JSON. Concurrent registration races are outside this question and are not promised to follow the pre-check path.
Where: `conduit/api.py` — `register`, `unique_user`, `APIError`, `api_error`.

## 3
Answer: The authenticated user's feed contains articles whose authors the user follows. They are ordered by `created_at` descending and then ID descending, inherited from the article model's ordering, before pagination.
Where: `conduit/api.py` — `feed`, `article_page`; `conduit/models.py` — `User.following`, `Article.Meta`.

## 4
Answer: The serializer calls `article.favorites.count()` on the article's many-to-many relation to users.
Where: `conduit/api.py` — `article_data`; `conduit/models.py` — `Article.favorites`.

## 5
Answer: For an existing comment on the requested article, a different authenticated author gets HTTP 403 and `{"errors":{"comment":["forbidden"]}}`. The ownership helper compares the resource author ID with the authenticated user ID; the exception handler formats the response.
Where: `conduit/api.py` — `delete_comment`, `owned`, `api_error`.

## 6
Answer: An explicitly supplied empty `bio` is converted to `None`, saved as database NULL, and returned as JSON null. Omitting `bio` leaves it unchanged because the update schema is dumped with `exclude_unset=True`.
Where: `conduit/api.py` — `update_user`, `user_data`; `conduit/models.py` — `User.bio`.

## 7
Answer: Each article stores its tags in a PostgreSQL array of strings using `ArrayField(CharField(max_length=255))`. `GET /api/tags` flattens the arrays across articles, deduplicates using a Python set, and sorts the strings ascending; it does not use a normalized tag table. The article array itself is assigned from input without that global deduplication step.
Where: `conduit/models.py` — `Article.tags`; `conduit/api.py` — `create_article`, `update_article`, `list_tags`.

## 8
Answer: Both list and feed default to 20. There is no upper limit imposed by this application; `article_page` clamps negative limits to zero and negative offsets to zero before slicing.
Where: `conduit/api.py` — `list_articles`, `feed`, `article_page`.

## 9
Answer: PyJWT signs an HS256 JWT with `settings.SECRET_KEY`, containing `sub` as the user's primary key converted to a string and `exp` set to the current UTC time plus 30 days. `viewer` accepts the `Token` authorization scheme and decodes with HS256; `user_data` creates a fresh token when serializing a user.
Where: `conduit/api.py` — `token_for`, `viewer`, `user_data`; `config/settings.py` — `SECRET_KEY`; `pyproject.toml` — PyJWT dependency.

## 10
Answer: Both article update and delete load the article then call `owned(article, request.auth, "article")`, which raises a 403 error unless its author ID equals the authenticated user's ID.
Where: `conduit/api.py` — `update_article`, `delete_article`, `owned`.

## 11
Answer: Omitting `tagList` leaves the existing tags unchanged due to `exclude_unset=True`. Explicit null reaches the update handler and produces HTTP 422 with `{"errors":{"tagList":["is invalid"]}}`; a supplied list replaces the array.
Where: `conduit/api.py` — `ArticleChanges`, `update_article`, `api_error`.

## 12
Answer: Password creation and changes use Django's password hashing machinery (`create_user` and `set_password`) on the custom `User(AbstractUser)` model; login uses `check_password`. Settings select Django's `Argon2PasswordHasher` first, backed by the declared `argon2-cffi` library, with `PBKDF2PasswordHasher` also enabled for compatible hashes. Passwords are stored as encoded hashes, not plaintext.
Where: `conduit/api.py` — `register`, `update_user`, `login`; `conduit/models.py` — `User`; `config/settings.py` — `PASSWORD_HASHERS`; `pyproject.toml` — `argon2-cffi` dependency.
