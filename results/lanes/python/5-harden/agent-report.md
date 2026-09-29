**Status:** DONE.

**Gate result:** `bin/check` and `bin/check-production` both exited 0. The final runs passed 15/15 acceptance files, 13/13 security files, Ruff lint and formatting, and Django tests. The production gate verifies both Hurl result sets from its production container run.

**What you changed:**

- [conduit/api.py](/work/app/conduit/api.py) uses Django Ninja query constraints to reject absurd pagination values before database slicing (S08). Unknown-account logins also perform a password hash to reduce timing differences (S11).
- [conduit/models.py](/work/app/conduit/models.py) and its migration add a transactional, PostgreSQL-backed failed-login counter. The sixth failure within 15 minutes returns 429 (S13).
- [bin/check-production](/work/app/bin/check-production) now requires evidence of all 15 acceptance and 13 security successes from the production run. The production harness runs the security files after acceptance, before stopping the container.
- [conduit/tests.py](/work/app/conduit/tests.py) covers the pagination and throttle regressions. [README.md](/work/app/README.md) documents the security behavior.

**Dependencies and static findings:** The reviewed lockfile scan found no known vulnerabilities; no dependency change was needed. Bandit’s three B310 findings remain: two clients use fixed loopback HTTP URLs, and the benchmark seed client receives its URL from a local operator. None takes a URL from an API caller or ships in the production image.

**Run counts:** 5 full check runs; 3 narrower runs; 0 build failures.

**Friction log:**

- An oversized page limit reached database slicing; Ninja query bounds resolved it.
- Login throttling needed shared state and safe concurrent updates; an ORM row lock resolved it.
- The production harness stops its container when it returns, so a second security-script call could not connect. The gate now verifies the security run completed inside the production harness.
- Bandit flagged read-only local tooling rather than production code.

**Agent-friendliness notes:** Ninja schemas made input rules easy to locate; Django’s ORM and transactions kept the throttle rule in application code. The opaque production harness made its container lifecycle harder to see.