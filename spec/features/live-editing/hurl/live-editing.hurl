# Author and unrelated user
POST {{host}}/api/users
{"user":{"username":"live_a_{{uid}}","email":"live_a_{{uid}}@test.com","password":"password123"}}
HTTP 201
[Captures]
author_token: jsonpath "$.user.token"

POST {{host}}/api/users
{"user":{"username":"live_b_{{uid}}","email":"live_b_{{uid}}@test.com","password":"password123"}}
HTTP 201
[Captures]
other_token: jsonpath "$.user.token"

POST {{host}}/api/articles
Authorization: Token {{author_token}}
{"article":{"title":"Live Draft {{uid}}","description":"private","body":"Before","status":"draft"}}
HTTP 201
[Captures]
slug: jsonpath "$.article.slug"
[Asserts]
jsonpath "$.article.revision" == 1

# Only the author may create the link
POST {{host}}/api/articles/{{slug}}/share
Authorization: Token {{other_token}}
HTTP 404

POST {{host}}/api/articles/{{slug}}/share
Authorization: Token {{author_token}}
HTTP 201
[Captures]
share_id: jsonpath "$.share.id"
share_key: jsonpath "$.share.key"
[Asserts]
jsonpath "$.share.id" isString
jsonpath "$.share.key" isString

# An uncredentialed reader learns nothing
GET {{host}}/api/shares/{{share_id}}/article
HTTP 404

GET {{host}}/api/shares/{{share_id}}/article
X-Share-Key: wrong-key
HTTP 404

GET {{host}}/api/shares/{{share_id}}/article
X-Share-Key: {{share_key}}
HTTP 200
[Asserts]
jsonpath "$.article.title" == "Live Draft {{uid}}"
jsonpath "$.article.body" == "Before"
jsonpath "$.article.revision" == 1
jsonpath "$.article.description" not exists

# The link grants title/body editing with the same revision rule as drafts
PUT {{host}}/api/shares/{{share_id}}/article
X-Share-Key: {{share_key}}
{"article":{"title":"Renamed Live Draft {{uid}}","body":"After","revision":1}}
HTTP 200
[Captures]
new_slug: jsonpath "$.article.slug"
[Asserts]
jsonpath "$.article.revision" == 2
jsonpath "$.article.body" == "After"

# The same share ID remains useful when a title changes the slug
GET {{host}}/api/shares/{{share_id}}/article
X-Share-Key: {{share_key}}
HTTP 200
[Asserts]
jsonpath "$.article.title" == "Renamed Live Draft {{uid}}"
jsonpath "$.article.revision" == 2

PUT {{host}}/api/shares/{{share_id}}/article
X-Share-Key: {{share_key}}
{"article":{"title":"Stale","body":"Stale","revision":1}}
HTTP 409
[Asserts]
jsonpath "$.errors.revision[0]" == "is stale"
jsonpath "$.article.body" == "After"
jsonpath "$.article.revision" == 2

# A share cannot change article status or other fields
PUT {{host}}/api/shares/{{share_id}}/article
X-Share-Key: {{share_key}}
{"article":{"title":"Bad","body":"Bad","revision":2,"status":"published"}}
HTTP 422

GET {{host}}/api/shares/{{share_id}}/article
X-Share-Key: {{share_key}}
HTTP 200
[Asserts]
jsonpath "$.article.revision" == 2
jsonpath "$.article.body" == "After"

# Rotating the link revokes the old one
POST {{host}}/api/articles/{{new_slug}}/share
Authorization: Token {{author_token}}
HTTP 201
[Captures]
new_share_id: jsonpath "$.share.id"
new_share_key: jsonpath "$.share.key"

GET {{host}}/api/shares/{{share_id}}/article
X-Share-Key: {{share_key}}
HTTP 404

GET {{host}}/api/shares/{{new_share_id}}/article
X-Share-Key: {{new_share_key}}
HTTP 200
[Asserts]
jsonpath "$.article.revision" == 2

DELETE {{host}}/api/articles/{{new_slug}}/share
Authorization: Token {{author_token}}
HTTP 204

GET {{host}}/api/shares/{{new_share_id}}/article
X-Share-Key: {{new_share_key}}
HTTP 404
