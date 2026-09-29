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

# Your task: performance tuning

This directory contains a working, production-packaged implementation: `bin/check` and `bin/check-production` both pass. Read `ENVIRONMENT.md` first. It names your stack, toolchain, port and sandbox limits.

Its production image has been benchmarked. The results are in `perf/baseline/results.json`:
- for each scenario: throughput, p50/p95/p99 latency, SQL statements per request, and peak memory;
- for the image: cold start, idle memory and size.

The workload and limits are fixed. The app and PostgreSQL each run in a container limited to 2 CPUs and 1 GB. The load is `perf/load.js` with 16 concurrent users, against data seeded by `perf/seed.py`.

**Make the app fast where it matters for this workload, without making the code worse.**

- **Target what the numbers show,** for example SQL statements per request on list endpoints, latency tails, throughput or memory.
- **Use changes this stack's best practitioners would recognize:** better queries, preloading, indexes, and sensible production server and pool settings.
- **Nothing speculative:** no caching that could serve stale data, and no changes to the benchmark, the data, the load or the limits.
- **The goal above still applies:** terse, idiomatic, each rule in one place.
- **Measure** with `perf/bench.sh`. It builds your image and runs the same benchmark, writing to `perf/latest/results.json`.
- **Keep** `bin/check` and `bin/check-production` green.
- **Don't touch** `.scaffold/`, `realworld_spec/`, or the benchmark files in `perf/` other than its outputs.

# Hard boundaries

Never cross these:
- Work only inside this directory. Don't read, list or modify other directories, apart from reading your toolchain and package caches.
- No global installs.
- Never modify `realworld_spec/` or `.scaffold/`.
- Production basics stay: a real PostgreSQL database, hashed passwords, and spec-conformant authentication, validation and error responses.
- Do not spawn subagents.

# RETURN conditions: stop and send your final report as soon as ANY of these is true

1. **DONE.** Work in **up to 3 tuning iterations**:
   - Each iteration ends with `bin/check` and `bin/check-production` green, and a fresh `perf/bench.sh` run.
   - Stop after an iteration that brings no meaningful gain, or after 3 iterations.

   Then update the README with the performance changes, and return.
2. **BLOCKED.** Any of these:
   - the same failure survives 3 consecutive fix attempts without a new hypothesis;
   - an environment or toolchain failure persists after 2 attempts;
   - finishing would require crossing a hard boundary.

   Report exactly what failed, the last error output, and what you tried.
3. **BUDGET.** You have run the checks 50 times without both being green. Report the current state.

# Final report (use exactly these headings)

- **Status:** DONE, BLOCKED or BUDGET.
- **Gate result:** the `bin/check` and `bin/check-production` results.
- **Before and after:** for each scenario, requests per second, p95 latency and SQL statements per request, from the baseline and from your final benchmark.
- **What you changed:** each change and why, in one line each.
- **What didn't help:** anything you tried and reverted.
- **Run counts:** check runs; benchmark runs; build failures hit.
- **Friction log:** the 3–5 problems that cost the most time or effort, each with its cause.
- **Agent-friendliness notes:** what in this stack made performance work easier or harder for an agent.
