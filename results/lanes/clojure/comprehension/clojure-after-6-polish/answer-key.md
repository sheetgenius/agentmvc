# Clojure comprehension answer key: after step 6

Source: immutable `stacks/clojure/6-polish`.
Source snapshot SHA-256: `22901b923a92173148878646ee7b02eebf4f74d227419225a7c636bed4237946`.
Prompt: the original twelve questions in `steps/comprehension.md`.
Derived afresh from the published step 6 implementation before consulting
any second-reader answer. No application code was executed. Earlier answers
and stack guidance are not the authority for these implementation facts.

## Scoring

Award 1 point for correct behavior plus an accurate file and implementing
function/method/module, 0.5 for correct behavior with a wrong or missing
location, and 0 for incorrect behavior. Maximum 12. Equivalent wording and
accurate alternative implementation locations are acceptable; line numbers
are supplied for verification but are not required from the reader. Optional
corner-case notes resolve ambiguities and are not a requirement to recite
every detail. Confidence labels and self-reported file counts are not scored.
Do not accept a statement contradicting an essential rule, such as including
drafts in the public feed or treating explicit null tags as omitted tags.

## 1

Answer: `slug` lowercases the title, replaces runs of characters outside ASCII
`a-z` and `0-9` with `-`, then appends `-` and the first eight characters of a
new random UUID. Creation invokes it, and a successful update that includes
`title` generates a new slug; omission of `title` preserves it.

Where: `src/conduit/articles.clj` — `slug` (19–21), `create!` (77–88),
`update!` (94–121, particularly 107–108).

Corner cases: There is no trimming of boundary hyphens. Supplying the same
title still generates a new random suffix. Required-field validation rejects
blank/non-string supplied titles; revision or authorization failures can
reject the update before it changes anything.

## 2

Answer: A pre-existing duplicate username produces HTTP 409 with
`{"errors":{"username":["has already been taken"]}}`; a duplicate email
produces HTTP 409 with
`{"errors":{"email":["has already been taken"]}}`. `available!` raises
the domain error and `wrap-api` serializes its status and errors as JSON.

Where: `src/conduit/users.clj` — `available!` (44–47), `register!` (49–55);
`src/conduit/domain.clj` — `fail` (4–5);
`src/conduit/http.clj` — `wrap-api` (31–49).

Corner cases: Required fields and password length are checked first. Username
is checked before email, so both being taken produces the username error.
The database also declares separate UNIQUE constraints in
`resources/migrations/001-conduit.up.sql` — `users` (1–8). The explicit
application lookup decides the described response; a concurrent SQL unique
constraint violation is not mapped to this response by a shown SQL exception
handler. Do not substitute HTTP 422 or an array aggregating both errors.

## 3

Answer: The feed requires authentication and includes only published
articles authored by users the viewer follows. Supplied author, tag, or
favorited filters further restrict that set, and results are ordered by
`a.created_at DESC, a.id DESC` before pagination.

Where: `src/conduit/articles.clj` — `listing` (167–174) supplies the
published/follows conditions and `article-page` (158–165) orders/paginates;
`src/conduit/http.clj` — `handler`'s `/api/articles/feed` route (69), using
`authorized` (22–25).

Corner cases: Ordering is by creation time, not `published_at` or update time.
Drafts are excluded even if authored by the viewer. Own articles are not
automatically included; they would need a matching follows row. Counts are
computed before pagination. Omitting the published-only condition makes the
membership answer materially incomplete for this snapshot.

## 4

Answer: `present-many` computes a correlated SQL `count(*)` of favorites
whose `article_id` equals each article's ID, calling the result
`favorites_count`; `article-response` maps that value to `favoritesCount`.
The batch details query covers the requested page, and the count includes
all users' favorite relationships, independently of the viewer.

Where: `src/conduit/articles.clj` — `present-many` (41–61, especially 46–52)
and `article-response` (30–39, line 37); `present` (63–64) uses the same
path for a single article.

Corner cases: This is not a stored counter or an application count of a
loaded collection. A separate EXISTS expression computes the viewer's
`favorited` flag. The favorites table's composite key `(user_id, article_id)`
prevents duplicate favorites by the same user:
`resources/migrations/001-conduit.up.sql` — `favorites` (34–38).

## 5

Answer: For an authenticated user addressing an existing comment on a
visible article, deleting a comment written by another user returns HTTP
403 with `{"errors":{"comment":["forbidden"]}}`. The ownership check
runs before the DELETE statement.

Where: `src/conduit/articles.clj` — `delete-comment!` (200–205);
`src/conduit/domain.clj` — `owned` (17–19) and `fail` (4–5);
`src/conduit/http.clj` — `wrap-api` (31–49) and the protected comment-delete
route in `handler` (82–83).

Corner cases: The comment lookup requires both the comment ID and addressed
article ID. Missing comments, wrong-article comments, and another user's
hidden draft take a 404 path first. Being the article's author does not grant
permission to delete another user's comment. Lack of authentication gives
401; successful deletion gives 204. These are distinct from the requested
non-owner failure.

## 6

Answer: An explicitly empty `bio` string is converted to Clojure `nil`,
stored as SQL NULL, and returned as JSON null in the user projection.

Where: `src/conduit/users.clj` — `update!` (70–87, particularly 79–83)
and `public` (36–38). The shared profile projection also carries the
nullable field through `profile-data` (92–94).

