# IHP proof-enabled candidate

This is a separately frozen fourth-stack track. It reuses the exact semantic-density one-shot prompt, spec, client, and acceptance harness from `one-shot/fixture-manifest.json`. Its only stack-specific inputs are the authentic IHP boilerplate with pinned Nix dependencies, a compiled LiquidHaskell smoke module, and `ENVIRONMENT.md`.

The original Rails, Phoenix and Loco fixture and eight-step histories are unchanged. Each measured run has its own Nix store, copied from a product-free prewarmed base so a later agent cannot inspect an earlier app through build artifacts. A measured IHP run starts only after toolchain, refinement, real migration, production image and isolation preflights pass.
