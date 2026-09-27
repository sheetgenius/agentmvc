# S11: failed logins don't reveal whether an account exists
POST {{host}}/api/users
{
  "user": {
    "username": "sec_s11_{{uid}}",
    "email": "sec_s11_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 201
[Captures]
token: jsonpath "$.user.token"


POST {{host}}/api/users/login
{
  "user": {"email": "nobody_{{uid}}@test.com", "password": "wrongpassword"}
}
HTTP 401
[Captures]
unknown_account_body: body

POST {{host}}/api/users/login
{
  "user": {"email": "sec_s11_{{uid}}@test.com", "password": "wrongpassword"}
}
HTTP 401
[Asserts]
body == "{{unknown_account_body}}"
