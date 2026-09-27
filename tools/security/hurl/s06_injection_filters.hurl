# S06: injection-shaped filter values are treated as plain data
GET {{host}}/api/articles
[QueryStringParams]
tag: ' OR '1'='1
HTTP 200
[Asserts]
jsonpath "$.articlesCount" == 0

GET {{host}}/api/articles
[QueryStringParams]
author: x' OR 1=1--
HTTP 200
[Asserts]
jsonpath "$.articlesCount" == 0

GET {{host}}/api/articles
[QueryStringParams]
favorited: x" OR "1"="1
HTTP 200
[Asserts]
jsonpath "$.articlesCount" == 0

GET {{host}}/api/profiles/x%27%20OR%201%3D1--
HTTP 404
