# Clojure comprehension answer key: after step 1

Source: immutable `stacks/clojure/1-build`.
Source snapshot SHA-256: `957d2bdce441a15ea338c083db6c20093dc2ae0d1c02b510d1a4ee5aa176721b`.
Prompt: the original twelve questions in `steps/comprehension.md`.
This key was derived by reading the published application source, before any
reader answer was consulted. It describes the implementation, including its
differences from the prepared stack guidance. No application code was run.

## Scoring

Each question is worth 1 point: correct behavior with an accurate source file
and implementing function/method/module. Award 0.5 for correct behavior with
a wrong or missing implementation location, and 0 for incorrect behavior.
Maximum: 12. Equivalent wording and accurate alternative implementation
locations are acceptable. Line numbers are supplied for the grader but are
not required from the reader. The optional corner-case notes below resolve
ambiguities; a concise answer need not recite every note to earn full credit.
Confidence and the reader's file count do not affect this behavior/location
rubric. Do not award points for intended framework behavior that contradicts
the code.

## 1

Answer: The private `slug` function lowercases the title, replaces each run
of characters outside ASCII `a-z` and `0-9` with `-`, then appends `-` and the
first eight characters of a new random UUID. Article creation calls it, and
an update containing `title` generates a new slug; an update without `title`
preserves the old slug.

Where: `src/conduit/articles.clj` — `slug` (lines 19–21), `create!` (55–62),
and `update!` (64–82, especially 72–73).

Corner cases: The implementation does not trim leading or trailing hyphens.
Supplying the same title still invokes the random slug generator; it does
not check whether the title changed. Blank or non-string supplied titles
fail the preceding required-field validation. Do not describe the slug as a
fixed title-only string, a sequential suffix, or unchanged on title updates.

## 2

Answer: Registration with an otherwise valid input and a pre-existing
username returns HTTP 409 with
`{"errors":{"username":["has already been taken"]}}`; a pre-existing email
returns HTTP 409 with
`{"errors":{"email":["has already been taken"]}}`. `available!` raises the
field-specific domain error, and `wrap-api` turns its exception data into the
JSON error response.

Where: `src/conduit/users.clj` — `register!` and `available!` (34–45);
`src/conduit/domain.clj` — `fail` (4–5);
`src/conduit/http.clj` — `wrap-api` (27–41).

Corner cases: Registration validates required fields and password length
before availability checks. Username is checked before email, so if both are
taken, the username error is returned first. The database also declares
separate UNIQUE constraints in `resources/migrations/001-conduit.up.sql`
(users, lines 1–8), but the shown HTTP response comes from the explicit
availability check. There is no source-level handler translating a concurrent
unique-constraint race to this domain response. Do not claim HTTP 422, an
array of both duplicate errors, or that SQL exceptions are centrally mapped
to this response.

## 3

Answer: The authenticated feed contains articles whose authors the current
user follows. It orders them newest first by `a.created_at DESC`, with
`a.id DESC` breaking timestamp ties, and applies the requested pagination.

Where: `src/conduit/articles.clj` — `listing` (102–115, particularly 105 and
112–113); `src/conduit/http.clj` — `handler`'s `/api/articles/feed` route
(line 60), wrapped by `authorized` (22–25).

Corner cases: The same listing function also accepts `author`, `tag`, and
`favorited` query filters; supplied filters are ANDed with the follows
condition, including on the feed. The user's own articles are not specially
included: they satisfy the condition only if a corresponding self-follow
exists. This step has no draft or publication-state filter. `articlesCount`
counts the complete filtered result before LIMIT/OFFSET, and feed list
projections omit the article body. A concise answer naming followed authors
and newest-first order is sufficient; contrary assertions about special
self-inclusion or a publication filter are incorrect.

## 4

Answer: For each presented article, the code queries
`SELECT count(*) AS count FROM favorites WHERE article_id = ?` and uses that
row's `:count` as `favoritesCount`. It counts all favorite relationships for
the article, independently of the viewing user.

Where: `src/conduit/articles.clj` — `present` (32–42, specifically 39–40).
The uniqueness guarantee is in `resources/migrations/001-conduit.up.sql` —
`favorites` table, primary key `(user_id, article_id)` (34–38).

Corner cases: This is a database count at projection time, not a stored
counter column, an author count, or the viewer's boolean `favorited` field.
The composite primary key prevents multiple favorite rows for the same
user/article pair.

## 5

Answer: An authenticated user deleting an existing comment on the addressed
article that belongs to someone else receives HTTP 403 with
`{"errors":{"comment":["forbidden"]}}`. The ownership check fails before
the DELETE statement runs.

Where: `src/conduit/articles.clj` — `delete-comment!` (137–142);
`src/conduit/domain.clj` — `owned` and `fail` (17–19 and 4–5);
`src/conduit/http.clj` — `wrap-api` (27–41), with the protected delete route
in `handler` (71–72).

Corner cases: The code first finds the article, then finds a comment matching
both its ID and that article ID; a missing/wrong-article comment gives the
not-found path instead. The article author has no special right to delete
another user's comment. An unauthenticated request hits the authorization
error first; successful authorized deletion returns 204, not this failure.

## 6

Answer: An explicitly empty string for `bio` is converted to Clojure `nil`
and written as SQL NULL. The returned user projection contains `bio: null`.

Where: `src/conduit/users.clj` — `update!` (54–71, especially the reduction
at 65–67) and `public` (26–28).

Corner cases: This is an exact `""` comparison, not a whitespace trim:
whitespace-only bio strings remain strings. An omitted bio is absent from
the update map and preserves its stored value. Explicit null also updates
it to NULL. The same empty-string normalization applies to `image`.

