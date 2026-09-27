# S01: a token signed with "alg": "none" is rejected
GET {{host}}/api/user
Authorization: Token eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxIiwiaWQiOjEsInBpZCI6IjAwMDAwMDAwLTAwMDAtMDAwMC0wMDAwLTAwMDAwMDAwMDAwMCIsImV4cCI6NDEwMjQ0NDgwMH0.
HTTP 401
