# S09: a 2 MB article with 2,000 tags doesn't crash the server
POST {{host}}/api/users
{
  "user": {
    "username": "sec_s09_{{uid}}",
    "email": "sec_s09_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 201
[Captures]
token: jsonpath "$.user.token"


POST {{host}}/api/articles
Authorization: Token {{token}}
Content-Type: application/json
file,oversized.json;
HTTP *
[Asserts]
status < 500