## 7

Answer: Tags are rows in `article_tags` containing `article_id`, text `tag`,
and integer `position`; the `(article_id, tag)` composite primary key makes
each tag unique per article. Replacing an article's tags deletes its old
rows and inserts the distinct supplied tags in first-occurrence order with
their positions. `GET /api/tags` returns `{"tags":[...]}` from
`SELECT DISTINCT tag FROM article_tags ORDER BY tag`: globally deduplicated
tags in ascending database text sort order.

Where: `resources/migrations/001-conduit.up.sql` — `article_tags` table
(27–32); `src/conduit/articles.clj` — `replace-tags!` (44–48), `tags` (26–27),
and `all-tags` (117–118); `src/conduit/http.clj` — `/api/tags` route in
`handler` (73).

Corner cases: Article `tagList` order uses stored `position`, while the
global tags endpoint sorts tag text. There is no separate global tags table
or JSON/array column. Tags are not lowercased or trimmed here; equal tag
strings are deduplicated, but differently spelled strings are not
application-normalized. Global ordering follows the database's collation.

## 8

Answer: Article lists, including the feed, default `limit` to 20. There is
no separately configured application maximum or upper clamp: the value is
parsed with `Integer/parseInt`, then lower-bounded at zero.

Where: `src/conduit/articles.clj` — `page-size` (98–100) and `listing`
(102–115, especially line 113).

Corner cases: Missing, malformed, and out-of-32-bit-range values fall back
to 20 because parsing exceptions are caught. A parsed negative limit becomes
0, and an explicit 0 remains 0. Thus the largest accepted integer value is
2,147,483,647 as a parsing consequence; larger numeric strings fall back to
20 rather than being clamped to that value. Accept either “no application
maximum” with the parse caveat or a precise description of this effective
32-bit parsing bound. An asserted fixed cap such as 100 is incorrect.

## 9

Answer: `token` calls Buddy's `jwt/sign` with the application secret and a
claim map containing the user's numeric `id` and `exp`, set to the current
Unix time in seconds plus 30 days (2,592,000 seconds). The application secret
comes from `SECRET_KEY_BASE`; `public` creates a token whenever it builds the
user response. Token reading uses `jwt/unsign` with the same secret.

Where: `src/conduit/users.clj` — `token` (12–14), `public` (26–28), and
`current` (16–21); `src/conduit/config.clj` — `environment` (7–10);
`src/conduit/system.clj` — `configuration` (11–17) and `ig/init-key ::handler`
(28–29). `deps.edn` identifies `buddy/buddy-sign`.

Corner cases: The source specifies `:id`, not `:sub`, username, email, or
roles; no `iat` claim is explicitly added by the application. Both sign and
unsign omit an algorithm option and therefore delegate algorithm selection
to the library default. The application source alone does not spell out that
default, so do not require the reader to name it for full credit. The expiry
is 30 days from each token issuance, not permanent or a server-side session
timeout. `current` recognizes the `Token ` authorization prefix and converts
verification exceptions into a missing current user.

## 10

Answer: Article `update!` and `delete!` load the article and call
`domain/owned` with its `author_id`, the current user's `id`, and `:article`
before modifying or deleting it. `owned` rejects unequal IDs with HTTP 403
domain error `{"errors":{"article":["forbidden"]}}`.

Where: `src/conduit/articles.clj` — `update!` (64–82, line 67) and `delete!`
(84–87, line 86); `src/conduit/domain.clj` — `owned` (17–19).
`src/conduit/http.clj` — `handler`'s protected PUT/DELETE article routes
(63–64) and `wrap-api` (27–41) handle authentication and serialization.

Corner cases: Authentication alone in `authorized` is not the author rule.
The rule is in the domain calls; it is not a database row policy, route
schema, or a check against a user-supplied author ID.

## 11

Answer: Omitting `tagList` preserves the existing tag rows because both
validation and replacement are guarded by `(contains? input :tagList)`.
Explicit `"tagList": null` is present but becomes `nil`, which fails
`valid-tags`' requirement for a sequential collection of strings and returns
HTTP 422 with `{"errors":{"tagList":["is invalid"]}}`; the update is
rejected rather than clearing tags.

Where: `src/conduit/articles.clj` — `update!` (64–82, especially 68–69 and
80–81), `valid-tags` (50–53), and `replace-tags!` (44–48);
`src/conduit/domain.clj` — `fail` (4–5);
`src/conduit/http.clj` — `wrap-api` (27–41).

Corner cases: An empty array is a valid sequential collection and clears
all tags. The null validation occurs before the article UPDATE and tag
replacement inside the transaction, so accompanying valid article-field
changes do not proceed on the null-input failure. Null is not treated as
omission and does not produce an empty list.

## 12

Answer: Passwords are stored as the encoded hash returned by
`buddy.hashers/derive` in the users table's `password_hash` text column, not
as plaintext. Both registration and password updates use that library;
login verifies a supplied password with `buddy.hashers/check`.

Where: `src/conduit/users.clj` — `register!` (39–45), `update!` (54–71,
line 64), and `login!` (47–52); `resources/migrations/001-conduit.up.sql` —
users `password_hash TEXT NOT NULL` (line 5); `deps.edn` —
`buddy/buddy-hashers` version 2.0.167.

Corner cases: The application passes no algorithm or work-factor options,
so the choice is Buddy's default. Do not require a particular default
algorithm name that is absent from the application source. In particular,
the implementation does not explicitly request Argon2id despite that choice
being discussed in the stack preparation guidance. A claim that the source
explicitly selects Argon2id is incorrect.
