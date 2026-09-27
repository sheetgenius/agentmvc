# Setup: register the author
POST {{host}}/api/users
{
  "user": {
    "username": "drafterr_a_{{uid}}",
    "email": "drafterr_a_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 201
[Captures]
token_a: jsonpath "$.user.token"

# Setup: register another user
POST {{host}}/api/users
{
  "user": {
    "username": "drafterr_b_{{uid}}",
    "email": "drafterr_b_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 201
[Captures]
token_b: jsonpath "$.user.token"

# The author creates a draft
POST {{host}}/api/articles
Authorization: Token {{token_a}}
{
  "article": {
    "title": "Hidden Draft {{uid}}",
    "description": "hidden",
    "body": "hidden",
    "status": "draft"
  }
}
HTTP 201
[Captures]
draft_slug: jsonpath "$.article.slug"

# An anonymous reader can't see the draft
GET {{host}}/api/articles/{{draft_slug}}
HTTP 404
[Asserts]
jsonpath "$.errors.article[0]" == "not found"

# Another user can't see the draft
GET {{host}}/api/articles/{{draft_slug}}
Authorization: Token {{token_b}}
HTTP 404
[Asserts]
jsonpath "$.errors.article[0]" == "not found"

# Another user can't update the draft
PUT {{host}}/api/articles/{{draft_slug}}
Authorization: Token {{token_b}}
{
  "article": {
    "body": "hijacked"
  }
}
HTTP 404
[Asserts]
jsonpath "$.errors.article[0]" == "not found"

# Another user can't delete the draft
DELETE {{host}}/api/articles/{{draft_slug}}
Authorization: Token {{token_b}}
HTTP 404
[Asserts]
jsonpath "$.errors.article[0]" == "not found"

# Another user can't publish the draft
POST {{host}}/api/articles/{{draft_slug}}/publish
Authorization: Token {{token_b}}
HTTP 404
[Asserts]
jsonpath "$.errors.article[0]" == "not found"

# Another user can't comment on the draft
POST {{host}}/api/articles/{{draft_slug}}/comments
Authorization: Token {{token_b}}
{
  "comment": {
    "body": "Nice draft"
  }
}
HTTP 404
[Asserts]
jsonpath "$.errors.article[0]" == "not found"

# Another user can't favorite the draft
POST {{host}}/api/articles/{{draft_slug}}/favorite
Authorization: Token {{token_b}}
HTTP 404
[Asserts]
jsonpath "$.errors.article[0]" == "not found"

# An anonymous reader can't list the draft's comments
GET {{host}}/api/articles/{{draft_slug}}/comments
HTTP 404
[Asserts]
jsonpath "$.errors.article[0]" == "not found"

# The author can't comment on their own draft
POST {{host}}/api/articles/{{draft_slug}}/comments
Authorization: Token {{token_a}}
{
  "comment": {
    "body": "Note to self"
  }
}
HTTP 422
[Asserts]
jsonpath "$.errors.article[0]" == "is a draft"

# The author can't favorite their own draft
POST {{host}}/api/articles/{{draft_slug}}/favorite
Authorization: Token {{token_a}}
HTTP 422
[Asserts]
jsonpath "$.errors.article[0]" == "is a draft"

# Publishing needs a token
POST {{host}}/api/articles/{{draft_slug}}/publish
HTTP 401
[Asserts]
jsonpath "$.errors.token[0]" == "is missing"

# Publishing an unknown article
POST {{host}}/api/articles/unknown-slug-{{uid}}/publish
Authorization: Token {{token_a}}
HTTP 404
[Asserts]
jsonpath "$.errors.article[0]" == "not found"

# Listing drafts needs a token
GET {{host}}/api/user/drafts
HTTP 401
[Asserts]
jsonpath "$.errors.token[0]" == "is missing"

# An invalid status is rejected
POST {{host}}/api/articles
Authorization: Token {{token_a}}
{
  "article": {
    "title": "Bad Status {{uid}}",
    "description": "bad",
    "body": "bad",
    "status": "archived"
  }
}
HTTP 422
[Asserts]
jsonpath "$.errors.status[0]" == "is invalid"

# The author creates a published article
POST {{host}}/api/articles
Authorization: Token {{token_a}}
{
  "article": {
    "title": "Conflict Article {{uid}}",
    "description": "conflict",
    "body": "Original body"
  }
}
HTTP 201
[Captures]
slug: jsonpath "$.article.slug"

# Another user can't publish someone else's article
POST {{host}}/api/articles/{{slug}}/publish
Authorization: Token {{token_b}}
HTTP 403
[Asserts]
jsonpath "$.errors.article[0]" == "forbidden"

# Ownership is checked before the revision
PUT {{host}}/api/articles/{{slug}}
Authorization: Token {{token_b}}
{
  "article": {
    "body": "hijacked",
    "revision": 99
  }
}
HTTP 403
[Asserts]
jsonpath "$.errors.article[0]" == "forbidden"

# The author updates with the current revision
PUT {{host}}/api/articles/{{slug}}
Authorization: Token {{token_a}}
{
  "article": {
    "body": "Second body",
    "revision": 1
  }
}
HTTP 200
[Asserts]
jsonpath "$.article.revision" == 2
[Captures]
slug: jsonpath "$.article.slug"

# A stale revision is refused and returns the current article
PUT {{host}}/api/articles/{{slug}}
Authorization: Token {{token_a}}
{
  "article": {
    "body": "Stale body",
    "revision": 1
  }
}
HTTP 409
[Asserts]
jsonpath "$.errors.revision[0]" == "is stale"
jsonpath "$.article.revision" == 2
jsonpath "$.article.body" == "Second body"

# The refused update changed nothing
GET {{host}}/api/articles/{{slug}}
HTTP 200
[Asserts]
jsonpath "$.article.body" == "Second body"
jsonpath "$.article.revision" == 2

# A revision that isn't an integer is invalid
PUT {{host}}/api/articles/{{slug}}
Authorization: Token {{token_a}}
{
  "article": {
    "body": "Other body",
    "revision": "abc"
  }
}
HTTP 422
[Asserts]
jsonpath "$.errors.revision[0]" == "is invalid"
