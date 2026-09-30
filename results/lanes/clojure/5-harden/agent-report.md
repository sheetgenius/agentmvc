**Status:** BLOCKED. The app is hardened and both gates pass, but I could not make `bin/check-production` explicitly invoke `security/run-hurl.sh` against the production container after acceptance. The supplied harness runs both suites, then stops that container; the security runner is read-only.

**Gate result:** Latest `bin/check` and `bin/check-production` each exited 0: 15/15 acceptance files, 13/13 security checks, and lint with 0 errors or warnings.

**What you changed:** [http.clj](/work/app/src/conduit/http.clj) returns a JSON 400 for Muuntaja decode errors (S07) and sets `nosniff` in one response-header definition (S12). [users.clj](/work/app/src/conduit/users.clj) uses a bounded Caffeine cache to return 429 after ten failed logins per email for five minutes (S13). [README.md](/work/app/README.md) records the measures and scan limits.

**Dependencies and static findings:** OSV-Scanner found no advisories among 86 resolved packages, including Caffeine. No dedicated Clojure security analyzer is configured; clj-kondo reported no findings, so there were no false positives to dismiss.

**Run counts:** Five full gate runs: two development, three production. Seven narrower runs. Zero build failures.

**Friction log:**

- Muuntaja marked malformed JSON as a decode exception without an HTTP status; the existing handler produced a server error.
- A standalone `security/run-hurl.sh` call after the production gate failed with `Failed to connect to 127.0.0.1 port 4112`; all 13 files failed with zero requests because the harness had stopped the container.
- I tried adding that call to `bin/check-production`, then tried to adapt the runner. The latter edit was rejected as outside writable project files. I restored the passing combined harness gate, but that does not establish the requested explicit invocation.

**Agent-friendliness notes:** Muuntaja’s typed exception and the harness’s per-file results made the fixes easy to locate and verify. The opaque container lifecycle made the production script requirement impossible to complete within the available write permissions.