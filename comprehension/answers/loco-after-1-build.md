## 1
Answer: The slug is the title passed through `slug::slugify`, followed by a hyphen and a new UUID. Sending `title` in an update regenerates the slug, even if the title text is unchanged.
Where: `conduit/src/models/articles.rs` — `Model::slug_for`; `conduit/src/controllers/articles.rs` — `update`
Confidence: high

## 2
Answer: Registration returns HTTP 409 with `{"errors":{"username":["has already been taken"]}}` or the same body with `email` as the key. Username is checked first.
Where: `conduit/src/controllers/users.rs` — `register`; `conduit/src/controllers/api.rs` — `ApiError::taken` and `IntoResponse::into_response`
Confidence: high

## 3
Answer: The feed contains articles by users the authenticated viewer follows, subject to any supplied author, favorited, tag, limit, and offset filters. Articles are ordered by descending article ID; a viewer who follows nobody gets an empty list.
Where: `conduit/src/controllers/articles.rs` — `feed` and `list_response`; `conduit/src/models/articles.rs` — `Model::list`
Confidence: high

## 4
Answer: `favoritesCount` is a database count of favorite records for that article.
Where: `conduit/src/views/realworld.rs` — `ArticleView::load`; `conduit/src/models/favorites.rs` — `Model::count`
Confidence: high

## 5
Answer: If the comment belongs to the article but another user wrote it, deletion returns HTTP 403 with `{"errors":{"comment":["forbidden"]}}`.
Where: `conduit/src/controllers/comments.rs` — `remove`; `conduit/src/controllers/api.rs` — `ApiError::forbidden` and `IntoResponse::into_response`
Confidence: high

## 6
Answer: An empty string for `bio` is converted to `None`, stored as SQL `NULL`, and returned as JSON `null`.
Where: `conduit/src/controllers/users.rs` — `update`; `conduit/src/views/realworld.rs` — `UserView::new`
Confidence: high

## 7
Answer: Each article stores its tags as a JSON array in the `tag_list` column. `GET /api/tags` combines tags from all articles into a `BTreeSet`, so its `tags` array is sorted and contains no duplicates.
Where: `conduit/migration/src/m20260927_000001_conduit.rs` — `Migration::up`; `conduit/src/models/articles.rs` — `Model::create` and `Model::all_tags`; `conduit/src/controllers/articles.rs` — `tags`
Confidence: high

## 8
Answer: Article lists default to `limit=20`. The code sets no maximum.
Where: `conduit/src/controllers/articles.rs` — `ListQuery` and `list_response`; `conduit/src/models/articles.rs` — `Model::list`
Confidence: high

## 9
Answer: Loco’s JWT helper creates the token using the configured secret, the user’s UUID `pid`, an empty map of extra claims, and the configured expiration. Both local configurations set expiration to `604800` seconds, or seven days.
Where: `conduit/src/models/users.rs` — `Model::token`; `conduit/src/controllers/users.rs` — `response`; `conduit/config/development.yaml` and `conduit/config/production.yaml` — `auth.jwt` configuration
Confidence: high

## 10
Answer: Both update and delete compare the article’s `author_id` with the authenticated viewer’s ID and reject a mismatch.
Where: `conduit/src/controllers/articles.rs` — `update` and `remove`
Confidence: high

## 11
Answer: Omitting `tagList` leaves the stored tags unchanged. Sending `"tagList": null` fails deserialization as a string vector and returns HTTP 422 with `{"errors":{"tagList":["is invalid"]}}`.
Where: `conduit/src/controllers/articles.rs` — `update`; `conduit/src/controllers/api.rs` — `ApiError::invalid` and `IntoResponse::into_response`
Confidence: high

## 12
Answer: Passwords are stored as hash strings in the users table. Registration and password changes call `loco_rs::hash::hash_password`; the hash algorithm is not specified in this directory.
Where: `conduit/src/models/users.rs` — `Model::register` and `ActiveModel::change_password`; `conduit/migration/src/m20260927_000001_conduit.rs` — `Migration::up`
Confidence: high

Files read: 12.