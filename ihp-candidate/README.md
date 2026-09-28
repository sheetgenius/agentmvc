# IHP track

IHP runs on its own frozen track because its toolchain runs through Nix. It reuses the baseline prompt, spec, client and acceptance harness hashed in `one-shot/fixture-manifest.json`. Its only stack-specific inputs are the IHP boilerplate with pinned Nix dependencies in `stacks/ihp/scaffold/`, a compiled LiquidHaskell smoke module, this folder's `ENVIRONMENT.md`, and `ihp.sh`, the agent's wrapper for the Nix toolchain.

Each measured run has its own Nix store, copied from a product-free prewarmed base, so a later agent can't inspect an earlier app through build artifacts. Start a measured run only after the toolchain, refinement, migration, production-image and isolation preflights pass. [docs/running.md](../docs/running.md) has the commands.
