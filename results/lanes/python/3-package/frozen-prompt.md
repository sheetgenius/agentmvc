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

# Your task: production packaging

This directory already contains a working implementation that passes all 15 acceptance files (the RealWorld suite plus the drafts feature). Read `ENVIRONMENT.md` first. It names your stack, toolchain, port and sandbox limits.

**Package the app for production, without changing its behavior.**

- **Dockerfile.** Add a `Dockerfile` in this directory that builds an optimized production image: a release or production build, running in production mode.
- **Runtime contract.** A container from that image receives only these environment variables:
  - `DATABASE_URL`, a PostgreSQL URL;
  - `SECRET_KEY_BASE`, 128 hex characters;
  - `PORT`.

  Given those, it must prepare the schema on an empty database, then serve the API on `0.0.0.0:$PORT` in production mode. It must not need any file from this directory at run time: no bind mounts.
- **`bin/check-production`.** Add this script. It must:
  - build the image;
  - start a fresh PostgreSQL;
  - run the container, publishing the port given in `ENVIRONMENT.md`;
  - run `realworld_spec/bin/run-hurl <port>` with all 15 files against it;
  - stop everything it started, even on failure.

  It must exit 0 only if every file passes.
- **Keep `bin/check` working.**
- **Configuration:** configure production the way this stack's best practitioners would ship it, with sensible defaults and nothing speculative. Change application code only where production mode requires it.
- **Don't touch `.scaffold/` or `realworld_spec/`.**

# Hard boundaries

Never cross these:
- Work only inside this directory. Don't read, list or modify other directories, apart from reading your toolchain and package caches.
- No global installs.
- Never modify `realworld_spec/` or `.scaffold/`.
- Production basics stay: a real PostgreSQL database, hashed passwords, and spec-conformant authentication, validation and error responses.
- Do not spawn subagents.

# RETURN conditions: stop and send your final report as soon as ANY of these is true

1. **DONE.** Both `bin/check` and `bin/check-production` exit 0. Then make **1 pass** over what you added, making it cleaner, terser and more idiomatic, and end that pass with both checks green. Then update the README with how to build and run the production image, and return.
2. **BLOCKED.** Any of these:
   - the same failure survives 3 consecutive fix attempts without a new hypothesis;
   - an environment or toolchain failure persists after 2 attempts;
   - finishing would require crossing a hard boundary.

   Report exactly what failed, the last error output, and what you tried.
3. **BUDGET.** You have run the checks 50 times without both being green. Report the current state.

# Final report (use exactly these headings)

- **Status:** DONE, BLOCKED or BUDGET.
- **Gate result:** the `bin/check` and `bin/check-production` results (Hurl files passed out of 15, lint, exit codes).
- **What you added:** each file created or changed, in one line each.
- **Production choices:** the server, concurrency settings, logging, how the schema is prepared, and the image base, each with why.
- **Run counts:** check runs; narrower runs; build failures hit.
- **Friction log:** the 3–5 problems that cost the most time or effort, each with its cause.
- **Agent-friendliness notes:** what in this stack made packaging for production easier or harder for an agent.
