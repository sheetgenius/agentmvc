# Security: what does each framework protect for free?

[`tools/security/scan.py`](../../tools/security/scan.py) scans a production image in three ways:
- 13 black-box checks;
- a dependency scan with OSV-Scanner;
- the stack's mainstream static analyzer, where one exists.

The step-4 images were the baseline. In step 5, each agent received its own results and the checks, and was asked to make every check pass the way its stack's best practitioners would.

| Check | What it tests |
| --- | --- |
| S01 | A forged `alg: none` token is rejected. |
| S02 | A real token with its signature stripped or replaced is rejected. |
| S03 | Garbage tokens are rejected. |
| S04 | Server-owned user fields can't be mass-assigned. |
| S05 | Server-owned article fields can't be mass-assigned. |
| S06 | Injection-shaped filter values are treated as plain data. |
| S07 | Malformed JSON gets a 4xx and leaks no stack trace. |
| S08 | Wrong types and absurd parameters get a 4xx, never a 5xx. |
| S09 | A 2 MB body with 2,000 tags doesn't cause a 5xx. |
| S10 | An unknown route returns 404 without internals. |
| S11 | Failed logins don't reveal whether an account exists. |
| S12 *(defense in depth)* | Responses carry `X-Content-Type-Options: nosniff`. |
| S13 *(defense in depth)* | Repeated failed logins are rate limited (`429`). |

## Hypotheses, written before the scan ran

- **H1:** all three pass the token, mass-assignment, injection and enumeration checks (S01–S06, S11).
- **H2:** they differ on defense in depth. Rails sends `nosniff` by default; Phoenix's API pipeline and Loco don't. None rate-limits login, although Rails 8 ships `rate_limit`.
- **H3:** hardening takes the least code in Rails, where `rate_limit` is one line and the security headers are a framework default.

## Results

| | Rails | Phoenix | Loco |
| --- | ---: | ---: | ---: |
| Checks passed before hardening (of 13) | 11 | 10 | 11 |
| Failed before hardening | S08, S13 | S08, S12, S13 | S12, S13 |
| Checks passed after hardening | 13 | 13 | 13 |
| Code to harden, tokens | 514 | 531 (1.03×) | 225 (0.44×) |
| Dependencies scanned (OSV) | 101 | 24 | 551 |
| Vulnerable dependencies | 0 | 0 | 1: `rsa` 0.9.10, RUSTSEC-2023-0071 |
| Static analyzer findings, before → after | Brakeman: 0 → 0 | Sobelow: 1 → 2 | none exists |

What each agent changed:

| Check | Rails | Phoenix | Loco |
| --- | --- | --- | --- |
| S08, wrong shapes | Rails 8's `params.expect`, plus a string check it doesn't do; pagination bounded, otherwise 422 | Map patterns in controller heads, with a fallback clause returning 422; limit capped at 100 | Already passing: typed request extractors |
| S12, `nosniff` | Already passing: a framework default | `put_secure_browser_headers` in the API pipeline | The built-in `secure_headers` middleware, off by default, switched on in configuration |
| S13, login rate limit | Built-in `rate_limit`, one line | The Hammer library: a supervised ETS limiter, 429 with `Retry-After` | The Governor crate: a keyed limiter, pruned periodically |
| New dependencies | none | Hammer | Governor |

All three limiters keep their counts in one server's memory, so none of them limits across several servers.

## Reading

- **H1 holds, and more broadly than predicted.** All three also passed malformed JSON, oversized bodies and unknown routes (S07, S09, S10) from the start.
- **The one core failure was the same request in Rails and Phoenix:** an `article` sent as a string instead of an object got a 500. Loco's typed extractors rejected it with a 4xx before any handler ran. That's the one place where the type system caught something the dynamic stacks missed.
- **H2 holds.**
  - Only Rails sent `nosniff` by default.
  - None rate-limited logins.
- **H3 doesn't hold: Loco's hardening was the cheapest.**
  - Its types had already covered S08, and its headers were one switch.
  - Rails' rate limit was one line, as predicted. But `params.expect` accepts numbers where strings are expected, so Rails needed an extra type check, plus pagination bounds.
  - Phoenix paid for both S08 and S13, including a third-party library.
- **What each framework gives for free:**
  - Rails ships the headers and the rate limiter.
  - Loco's types handle input shapes, and it ships headers that are off by default, but no rate limiter.
  - Phoenix ships a header plug and neither of the others.
- **Unpatched advisories need judgment, not code.**
  - RUSTSEC-2023-0071, a timing side channel in RSA, has no fixed release. It reaches Loco through `loco-rs` → `jsonwebtoken` → `rsa`.
  - The agent traced it with `cargo tree` and documented why it doesn't apply: the app signs tokens with HMAC and never uses RSA private keys.
- **Static findings.**
  - Brakeman found nothing, before or after.
  - Sobelow flagged HTTPS not being enforced in Phoenix's `prod.exs`. Phoenix reads `force_ssl` at compile time, so enabling it broke the HTTP-based production check. The agent documented TLS termination at a reverse proxy instead.
  - Adding the secure-headers plug made Sobelow raise a second finding: a missing Content-Security-Policy. That check is aimed at HTML pages, not a JSON API, and the agent never saw it, because it only had the baseline scan.
- **After step 6,** a rescan of the polished images gave the same results: 13/13 everywhere, with the same dependency and analyzer findings.

The raw results are in [`results/security/`](../../results/security/).
