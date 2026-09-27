## 1
Answer: `set_slug` combines the parameterized title with a random 12-character hex suffix. It runs when the title changes, so updating the title changes the slug.
Where: `app/models/article.rb` — `Article#set_slug`
Confidence: high

## 2
Answer: Registration returns HTTP 409 with `{"errors":{"email":["has already been taken"]}}` or the corresponding `username` error; both fields appear if both are taken. The model detects the conflict, and `render_validation` chooses the status and body.
Where: `app/models/user.rb` — `User` validations; `app/controllers/application_controller.rb` — `render_validation`
Confidence: high

## 3
Answer: The feed contains articles by users the authenticated user follows. It orders them by `created_at` descending, then `id` descending, before applying `limit` and `offset`.
Where: `app/controllers/api/articles_controller.rb` — `feed`, `list`; `app/models/article.rb` — `recent`
Confidence: high

## 4
Answer: `favoritesCount` is the count of the article’s associated favorites.
Where: `app/views/api/articles/_article.json.jbuilder` — article partial
Confidence: high

## 5
Answer: The request returns HTTP 403 with `{"errors":{"comment":["forbidden"]}}`.
Where: `app/controllers/api/comments_controller.rb` — `destroy`; `app/controllers/application_controller.rb` — `render_error`
Confidence: high

## 6
Answer: An empty string is normalized to `nil`, so the user’s bio is cleared.
Where: `app/models/user.rb` — `User` bio normalization
Confidence: high

## 7
Answer: Tags are rows in `tags`, linked to articles through `article_tags`; database indexes prevent duplicate tag names and duplicate article–tag pairs. `GET /api/tags` returns all tag names alphabetically, without duplicates.
Where: `db/migrate/20260927000000_create_conduit.rb` — `CreateConduit#change`; `app/controllers/api/tags_controller.rb` — `index`
Confidence: high

## 8
Answer: The default `limit` is 20. The code sets no maximum.
Where: `app/controllers/api/articles_controller.rb` — `list`
Confidence: high

## 9
Answer: The token is an HS256-signed JWT using Rails’ `secret_key_base`; it contains the user ID as `sub` and an `exp` timestamp 30 days after creation.
Where: `app/models/user.rb` — `token`
Confidence: high

## 10
Answer: `authorize_article` enforces the author check before article updates and deletes.
Where: `app/controllers/api/articles_controller.rb` — `authorize_article` and `before_action`
Confidence: high

## 11
Answer: Omitting `tagList` leaves the article’s tags unchanged. Sending `"tagList": null` returns HTTP 422 with `{"errors":{"tagList":["must be a list of nonempty strings"]}}`.
Where: `app/controllers/api/articles_controller.rb` — `update`, `invalid_tags?`
Confidence: high

## 12
Answer: Passwords are stored as hashes in `password_digest` through Rails’ `has_secure_password`, which uses the `bcrypt` library.
Where: `app/models/user.rb` — `User` (`has_secure_password`); `db/migrate/20260927000000_create_conduit.rb` — `CreateConduit#change`; `Gemfile` — `bcrypt` dependency
Confidence: high

Files read: 19.