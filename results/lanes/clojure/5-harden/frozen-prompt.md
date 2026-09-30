# Goal

This directory holds a backend implementing the **RealWorld ("Conduit") API**. It is a pilot for rewriting a much larger product on this stack. In that rewrite, AI agents will learn the product by reading its source, so the code must let a reader absorb as much of the domain as possible, as fast as possible.

The bar is the simplicity and beauty of Ruby on Rails at its best: code that reads almost like a description of the domain, because the framework and its conventions carry everything else. Whatever stack you are on, reach for that level of simplicity through **this stack's own best idioms and libraries**. Don't imitate Ruby syntax or bend the language against its grain.

Make the code **clean, terse and idiomatic**:

- **Terse.** Every line should say something about the product: a rule, a data shape, a relationship. Remove line noise: boilerplate, plumbing, repetition, restated defaults, and generated files or configuration the app doesn't use.
- **Let the framework carry the load.** Use the framework's conventions, generators and built-in features, plus the best mainstream libraries, for everything they can do. Then the code you write is only what is specific to this product.
- **Idiomatic.**
  - An experienced developer in this stack should recognize every file at a glance, find each rule where the stack's conventions put it, and understand it without running it.
  - Keep business logic in the application code, not in database functions, triggers or SQL strings inside migrations.
  - Each rule lives in exactly one place.
- **Clean, not clever.**
  - Use clear domain names.
  - No code golf.
  - No macros or metaprogramming invented just to shorten code.
  - Keep the stack's default formatter and linter settings.
  - Comment only to explain a non-obvious *why*.

The behavior is fixed: the official RealWorld acceptance suite must pass completely.

You are working alone and unsupervised. Keep going until one of the RETURN conditions at the end is met.

# Your task: security hardening

This directory contains a working, production-packaged implementation: `bin/check` and `bin/check-production` both pass. Read `ENVIRONMENT.md` first. It names your stack, toolchain, port and sandbox limits.

A security review ran against your production container. Its results are in `security/baseline/results.json`:

- **13 black-box checks** in `security/hurl/`. S01–S11 are core; S12 and S13 are defense in depth. `security/run-hurl.sh BASE_URL` runs them. Each file begins with a comment saying what it tests.
- **A dependency scan** of your lockfile (OSV-Scanner).
- **Static analysis,** where this stack has a mainstream analyzer.

**Harden the app so that every check passes, the way this stack's best practitioners would.**

- **Checks:** make all 13 checks pass against the production container.
- **`bin/check-production`:** extend it to run `security/run-hurl.sh` against the production container, after the acceptance suite. It must exit 0 only if all 15 acceptance files and all 13 security checks pass.
- **Dependencies:** resolve vulnerable packages where a fixed version or a clean alternative exists. If none exists, explain why in the README.
- **Static findings:** address the analyzer's real findings, and explain any you judge to be false positives.
- **Use the framework's own mechanisms** wherever they exist. The goal above still applies: terse, idiomatic, each rule in one place.
- **Don't touch** `.scaffold/`, `realworld_spec/` or `security/hurl/`.

# Hard boundaries

Never cross these:
- Work only inside this directory. Don't read, list or modify other directories, apart from reading your toolchain and package caches.
- No global installs.
- Never modify `realworld_spec/` or `.scaffold/`.
- Production basics stay: a real PostgreSQL database, hashed passwords, and spec-conformant authentication, validation and error responses.
- Do not spawn subagents.

# RETURN conditions: stop and send your final report as soon as ANY of these is true

1. **DONE.** `bin/check` and the extended `bin/check-production` both exit 0. Then make **1 pass** over what you changed, making it cleaner, terser and more idiomatic, ending with both green. Then update the README with the security measures, and return.
2. **BLOCKED.** Any of these:
   - the same failure survives 3 consecutive fix attempts without a new hypothesis;
   - an environment or toolchain failure persists after 2 attempts;
   - finishing would require crossing a hard boundary.

   Report exactly what failed, the last error output, and what you tried.
3. **BUDGET.** You have run the checks 50 times without them being green. Report the current state.

# Final report (use exactly these headings)

- **Status:** DONE, BLOCKED or BUDGET.
- **Gate result:** Hurl acceptance files passed out of 15, security checks passed out of 13, lint, exit codes.
- **What you changed:** each change, which check or finding it addresses, and why this is the idiomatic mechanism.
- **Dependencies and static findings:** what you fixed, and what you judged not applicable and why.
- **Run counts:** check runs; narrower runs; build failures hit.
- **Friction log:** the 3–5 problems that cost the most time or effort, each with its cause.
- **Agent-friendliness notes:** what in this stack made this work easier or harder for an agent.
