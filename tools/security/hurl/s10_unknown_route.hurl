# S10: an unknown route returns 404 without internals
GET {{host}}/api/does-not-exist-{{uid}}
HTTP 404
[Asserts]
body not contains "Traceback"
body not contains "backtrace"
body not contains "panicked"
body not contains ".rb:"
body not contains ".ex:"
body not contains ".rs:"

