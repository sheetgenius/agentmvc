# S13 (defense in depth): repeated failed logins for one account get rate limited
POST {{host}}/api/users
{
  "user": {
    "username": "sec_s13_{{uid}}",
    "email": "sec_s13_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 201
[Captures]
token: jsonpath "$.user.token"


POST {{host}}/api/users/login
[Options]
repeat: 20
{
  "user": {"email": "sec_s13_{{uid}}@test.com", "password": "wrongpassword"}
}
HTTP *

POST {{host}}/api/users/login
{
  "user": {"email": "sec_s13_{{uid}}@test.com", "password": "wrongpassword"}
}
HTTP 429
