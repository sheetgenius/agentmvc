## 1
Answer: The title is lowercased, non-ASCII-letter-or-digit runs become hyphens, and an eight-character UUID prefix is appended. Changing the title during an update generates a new slug.
Where: `lib/conduit/content/article.ex` — `slug_from_title/1`, `update_changeset/2`
Confidence: high

## 2
Answer: A duplicate email or username returns HTTP 409 with `{"errors":{"email":["has already been taken"]}}` or the corresponding `username` error. The user changeset identifies the conflicting field; the fallback controller chooses the status and body.
Where: `lib/conduit/accounts/user.ex` — `validate_identity/1`; `lib/conduit_web/controllers/fallback_controller.ex` — `call/2`
Confidence: high

## 3
Answer: The feed contains published articles by users the viewer follows. It orders them by creation time descending, then article ID descending.
Where: `lib/conduit/content.ex` — `feed/2`, `page/3`
Confidence: high

## 4
Answer: `favoritesCount` is the number of rows in `favorites` for that article. Article lists preload those counts; other responses count them when rendered.
Where: `lib/conduit/content.ex` — `listing_data/2`, `favorite_stats/2`; `lib/conduit_web/presenter.ex` — `article/3`
Confidence: high

## 5
Answer: The request returns HTTP 403 with `{"errors":{"comment":["forbidden"]}}`.
Where: `lib/conduit/content.ex` — `delete_comment/2`, `ensure_author/2`; `lib/conduit_web/controllers/fallback_controller.ex` — `call/2`
Confidence: high

## 6
Answer: An empty string for `bio` is cast to `nil`, clearing the stored bio.
Where: `lib/conduit/accounts/user.ex` — `update_changeset/2`
Confidence: high

## 7
Answer: Tags are stored in each article’s `tag_list` string array column. `GET /api/tags` collects tags from published articles, removes duplicates, and returns them sorted ascending.
Where: `priv/repo/migrations/20260927021412_create_conduit.exs` — `change/0`; `lib/conduit/content.ex` — `tags/0`
Confidence: high

## 8
Answer: `limit` defaults to 20 and has a maximum accepted value of 100. Values above 100 fall back to 20.
Where: `lib/conduit/content.ex` — `page/3`, `nonnegative_integer/3`
Confidence: high

## 9
Answer: The token is an HS256 signed JWT using the endpoint’s `secret_key_base`. It contains the user ID as a string `sub` plus Joken’s default time claims, including an `exp` that expires two hours after issue; `iss`, `aud`, and `jti` are skipped.
Where: `lib/conduit/accounts.ex` — `token/1`, `signer/0`, `token_claims/0`
Confidence: medium

## 10
Answer: Both update and delete call `ensure_author/2`, which rejects an article when its `author_id` differs from the current user’s ID.
Where: `lib/conduit/content.ex` — `update_article/3`, `delete_article/2`, `ensure_author/2`
Confidence: high

## 11
Answer: Omitting `tagList` preserves the existing tags. Sending `"tagList": null` adds a validation error, returned as `{"errors":{"tagList":["can't be blank"]}}` with HTTP 422.
Where: `lib/conduit/content/article.ex` — `changeset/2`, `reject_null_tags/2`; `lib/conduit_web/controllers/fallback_controller.ex` — `call/2`, `error_field/1`
Confidence: high

## 12
Answer: Passwords are stored as bcrypt hashes in `password_hash`; the plaintext `password` field is virtual. The `bcrypt_elixir` library supplies `Bcrypt.hash_pwd_salt/1`.
Where: `lib/conduit/accounts/user.ex` — `hash_password/1`, `Conduit.Accounts.User` schema; `mix.exs` — `deps/0`
Confidence: high

Files read: 13