# S03: garbage tokens are rejected with 401, never a server error
GET {{host}}/api/user
Authorization: Token abc
HTTP 401

GET {{host}}/api/user
Authorization: Token a.b.c
HTTP 401
