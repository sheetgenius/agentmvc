## 1
Answer: The slug is the parameterized title followed by a hyphen and 12 random hexadecimal characters. It is regenerated when the title changes, including on an update.
Where: [app/models/article.rb](../../stacks/rails/6-polish/app/models/article.rb#L11) — `Article#set_slug` and its `before_validation` callback
Confidence: high

## 2
Answer: Registration returns HTTP 409 Conflict with a body such as `{"errors":{"email":["has already been taken"]}}` or the same form for `username`. The user validation identifies the duplicate, and shared validation handling chooses the status and body.
Where: [app/models/user.rb](../../stacks/rails/6-polish/app/models/user.rb#L12) — `User` validations; [app/controllers/application_controller.rb](../../stacks/rails/6-polish/app/controllers/application_controller.rb#L43) — `render_validation`
Confidence: high

## 3
Answer: The feed contains published articles by users the authenticated reader follows. It is ordered by creation time descending, then article ID descending, and paginated.
Where: [app/controllers/api/articles_controller.rb](../../stacks/rails/6-polish/app/controllers/api/articles_controller.rb#L17) — `feed` and `list`; [app/models/article.rb](../../stacks/rails/6-polish/app/models/article.rb#L20) — `recent`
Confidence: high

## 4
Answer: `favoritesCount` is the size of the article’s `favorites` association.
Where: [app/views/api/articles/_article.json.jbuilder](../../stacks/rails/6-polish/app/views/api/articles/_article.json.jbuilder#L10) — article JSON partial
Confidence: high

## 5
Answer: Deleting someone else’s comment returns HTTP 403 Forbidden with `{"errors":{"comment":["forbidden"]}}`.
Where: [app/controllers/api/comments_controller.rb](../../stacks/rails/6-polish/app/controllers/api/comments_controller.rb#L16) — `destroy`; [app/controllers/application_controller.rb](../../stacks/rails/6-polish/app/controllers/application_controller.rb#L39) — `render_error`
Confidence: high

## 6
Answer: An empty string for `bio` is normalized to `nil`, so the stored bio is cleared.
Where: [app/models/user.rb](../../stacks/rails/6-polish/app/models/user.rb#L14) — `User` bio normalization; [app/controllers/api/users_controller.rb](../../stacks/rails/6-polish/app/controllers/api/users_controller.rb#L14) — `update`
Confidence: high

## 7
Answer: Tags are separate rows in `tags`, connected to articles through `article_tags`; tag names and article–tag pairs are unique. `GET /api/tags` returns names used by published articles, alphabetically ordered with duplicates removed.
Where: [db/migrate/20260927000000_create_conduit.rb](../../stacks/rails/6-polish/db/migrate/20260927000000_create_conduit.rb#L31) — `CreateConduit#change`; [app/controllers/api/tags_controller.rb](../../stacks/rails/6-polish/app/controllers/api/tags_controller.rb#L3) — `index`
Confidence: high

## 8
Answer: The default `limit` is 20, and the maximum accepted value is 1000.
Where: [app/controllers/api/articles_controller.rb](../../stacks/rails/6-polish/app/controllers/api/articles_controller.rb#L92) — `set_pagination`
Confidence: high

## 9
Answer: `User#token` creates an HS256 JWT signed with the Rails secret key. Its payload contains the user ID as `sub` and an `exp` timestamp 30 days after creation.
Where: [app/models/user.rb](../../stacks/rails/6-polish/app/models/user.rb#L20) — `token`
Confidence: high

## 10
Answer: The author check is enforced before article update and delete by `authorize_article`, which returns a forbidden error when the current user is not the author.
Where: [app/controllers/api/articles_controller.rb](../../stacks/rails/6-polish/app/controllers/api/articles_controller.rb#L80) — `authorize_article` and its `before_action`
Confidence: high

## 11
Answer: Omitting `tagList` leaves the article’s tags unchanged. Sending `"tagList": null` returns HTTP 422 with `{"errors":{"tagList":["must be a list of nonempty strings"]}}`.
Where: [app/controllers/api/articles_controller.rb](../../stacks/rails/6-polish/app/controllers/api/articles_controller.rb#L40) — `update` and `invalid_tags?`; [app/models/article.rb](../../stacks/rails/6-polish/app/models/article.rb#L28) — `revise!`
Confidence: high

## 12
Answer: Passwords are stored as bcrypt hashes in `users.password_digest`, using Rails’ `has_secure_password` with the `bcrypt` gem.
Where: [app/models/user.rb](../../stacks/rails/6-polish/app/models/user.rb#L2) — `User` `has_secure_password`; [Gemfile](../../stacks/rails/6-polish/Gemfile#L7) — `bcrypt` dependency; [db/migrate/20260927000000_create_conduit.rb](../../stacks/rails/6-polish/db/migrate/20260927000000_create_conduit.rb#L6) — `CreateConduit#change`
Confidence: high

Files read: 18.