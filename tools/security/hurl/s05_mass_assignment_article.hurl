# S05: server-owned article fields can't be set by the client
POST {{host}}/api/users
{
  "user": {
    "username": "sec_s05_{{uid}}",
    "email": "sec_s05_{{uid}}@test.com",
    "password": "password123"
  }
}
HTTP 201
[Captures]
token: jsonpath "$.user.token"


POST {{host}}/api/articles
Authorization: Token {{token}}
{
  "article": {
    "title": "Mass Assignment {{uid}}",
    "description": "d",
    "body": "b",
    "slug": "hijacked-slug-{{uid}}",
    "favoritesCount": 999,
    "favorited": true,
    "createdAt": "2000-01-01T00:00:00Z",
    "author": {"username": "someone_else"},
    "revision": 99,
    "status": "draft",
    "publishedAt": "2000-01-01T00:00:00Z"
  }
}
HTTP 201
[Asserts]
jsonpath "$.article.slug" != "hijacked-slug-{{uid}}"
jsonpath "$.article.favoritesCount" == 0
jsonpath "$.article.favorited" == false
jsonpath "$.article.createdAt" not startsWith "2000"
jsonpath "$.article.author.username" == "sec_s05_{{uid}}"
jsonpath "$.article.revision" == 1
jsonpath "$.article.publishedAt" == null
