# S07: malformed JSON gets a client error, not a server error, and leaks no internals
POST {{host}}/api/users
Content-Type: application/json
```
{"user": {"username": "broken"
```
HTTP *
[Asserts]
status >= 400
status < 500
body not contains "Traceback"
body not contains "backtrace"
body not contains "panicked"
body not contains ".rb:"
body not contains ".ex:"
body not contains ".rs:"

