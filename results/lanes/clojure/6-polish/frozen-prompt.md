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

# Your task: mastery pass

This directory contains a working implementation. `bin/check` passes all 15 acceptance files. `bin/check-production` passes the same 15 files plus 13 security checks against the production container. Read `ENVIRONMENT.md` first. It names your stack, toolchain, port and sandbox limits.

**Make a mastery pass.** Rework the code the way this language's and framework's best practitioners would write it, and the way you would most want to read it cold as a new maintainer:
- use the language and the framework to the full;
- make every file intuitive at a glance;
- make the code as terse and clean as it can be without becoming clever.

You may restructure, rename, merge, split or rewrite anything. The behavior must not change: both checks must stay green.

Don't touch `.scaffold/`, `realworld_spec/`, `security/` or `perf/`.

# Hard boundaries

Never cross these:
- Work only inside this directory. Don't read, list or modify other directories, apart from reading your toolchain and package caches.
- No global installs.
- Never modify `realworld_spec/` or `.scaffold/`.
- Production basics stay: a real PostgreSQL database, hashed passwords, and spec-conformant authentication, validation and error responses.
- Do not spawn subagents.

# RETURN conditions: stop and send your final report as soon as ANY of these is true

1. **DONE.** Work in **up to 3 passes.** Each pass re-reads every file you own and ends with `bin/check` and `bin/check-production` both green. Stop after a pass that finds nothing worthwhile to improve, or after 3 passes. Then update the README so it describes the code as it now is, and return.
2. **BLOCKED.** Any of these:
   - the same failure survives 3 consecutive fix attempts without a new hypothesis;
   - an environment or toolchain failure persists after 2 attempts;
   - finishing would require crossing a hard boundary.

   Report exactly what failed, the last error output, and what you tried.
3. **BUDGET.** You have run the checks 50 times without them being green. Report the current state.

# Final report (use exactly these headings)

- **Status:** DONE, BLOCKED or BUDGET.
- **Gate result:** Hurl acceptance files passed out of 15, security checks passed out of 13, lint, exit codes.
- **Code map:** each file you own and its role, in one line each.
- **What each pass changed:** per pass, what became more fluent, clearer or terser, and why you stopped.
- **Run counts:** check runs; narrower runs; build failures hit.
- **Friction log:** the 3–5 problems that cost the most time or effort, each with its cause.
- **Agent-friendliness notes:** what in this stack made this work easier or harder for an agent.
