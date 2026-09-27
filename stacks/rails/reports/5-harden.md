## Status

DONE.

## Gate result

`bin/check` exited 0: **15/15** acceptance files passed and Omakase lint found no offenses. The extended `bin/check-production` exited 0: **15/15** acceptance files and **13/13** security checks passed against the production container.

## What you changed

- Used Rails `params.expect` and string-field checks to return client errors for malformed payloads (S08). Kept the required 422 response for invalid article tags.
- Validated pagination values before querying (S08) and used Rails’ built-in login rate limiter (S13).
- Extended [bin/check-production](../5-harden/bin/check-production) to run the security suite after acceptance. Documented the measures in [README.md](../5-harden/README.md).

## Dependencies and static findings

The baseline OSV-Scanner report lists no vulnerable packages; Brakeman lists no findings. There were no dependency fixes or false positives to resolve.

## Run counts

5 full gate runs: 3 `bin/check`, 2 `bin/check-production`. Narrower runs: 0. Build failures: 0.

## Friction log

- Rails `expect` returned 400 for `tagList: null`; the acceptance contract requires 422.
- `expect` permits numeric scalars, so string fields needed an additional type check.
- Login throttling needed an account-specific key so attempts for different accounts did not share one limit.

## Agent-friendliness notes

Rails made the hardening easy to locate: request shape checks live in controllers, and throttling uses a controller feature. The main subtlety was where Rails’ parameter filtering differed from the API’s required error response.