## 1
Answer: The title is lowercased, runs of non-ASCII letters or digits become hyphens, and leading or trailing hyphens are removed; the first eight characters of a generated UUID are appended. Changing the title generates a new slug; omitting or leaving the title unchanged does not.
Where: `lib/conduit/content/article.ex` — `slug_from_title/1`
Confidence: high

## 2
Answer: A duplicate email or username returns HTTP 409 with `{"errors":{"email":["has already been taken"]}}` or the equivalent `username` field; both fields can appear if both conflict. The fallback decides the status and response body from the changeset errors.
Where: `lib/conduit/accounts/user.ex` — `registration_changeset/2`; `lib/conduit_web/controllers/fallback_controller.ex` — `call/2`
Confidence: high

## 3
Answer: The feed contains articles by users the authenticated viewer follows. It orders them by creation time descending, then article ID descending, before applying pagination.
Where: `lib/conduit/content.ex` — `feed/2`, `page/2`
Confidence: high

## 4
Answer: `favoritesCount` is a database count of users associated with the article through the `favorites` join table.
Where: `lib/conduit_web/presenter.ex` — `article/3`; `lib/conduit/content.ex` — `favorites_count/1`
Confidence: high

## 5
Answer: The request returns HTTP 403 with `{"errors":{"comment":["forbidden"]}}`.
Where: `lib/conduit_web/controllers/comment_controller.ex` — `delete/2`, `owner/2`; `lib/conduit_web/controllers/fallback_controller.ex` — `call/2`
Confidence: high

## 6
Answer: An empty string is treated as an empty value by Ecto’s `cast`, so the stored `bio` becomes `nil`.
Where: `lib/conduit/accounts/user.ex` — `update_changeset/2`
Confidence: high

## 7
Answer: Tags are stored as a string array in each article’s `tag_list` column. `GET /api/tags` flattens those arrays, removes duplicates, and returns the tags sorted ascending.
Where: `priv/repo/migrations/20260927021412_create_conduit.exs` — `change/0`; `lib/conduit/content.ex` — `tags/0`
Confidence: high

## 8
Answer: The default `limit` is 20. The code accepts nonnegative integers, including zero, and sets no maximum.
Where: `lib/conduit/content.ex` — `page/2`, `positive_integer/2`
Confidence: high

## 9
Answer: Joken creates a token signed with HS256 using the endpoint’s `secret_key_base`; its `sub` claim contains the user ID as a string. Expiry comes from Joken’s default claims, and this directory does not specify a lifetime.
Where: `lib/conduit/accounts.ex` — `token/1`, `signer/0`, `token_claims/0`
Confidence: high

## 10
Answer: The controller checks that the current user’s ID equals the article’s `author_id` before either update or delete proceeds.
Where: `lib/conduit_web/controllers/article_controller.ex` — `update/2`, `delete/2`, `owner/2`
Confidence: high

## 11
Answer: Omitting `tagList` leaves the existing tags unchanged. Sending `"tagList": null` adds a validation error, `"can't be blank"`, for `tagList`.
Where: `lib/conduit/content/article.ex` — `changeset/2`, `reject_null_tags/2`
Confidence: high

## 12
Answer: Passwords are stored as bcrypt hashes in `password_hash`; the plaintext `password` field is virtual. The `bcrypt_elixir` library supplies `Bcrypt.hash_pwd_salt/1`.
Where: `lib/conduit/accounts/user.ex` — `hash_password/1`, `schema "users"`; `mix.exs` — `deps/0`
Confidence: high

Files read: 12