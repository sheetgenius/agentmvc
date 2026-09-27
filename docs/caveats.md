# Caveats

- **One run per stack per step.** Agent runs vary. Treat differences under about 20% as noise; the size of a gap is more reliable than its exact value.
- **One model.** Every run used Codex `gpt-6-sol` at `xhigh` reasoning. The results reflect what that model writes well in each stack, including how familiar it is with each one. A second model would be the most useful check.
- **One reviewer.** The feature specs, prompts, security checks, comprehension questions and answer keys were all written by the same reviewer, Claude.
  - Hypotheses were written down before each step ran.
  - Both features were validated by throwaway implementations before any agent saw them.
  - Each answer key was written before any answer it grades was opened.

  A second, independent reviewer would still strengthen the results.
- **Formatters and starters differ.**
  - `mix format` and `rustfmt` lay code out more vertically than RuboCop; tokens reduce this effect.
  - Loco's starter ships user authentication, while Rails and Phoenix start closer to empty.
- **Speed was measured on one shared workstation:**
  - an 18-core Apple-silicon machine running Docker under OrbStack, with k6 in the same VM;
  - 15-second runs at 16 users.

  Unrelated workloads ran on the same machine, and identical images drifted by up to about 1.5× between sessions. The findings compare before and after only within a session, and claim nothing under 1.5×. Absolute numbers will differ on your hardware.
- **Agent tokens depend on prompt caching.** On short runs, one cache miss can add about 10k tokens, so the comprehension findings also report total input.
- **Security is a baseline, not a penetration test:** 13 black-box checks, one dependency scanner, and each stack's mainstream analyzer where it has one. Rust and Loco have no mainstream equivalent of Brakeman or Sobelow.
- **RealWorld is small.** It's a CRUD API with one background job, and no real-time features or media processing. The app grew by about a third over the seven steps, too little to show how the ratios behave in a codebase many times larger.
