# S02: a real token with its signature stripped or replaced is rejected
POST {{host}}/api/users
{
  "user": {
    "username": "sec_s02_{{uid}}",
    "email": "sec_s02_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 201
[Captures]
signed_part: jsonpath "$.user.token" regex "^([^.]+\\.[^.]+)\\."


GET {{host}}/api/user
Authorization: Token {{signed_part}}.
HTTP 401

GET {{host}}/api/user
Authorization: Token {{signed_part}}.c2lnbmF0dXJl
HTTP 401
