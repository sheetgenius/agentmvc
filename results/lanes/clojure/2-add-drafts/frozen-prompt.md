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

# Your task: add a feature

This directory already contains a working implementation that passes the official acceptance suite. Read `ENVIRONMENT.md` first. It names your stack, toolchain, port and sandbox limits.

**Add the feature specified in `realworld_spec/features/drafts/drafts.md`: article drafts, publishing and edit conflicts.**

- Its acceptance tests are in `realworld_spec/features/drafts/hurl/`. With no file arguments, `realworld_spec/bin/run-hurl <port>` now runs them together with the original 13 files. All 15 files must pass.
- Build the feature the way the goal above demands. Change existing code wherever the feature requires it, so that each rule still lives in exactly one place. Don't rework parts of the app the feature doesn't touch.
- Don't touch `.scaffold/`.

# The specification

The spec is pinned in `./realworld_spec/`:

- `realworld_spec/docs/*.md` and `realworld_spec/api/openapi.yml`: the original backend spec;
- `realworld_spec/api/hurl/*.hurl`: the official acceptance suite, 13 files;
- `realworld_spec/features/drafts/`: this feature's prose spec and its 2 Hurl files;
- `realworld_spec/bin/run-hurl PORT [file ...]`: runs the suites in Docker against `http://host.docker.internal:PORT`. File paths are relative to `realworld_spec/`, for example `features/drafts/hurl/drafts.hurl`.

The Hurl files are the definition of correct. Never edit, skip, filter or work around any test, and never change anything under `realworld_spec/`. Where prose and tests disagree, the tests win. Where the tests are silent, choose, and note the choice in the README.

# `bin/check`

`bin/check` already exists. Keep it working. With no arguments it must exit 0 only if all 15 Hurl files pass and the formatter check and linter are clean. It must still start a fresh PostgreSQL, prepare the schema from scratch, and stop everything it started.

# README

Update `README.md` so it describes the feature: routes, rules, and any spec choices.

# Hard boundaries

Never cross these:
- Work only inside this directory. Don't read, list or modify other directories, apart from reading your toolchain and package caches.
- No global installs.
- Never modify `realworld_spec/` or `.scaffold/`.
- Production basics stay: a real PostgreSQL database, hashed passwords, and spec-conformant authentication, validation and error responses.
- Do not spawn subagents.

# RETURN conditions: stop and send your final report as soon as ANY of these is true

1. **DONE.** `bin/check` is fully green: all 15 Hurl files pass, and the formatter and linter are clean. Then make **up to 2 passes** over the code you added or changed:
   - Each pass makes that code cleaner, terser and more idiomatic.
   - Each pass ends with a fully green `bin/check`.
   - Stop after a pass that finds nothing worthwhile to improve, or after 2 passes.

   Then make sure the README is current, and return.
2. **BLOCKED.** Any of these:
   - the same failure survives 3 consecutive fix attempts without a new hypothesis;
   - an environment or toolchain failure persists after 2 attempts;
   - finishing would require crossing a hard boundary.

   Report exactly what failed, the last error output, and what you tried.
3. **BUDGET.** You have run `bin/check` 50 times without a fully green run. Report the current state.

# Final report (use exactly these headings)

- **Status:** DONE, BLOCKED or BUDGET.
- **Gate result:** Hurl files passed out of 15; formatter and linter status; the final `bin/check` exit code.
- **Where the feature landed:** each file you created or changed, in one line each: what changed and why.
- **Passes:** what each pass made cleaner, and why you stopped.
- **Spec decisions:** ambiguities you resolved.
- **Run counts:** `bin/check` runs; narrower runs; compile or build failures hit.
- **Friction log:** the 3–5 problems that cost the most time or effort, each with its cause.
- **Agent-friendliness notes:** what in this stack made adding this feature easier or harder for an agent.
