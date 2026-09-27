# S12 (defense in depth): JSON responses carry X-Content-Type-Options: nosniff
GET {{host}}/api/tags
HTTP 200
[Asserts]
header "X-Content-Type-Options" == "nosniff"
