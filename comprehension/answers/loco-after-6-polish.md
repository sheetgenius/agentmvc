## 1
Answer: The slug is the slugified title followed by a hyphen and a new UUID without separators. Supplying a title in an update generates a new slug, even if the title text is unchanged; omitting the title leaves the slug alone.
Where: `conduit/src/models/articles.rs` — `Model::slug_for`, `Model::create`; `conduit/src/controllers/articles.rs` — `update`
Confidence: high

## 2
Answer: An existing username or email produces HTTP 409 with `{"errors":{"username":["has already been taken"]}}` or `{"errors":{"email":["has already been taken"]}}`. The username check runs first.
Where: `conduit/src/controllers/users.rs` — `register`; `conduit/src/controllers/api.rs` — `ApiError::taken`, `IntoResponse for ApiError`
Confidence: high

## 3
Answer: The feed requires authentication and lists published articles by users the viewer follows, ordered by descending article ID. Supplied `author`, `favorited`, and `tag` filters also apply.
Where: `conduit/src/controllers/articles.rs` — `feed`, `list_response`; `conduit/src/models/articles.rs` — `Model::list`
Confidence: high

## 4
Answer: `favoritesCount` is the number of rows in `favorites` for that article. List responses calculate counts in a grouped query and use zero when an article has no matching rows.
Where: `conduit/src/views/realworld.rs` — `ArticleView::load`, `ArticleView::load_many`; `conduit/src/models/favorites.rs` — `Model::count`
Confidence: high

## 5
Answer: Deleting another user's comment returns HTTP 403 with `{"errors":{"comment":["forbidden"]}}`.
Where: `conduit/src/controllers/comments.rs` — `remove`; `conduit/src/controllers/api.rs` — `ApiError::forbidden`, `IntoResponse for ApiError`
Confidence: high

## 6
Answer: An empty string for `bio` is converted to `None` and saved as a null value.
Where: `conduit/src/controllers/users.rs` — `update`
Confidence: high

## 7
Answer: Each article stores its tags as a JSON array in the `tag_list` column. `GET /api/tags` collects tags from published articles into a `BTreeSet`, so its `tags` array is sorted and contains no duplicates.
Where: `conduit/migration/src/m20260927_000001_conduit.rs` — `Migration::up`; `conduit/src/models/articles.rs` — `Model::create`, `Model::all_tags`; `conduit/src/controllers/articles.rs` — `tags`
Confidence: high

## 8
Answer: The default `limit` is 20. The code applies no maximum to a supplied `limit`.
Where: `conduit/src/controllers/articles.rs` — `ListQuery::page`; `conduit/src/models/articles.rs` — `Model::page`
Confidence: high

## 9
Answer: The backend creates a JWT using Loco's JWT helper and the configured secret, passing the user's UUID `pid` and an empty extra-claims map. Both configuration files set its expiration to `604800` seconds, or seven days.
Where: `conduit/src/models/users.rs` — `Model::token`; `conduit/src/controllers/users.rs` — `response`; `conduit/config/development.yaml`, `conduit/config/production.yaml` — `auth.jwt`
Confidence: medium

## 10
Answer: `owned` rejects an article whose `author_id` differs from the viewer's ID. The update path calls it through `find_owned_for_update`, and the delete path calls it directly.
Where: `conduit/src/controllers/articles.rs` — `owned`, `find_owned_for_update`, `update`, `remove`
Confidence: high

## 11
Answer: Omitting `tagList` leaves the stored tags unchanged. Sending `"tagList": null` fails deserialization as `Vec<String>` and returns HTTP 422 with `{"errors":{"tagList":["is invalid"]}}`.
Where: `conduit/src/controllers/articles.rs` — `update`; `conduit/src/controllers/api.rs` — `ApiError::invalid`, `IntoResponse for ApiError`
Confidence: high

## 12
Answer: Passwords are stored as hashes returned by `loco_rs::hash::hash_password`, both at registration and when changed; verification uses `loco_rs::hash::verify_password`. This directory does not specify the hash algorithm used inside Loco.
Where: `conduit/src/models/users.rs` — `Model::register`, `ActiveModel::change_password`, `Model::verify_password`
Confidence: high

Files read: 13