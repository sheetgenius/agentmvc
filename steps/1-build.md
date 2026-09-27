# Goal

This directory is for a backend implementing the **RealWorld ("Conduit") API**. It is a pilot for rewriting a much larger product on this stack. In that rewrite, AI agents will learn the product by reading its source, so the code must let a reader absorb as much of the domain as possible, as fast as possible.

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

# Where to start

Read `ENVIRONMENT.md` first. It names your stack, toolchain, port and sandbox limits.

- **If this directory already contains an implementation,** it passes the acceptance suite. Refine it toward the goal above. Rework it as deeply as you judge worthwhile; rewriting any part is fine. Keep `bin/check` working, and don't touch `.scaffold/`.
- **If it contains only `realworld_spec/` and `ENVIRONMENT.md`,** build the app:
  1. Run the stack's generator.
  2. Before changing anything, snapshot the untouched generator output into `.scaffold/` using the command in `ENVIRONMENT.md`. A reviewer compares your work against it.
  3. Build the app.

# The specification

The spec is pinned in `./realworld_spec/`, copied unchanged from the official RealWorld repository:

- `realworld_spec/docs/*.md`: the prose backend spec (endpoints, response format, error handling, CORS, tests);
- `realworld_spec/api/openapi.yml`: the OpenAPI contract;
- `realworld_spec/api/hurl/*.hurl`: the official acceptance suite, 13 files;
- `realworld_spec/bin/run-hurl PORT [hurl/<file>.hurl ...]`: runs that suite in Docker against `http://host.docker.internal:PORT`. The files call `{{host}}/api/...`. Your server may listen on `127.0.0.1` or `0.0.0.0`.

The Hurl suite is the definition of correct. Never edit, skip, filter or work around any test, and never change anything under `realworld_spec/`. Where the prose and the suite disagree, the suite wins. Where the suite is silent, choose, and note the choice in the README.

# `bin/check`

A reviewer will run `bin/check` with no arguments. It must exit 0 only if everything passes. It must:

- start a fresh PostgreSQL in Docker, using a Docker Compose project name that includes this directory's name;
- prepare the schema from scratch;
- boot the app on the port given in `ENVIRONMENT.md`;
- run `realworld_spec/bin/run-hurl <port>` with all 13 files;
- run the formatter check and linter given in `ENVIRONMENT.md`;
- stop everything it started, even on failure.

If `bin/check` already exists, keep it working.

# README

Keep a short `README.md` covering:
- how to run the app;
- each library and why;
- how the code is organized;
- spec choices;
- if you refined an existing implementation, what you changed and why.

# Hard boundaries

Never cross these:
- Work only inside this directory. Don't read, list or modify other directories, apart from reading your toolchain and package caches.
- No global installs.
- Never modify `realworld_spec/` or `.scaffold/`.
- Production basics stay: a real PostgreSQL database, hashed passwords, and spec-conformant authentication, validation and error responses.
- Do not spawn subagents.

# RETURN conditions: stop and send your final report as soon as ANY of these is true

1. **DONE.** `bin/check` is fully green: all 13 Hurl files pass, and the formatter and linter are clean. Then work toward the goal in **passes**:
   - In each pass, re-read every file you own and make it cleaner, terser and more idiomatic.
   - Each pass ends with a fully green `bin/check`.
   - Stop after a pass that finds nothing worthwhile to improve, or after 3 passes, whichever comes first.

   Then make sure the README is current, and return.
2. **BLOCKED.** Any of these:
   - the same failure survives 3 consecutive fix attempts without a new hypothesis;
   - an environment or toolchain failure persists after 2 attempts;
   - finishing would require crossing a hard boundary.

   Report exactly what failed, the last error output, and what you tried.
3. **BUDGET.** You have run `bin/check` 50 times without a fully green run. Report the current state.

# Final report (use exactly these headings)

- **Status:** DONE, BLOCKED or BUDGET.
- **Gate result:** Hurl files passed out of 13; formatter and linter status; the final `bin/check` exit code.
- **Libraries:** each dependency and its reason.
- **Code map:** each file you own and its role, in one line each.
- **What you did toward the goal:** per pass, what became cleaner, terser or more idiomatic, and why you stopped.
- **Spec decisions:** ambiguities you resolved.
- **Run counts:** `bin/check` runs; narrower runs; compile or build failures hit.
- **Friction log:** the 3–5 problems that cost the most time or effort, each with its cause.
- **Agent-friendliness notes:** what in this stack made the work easier or harder for an agent.
