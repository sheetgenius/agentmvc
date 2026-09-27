# S08: wrong types and absurd parameters get client errors, never server errors
POST {{host}}/api/users
{
  "user": {
    "username": "sec_s08_{{uid}}",
    "email": "sec_s08_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 201
[Captures]
token: jsonpath "$.user.token"


POST {{host}}/api/users
{
  "user": {"username": 123, "email": ["a"], "password": {"x": 1}}
}
HTTP *
[Asserts]
status >= 400
status < 500

POST {{host}}/api/articles
Authorization: Token {{token}}
{
  "article": "just a string"
}
HTTP *
[Asserts]
status >= 400
status < 500

POST {{host}}/api/articles
Authorization: Token {{token}}
{
  "article": {"title": "t", "description": "d", "body": "b", "tagList": "not-a-list"}
}
HTTP *
[Asserts]
status >= 400
status < 500

GET {{host}}/api/articles?limit=abc
HTTP *
[Asserts]
status < 500

GET {{host}}/api/articles?limit=-5&offset=-5
HTTP *
[Asserts]
status < 500

GET {{host}}/api/articles?limit=99999999999999999999
HTTP *
[Asserts]
status < 500

DELETE {{host}}/api/articles/nothing-{{uid}}/comments/abc
Authorization: Token {{token}}
HTTP *
[Asserts]
status >= 400
status < 500
