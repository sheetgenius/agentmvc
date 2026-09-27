**Status:** DONE.

**Gate result:** `bin/check` exited 0: 15/15 acceptance files, formatting, and warning-free compilation passed. The extended `bin/check-production` exited 0: 15/15 acceptance files and 13/13 security checks passed.

**What you changed:**

- S08: Controllers now return 422 for nonobject request envelopes; [Content](../5-harden/lib/conduit/content.ex) bounds page size and rejects out-of-range pagination values before they reach Ecto.
- S12: The API pipeline uses Phoenix’s secure-header plug to add `nosniff`.
- S13: A supervised Hammer ETS limiter caps login attempts per email at 10 per minute; the fallback returns 429 with `Retry-After`.
- [bin/check-production](../5-harden/bin/check-production) now runs all 13 security checks after acceptance. The [README](../5-harden/README.md) documents the protections and deployment boundary.

**Dependencies and static findings:** The baseline OSV scan reported no vulnerable lockfile packages; Hammer 7.5.0 was added for rate limiting. Sobelow’s HTTPS finding concerns the container’s HTTP hop. Public deployment requires an HTTPS reverse proxy and a private container port, as documented in the README; direct public exposure would leave the finding applicable. [Phoenix’s SSL guidance](https://hexdocs.pm/phoenix/1.7.1/using_ssl.html) describes this proxy setup.

**Run counts:** 3 `bin/check` runs; 3 production gate runs; 1 narrower dependency, format, and compile run. Build failures: 0. One production release failed to boot during the cleanup pass and was corrected.

**Friction log:**

- A string article envelope reached map-only code and caused S08’s 500.
- Oversized pagination needed a bound before Ecto built the query.
- Phoenix’s compile-time `force_ssl` setting could not be disabled at runtime for the HTTP production suite; the attempted toggle prevented release boot.

**Agent-friendliness notes:** Phoenix pipelines, controller fallbacks, and Ecto changesets made the security rules easy to place. Release configuration and deployment-level TLS required more care because the static finding cannot see the ingress boundary.