# Setup: register the author
POST {{host}}/api/users
{
  "user": {
    "username": "exports_a_{{uid}}",
    "email": "exports_a_{{uid}}@test.com",
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
    "username": "exports_b_{{uid}}",
    "email": "exports_b_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 201
[Captures]
token_b: jsonpath "$.user.token"

# The author publishes an article
POST {{host}}/api/articles
Authorization: Token {{token_a}}
{
  "article": {
    "title": "Exported First {{uid}}",
    "description": "First description",
    "body": "First body",
    "tagList": ["export_{{uid}}", "second_{{uid}}"]
  }
}
HTTP 201
[Captures]
first_slug: jsonpath "$.article.slug"

# The author writes a draft
POST {{host}}/api/articles
Authorization: Token {{token_a}}
{
  "article": {
    "title": "Exported Draft {{uid}}",
    "description": "Draft description",
    "body": "Draft body",
    "status": "draft"
  }
}
HTTP 201
[Captures]
draft_slug: jsonpath "$.article.slug"

# The other user writes an article, which must not appear in the author's export
POST {{host}}/api/articles
Authorization: Token {{token_b}}
{
  "article": {
    "title": "Not Exported {{uid}}",
    "description": "Other description",
    "body": "Other body"
  }
}
HTTP 201

# Two comments on the published article
POST {{host}}/api/articles/{{first_slug}}/comments
Authorization: Token {{token_b}}
{
  "comment": {"body": "First comment"}
}
HTTP 201

POST {{host}}/api/articles/{{first_slug}}/comments
Authorization: Token {{token_a}}
{
  "comment": {"body": "Second comment"}
}
HTTP 201

# Starting an export requires a token
POST {{host}}/api/user/exports
HTTP 401
[Asserts]
jsonpath "$.errors.token[0]" == "is missing"

# Start an export: it is accepted and pending
POST {{host}}/api/user/exports
Authorization: Token {{token_a}}
HTTP 202
[Captures]
export_id: jsonpath "$.export.id"
[Asserts]
jsonpath "$.export.id" exists
jsonpath "$.export.status" == "pending"
jsonpath "$.export.createdAt" isString
jsonpath "$.export.completedAt" == null
jsonpath "$.export.articles" == null

# Wait for the background job to finish (up to 30 seconds)
GET {{host}}/api/user/exports/{{export_id}}
Authorization: Token {{token_a}}
[Options]
retry: 120
retry-interval: 250
HTTP 200
[Asserts]
jsonpath "$.export.status" == "done"

# The finished export holds the author's articles, drafts included, oldest first
GET {{host}}/api/user/exports/{{export_id}}
Authorization: Token {{token_a}}
HTTP 200
[Asserts]
jsonpath "$.export.id" exists
jsonpath "$.export.status" == "done"
jsonpath "$.export.createdAt" isString
jsonpath "$.export.completedAt" isString
jsonpath "$.export.articles" count == 2
jsonpath "$.export.articles[0].slug" == "{{first_slug}}"
jsonpath "$.export.articles[0].title" == "Exported First {{uid}}"
jsonpath "$.export.articles[0].description" == "First description"
jsonpath "$.export.articles[0].body" == "First body"
jsonpath "$.export.articles[0].tagList" count == 2
jsonpath "$.export.articles[0].tagList" contains "export_{{uid}}"
jsonpath "$.export.articles[0].tagList" contains "second_{{uid}}"
jsonpath "$.export.articles[0].status" == "published"
jsonpath "$.export.articles[0].commentsCount" == 2
jsonpath "$.export.articles[1].slug" == "{{draft_slug}}"
jsonpath "$.export.articles[1].title" == "Exported Draft {{uid}}"
jsonpath "$.export.articles[1].body" == "Draft body"
jsonpath "$.export.articles[1].tagList" count == 0
jsonpath "$.export.articles[1].status" == "draft"
jsonpath "$.export.articles[1].commentsCount" == 0

# Later changes don't alter a finished export: add an article and delete the draft
POST {{host}}/api/articles
Authorization: Token {{token_a}}
{
  "article": {
    "title": "Written Later {{uid}}",
    "description": "Later description",
    "body": "Later body"
  }
}
HTTP 201

DELETE {{host}}/api/articles/{{draft_slug}}
Authorization: Token {{token_a}}
HTTP 204

GET {{host}}/api/user/exports/{{export_id}}
Authorization: Token {{token_a}}
HTTP 200
[Asserts]
jsonpath "$.export.articles" count == 2
jsonpath "$.export.articles[1].slug" == "{{draft_slug}}"
jsonpath "$.export.articles[1].title" == "Exported Draft {{uid}}"

# Another user can't see the export
GET {{host}}/api/user/exports/{{export_id}}
Authorization: Token {{token_b}}
HTTP 404
[Asserts]
jsonpath "$.errors.export[0]" == "not found"

# A malformed id is simply not found
GET {{host}}/api/user/exports/not-an-export
Authorization: Token {{token_a}}
HTTP 404
[Asserts]
jsonpath "$.errors.export[0]" == "not found"

# Reading an export requires a token
GET {{host}}/api/user/exports/{{export_id}}
HTTP 401
[Asserts]
jsonpath "$.errors.token[0]" == "is missing"
