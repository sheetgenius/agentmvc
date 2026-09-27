# Setup: register the author
POST {{host}}/api/users
{
  "user": {
    "username": "drafts_a_{{uid}}",
    "email": "drafts_a_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 201
[Captures]
token_a: jsonpath "$.user.token"

# Setup: register a follower
POST {{host}}/api/users
{
  "user": {
    "username": "drafts_b_{{uid}}",
    "email": "drafts_b_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 201
[Captures]
token_b: jsonpath "$.user.token"

# The follower follows the author
POST {{host}}/api/profiles/drafts_a_{{uid}}/follow
Authorization: Token {{token_b}}
HTTP 200

# Create a draft with a tag used nowhere else
POST {{host}}/api/articles
Authorization: Token {{token_a}}
{
  "article": {
    "title": "Draft Article {{uid}}",
    "description": "Draft description",
    "body": "Draft body",
    "tagList": ["draftonly_{{uid}}"],
    "status": "draft"
  }
}
HTTP 201
[Asserts]
jsonpath "$.article.status" == "draft"
jsonpath "$.article.publishedAt" == null
jsonpath "$.article.revision" == 1
jsonpath "$.article.tagList" contains "draftonly_{{uid}}"
[Captures]
draft_slug: jsonpath "$.article.slug"

# Create an article without a status: it is published
POST {{host}}/api/articles
Authorization: Token {{token_a}}
{
  "article": {
    "title": "Published Article {{uid}}",
    "description": "Published description",
    "body": "Published body"
  }
}
HTTP 201
[Asserts]
jsonpath "$.article.status" == "published"
jsonpath "$.article.publishedAt" matches "^\\d{4}-\\d{2}-\\d{2}T"
jsonpath "$.article.revision" == 1

# The author can read their draft
GET {{host}}/api/articles/{{draft_slug}}
Authorization: Token {{token_a}}
HTTP 200
[Asserts]
jsonpath "$.article.status" == "draft"
jsonpath "$.article.body" == "Draft body"

# Lists exclude drafts, even for the author
GET {{host}}/api/articles?author=drafts_a_{{uid}}
Authorization: Token {{token_a}}
HTTP 200
[Asserts]
jsonpath "$.articlesCount" == 1
jsonpath "$.articles[0].status" == "published"
jsonpath "$.articles[0].revision" == 1

# Filtering by the draft's tag finds nothing
GET {{host}}/api/articles?tag=draftonly_{{uid}}
HTTP 200
[Asserts]
jsonpath "$.articlesCount" == 0

# Tags used only on drafts are hidden
GET {{host}}/api/tags
HTTP 200
[Asserts]
jsonpath "$.tags" not contains "draftonly_{{uid}}"

# The follower's feed holds only the published article
GET {{host}}/api/articles/feed
Authorization: Token {{token_b}}
HTTP 200
[Asserts]
jsonpath "$.articlesCount" == 1
jsonpath "$.articles[0].status" == "published"

# Create a second draft
POST {{host}}/api/articles
Authorization: Token {{token_a}}
{
  "article": {
    "title": "Second Draft {{uid}}",
    "description": "Second draft description",
    "body": "Second draft body",
    "status": "draft"
  }
}
HTTP 201
[Captures]
second_draft_slug: jsonpath "$.article.slug"

# The author's drafts, newest first, without bodies
GET {{host}}/api/user/drafts
Authorization: Token {{token_a}}
HTTP 200
[Asserts]
jsonpath "$.articlesCount" == 2
jsonpath "$.articles[0].slug" == "{{second_draft_slug}}"
jsonpath "$.articles[1].slug" == "{{draft_slug}}"
jsonpath "$.articles[0].status" == "draft"
jsonpath "$.articles[0].body" not exists

# Drafts paginate like other lists
GET {{host}}/api/user/drafts?limit=1&offset=1
Authorization: Token {{token_a}}
HTTP 200
[Asserts]
jsonpath "$.articlesCount" == 2
jsonpath "$.articles" count == 1
jsonpath "$.articles[0].slug" == "{{draft_slug}}"

# Update the draft with its current revision
PUT {{host}}/api/articles/{{draft_slug}}
Authorization: Token {{token_a}}
{
  "article": {
    "body": "Revised draft body",
    "revision": 1
  }
}
HTTP 200
[Asserts]
jsonpath "$.article.body" == "Revised draft body"
jsonpath "$.article.revision" == 2
jsonpath "$.article.status" == "draft"
[Captures]
draft_slug: jsonpath "$.article.slug"

# Update the draft without a revision: the last write wins
PUT {{host}}/api/articles/{{draft_slug}}
Authorization: Token {{token_a}}
{
  "article": {
    "description": "Revised description"
  }
}
HTTP 200
[Asserts]
jsonpath "$.article.description" == "Revised description"
jsonpath "$.article.revision" == 3
[Captures]
draft_slug: jsonpath "$.article.slug"

# Publish the draft
POST {{host}}/api/articles/{{draft_slug}}/publish
Authorization: Token {{token_a}}
HTTP 200
[Asserts]
jsonpath "$.article.status" == "published"
jsonpath "$.article.publishedAt" matches "^\\d{4}-\\d{2}-\\d{2}T"
jsonpath "$.article.revision" == 4
jsonpath "$.article.body" == "Revised draft body"
[Captures]
published_at: jsonpath "$.article.publishedAt"

# Publishing again changes nothing
POST {{host}}/api/articles/{{draft_slug}}/publish
Authorization: Token {{token_a}}
HTTP 200
[Asserts]
jsonpath "$.article.status" == "published"
jsonpath "$.article.publishedAt" == "{{published_at}}"
jsonpath "$.article.revision" == 4

# The published article's tag is now listed
GET {{host}}/api/tags
HTTP 200
[Asserts]
jsonpath "$.tags" contains "draftonly_{{uid}}"

# The follower's feed now holds both articles
GET {{host}}/api/articles/feed
Authorization: Token {{token_b}}
HTTP 200
[Asserts]
jsonpath "$.articlesCount" == 2

# The follower can now read it
GET {{host}}/api/articles/{{draft_slug}}
Authorization: Token {{token_b}}
HTTP 200
[Asserts]
jsonpath "$.article.status" == "published"

# One draft remains
GET {{host}}/api/user/drafts
Authorization: Token {{token_a}}
HTTP 200
[Asserts]
jsonpath "$.articlesCount" == 1
jsonpath "$.articles[0].slug" == "{{second_draft_slug}}"

# The author deletes the remaining draft
DELETE {{host}}/api/articles/{{second_draft_slug}}
Authorization: Token {{token_a}}
HTTP 204

# No drafts remain
GET {{host}}/api/user/drafts
Authorization: Token {{token_a}}
HTTP 200
[Asserts]
jsonpath "$.articlesCount" == 0
jsonpath "$.articles" count == 0