Corner cases: This is an exact empty-string test, not trimming whitespace.
Omission leaves the stored bio unchanged, explicit null sets it to NULL,
and whitespace-only strings stay strings. The same conversion applies to
`image`.

## 7

Answer: Tags are stored in `article_tags` rows containing `article_id`,
text `tag`, and integer `position`, with `(article_id, tag)` as the primary
key. Replacement deletes the article's old tags and inserts distinct input
tags in first-occurrence order. `GET /api/tags` returns a `tags` array of
distinct tag strings belonging to published articles, in ascending database
text sort order.

Where: `resources/migrations/001-conduit.up.sql` — `article_tags` (27–32);
`src/conduit/articles.clj` — `replace-tags!` (66–70), `present-many`'s tag
query (53–60), `all-tags` (180–181);
`src/conduit/http.clj` — `handler`'s `/api/tags` route (84).

Corner cases: A tag used only by drafts is absent from the global endpoint;
a tag shared with a published article remains present. Per-article tag order
uses stored positions; the global list orders text under the database's
collation. There is no separate global tags table or tags JSON column, and
the code does not normalize tag spelling/case. The published-only restriction
is an essential part of the endpoint's current behavior.

## 8

Answer: Article list limits default to 20. There is no configured upper cap;
`page-size` uses `parse-long`, falls back to the default if parsing yields
nil, and clamps only the lower bound with `max 0`.

Where: `src/conduit/articles.clj` — `page-size` (155–156) and `article-page`
(158–165, line 163). `listing` and `drafts` both use `article-page`.

Corner cases: Query-string integers are parsed as signed 64-bit longs;
missing, malformed, and out-of-long-range strings default to 20. Valid
negative values become 0 and zero remains 0. The largest representable
positive parse result is 9,223,372,036,854,775,807, not a separately imposed
pagination cap. Accept “no maximum” meaning no application upper clamp, or
a precise distinction between that and the parser's representational bound.
Do not claim the previous 32-bit parser, a cap of 100, or upper clamping.

## 9

Answer: `token` calls Buddy `jwt/sign` with the application secret and
claims `id` (the user's ID) and `exp` (current Unix seconds plus 30 days,
2,592,000 seconds). The secret comes from `SECRET_KEY_BASE`, and `public`
issues a token whenever it constructs the user response. `current` verifies
incoming token text using `jwt/unsign` and the same secret.

Where: `src/conduit/users.clj` — `token` (22–24), `public` (36–38),
`current` (26–31); `src/conduit/config.clj` — `environment`;
`src/conduit/system.clj` — `configuration` and `ig/init-key ::handler`.
`deps.edn` declares `buddy/buddy-sign` version 3.6.1-359.

Corner cases: The application explicitly sets `id` and `exp`, not `sub`,
username, email, roles, or `iat`. Algorithm options are omitted; naming a
library-default algorithm absent from application source is not required.
The request header must start with `Token `. Verification exceptions are
caught only around `jwt/unsign`/claim extraction; the subsequent `user-by-id`
database lookup is outside that catch. Do not claim database failures are
silently converted to unauthenticated users by `current`.

## 10

Answer: `update!` and `delete!` first find an article visible to the viewer,
then call `domain/owned` with its `author_id`, the viewer's `id`, and
`:article`. The shared rule compares the IDs and rejects a mismatch with a
403 article-forbidden domain error before mutation.

Where: `src/conduit/articles.clj` — `update!` (94–121, line 97), `delete!`
(135–138, line 137), and `find-article` (23–25);
`src/conduit/domain.clj` — `owned` (17–19).

Corner cases: The HTTP `authorized` wrapper only requires a logged-in user;
it does not enforce article authorship. Another author's published article
reaches the ownership 403, whereas another author's draft is hidden by the
lookup and returns 404 first. An author may update/delete their own draft.

## 11

Answer: Omitting `tagList` preserves the existing tag rows. Explicit
`"tagList": null` is present according to `contains?` but becomes nil,
fails `valid-tags`' vector-of-strings check, and returns HTTP 422 with
`{"errors":{"tagList":["is invalid"]}}` instead of modifying the article.

Where: `src/conduit/articles.clj` — `update!` (103–104 and 119–120),
`valid-tags` (72–75), `replace-tags!` (66–70);
`src/conduit/domain.clj` — `fail`;
`src/conduit/http.clj` — `wrap-api` (31–49).

Corner cases: An empty JSON array is valid and clears tags. Authorization
and supplied-revision validation precede tag validation, so those failures
can take precedence. Unlike tag omission, a valid update still increments
revision/updated_at even when no title, description, body or tag changes are
supplied; this does not mean omitted tags are cleared. Explicit null rejects
before the SQL UPDATE and does not apply accompanying field changes.

## 12

Answer: Registration and password changes store Buddy's encoded
`hashers/derive` result in the users table's `password_hash TEXT NOT NULL`
column. Login verifies a supplied password with `hashers/check`; plaintext
is not the stored representation.

Where: `src/conduit/users.clj` — `register!` (49–55), `update!` (70–87,
line 80), `login!` (57–68, line 65);
`resources/migrations/001-conduit.up.sql` — `users.password_hash` (line 5);
`deps.edn` — `buddy/buddy-hashers` version 2.0.167.

Corner cases: Neither derive call selects an explicit algorithm or work
factor, so the source delegates those choices to Buddy. Do not require the
reader to name defaults absent from the application code, and do not accept
a claim that this implementation explicitly requests Argon2id. Login also
has a failure-attempt limiter, but that is separate from password storage.
