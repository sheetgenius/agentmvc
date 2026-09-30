## 1
Answer: The slug is the lowercased title with each run of non-alphanumeric characters replaced by `-`, followed by `-` and the first eight characters of a random UUID. Supplying `title` in an update generates a new slug, even if the title text is unchanged.
Where: `src/conduit/articles.clj` — `slug`, `create!`, `update!`
Confidence: high

## 2
Answer: A taken email or username produces HTTP 409 with `{"errors":{"email":["has already been taken"]}}` or the same body with `username` as the key. `available!` chooses the error; `wrap-api` turns it into the HTTP response.
Where: `src/conduit/users.clj` — `available!`, `register!`; `src/conduit/domain.clj` — `fail`; `src/conduit/http.clj` — `wrap-api`
Confidence: high

## 3
Answer: The feed contains articles by users the authenticated viewer follows, subject to any supplied author, tag, or favorited filters. It orders them by `created_at` descending, then article ID descending, before applying pagination.
Where: `src/conduit/http.clj` — `handler`; `src/conduit/articles.clj` — `listing`
Confidence: high

## 4
Answer: `favoritesCount` is the count of rows in `favorites` for that article’s ID.
Where: `src/conduit/articles.clj` — `present`
Confidence: high

## 5
Answer: Deleting someone else’s comment produces HTTP 403 with `{"errors":{"comment":["forbidden"]}}`.
Where: `src/conduit/articles.clj` — `delete-comment!`; `src/conduit/domain.clj` — `owned`, `fail`; `src/conduit/http.clj` — `wrap-api`
Confidence: high

## 6
Answer: An update with `"bio": ""` stores `NULL`, so the returned user’s `bio` is `null`.
Where: `src/conduit/users.clj` — `update!`, `public`
Confidence: high

## 7
Answer: Tags are rows in `article_tags`, with an article ID, tag text, and position; each article can have a given tag only once. `GET /api/tags` returns distinct tags across all articles in ascending database sort order.
Where: `resources/migrations/001-conduit.up.sql` — `article_tags` table; `src/conduit/articles.clj` — `replace-tags!`, `all-tags`; `src/conduit/http.clj` — `handler`
Confidence: high

## 8
Answer: The default `limit` is 20. There is no configured maximum, though `Integer/parseInt` restricts accepted values to signed 32-bit integers.
Where: `src/conduit/articles.clj` — `page-size`, `listing`
Confidence: high

## 9
Answer: `buddy.sign.jwt/sign` signs a token with the configured secret. Its payload contains the user ID and an `exp` timestamp set to 30 days after creation.
Where: `src/conduit/users.clj` — `token`
Confidence: high

## 10
Answer: Both article update and deletion call `domain/owned`, which rejects a viewer whose ID differs from the article’s author ID.
Where: `src/conduit/articles.clj` — `update!`, `delete!`; `src/conduit/domain.clj` — `owned`
Confidence: high

## 11
Answer: Omitting `tagList` leaves the article’s tags unchanged. Sending `"tagList": null` fails validation with HTTP 422 and `{"errors":{"tagList":["is invalid"]}}`.
Where: `src/conduit/articles.clj` — `update!`, `valid-tags`; `src/conduit/http.clj` — `wrap-api`
Confidence: high

## 12
Answer: Passwords are stored as derived hashes in the `users.password_hash` column using `buddy.hashers/derive`; login checks them with `buddy.hashers/check`.
Where: `src/conduit/users.clj` — `register!`, `update!`, `login!`; `resources/migrations/001-conduit.up.sql` — `users` table
Confidence: high

Files read: 6