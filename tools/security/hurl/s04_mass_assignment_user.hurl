# S04: server-owned user fields can't be set by the client
POST {{host}}/api/users
{
  "user": {
    "username": "sec_s04_{{uid}}",
    "email": "sec_s04_{{uid}}@test.com",
    "password": "password123",
    "admin": true,
    "id": 424242,
    "token": "forged"
  }
}
HTTP 201
[Asserts]
jsonpath "$.user.token" != "forged"
jsonpath "$.user.admin" not exists
[Captures]
token: jsonpath "$.user.token"

PUT {{host}}/api/user
Authorization: Token {{token}}
{
  "user": {
    "bio": "hello",
    "token": "forged",
    "id": 1
  }
}
HTTP 200
[Asserts]
jsonpath "$.user.token" != "forged"
jsonpath "$.user.username" == "sec_s04_{{uid}}"
