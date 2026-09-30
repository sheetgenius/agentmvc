# <Stack> brief

## Rule ownership

Where each kind of product rule lives in this framework: visibility and edit authority, lifecycle and revision transitions, database invariants, background jobs, and socket delivery. Say where one rule shared by two entrances should live.

## Use what the framework provides

Built-in features and maintained libraries to use instead of hand-rolling: password hashing, tokens, rate limiting, locking, jobs and validation.

## Bounded queries

How to keep lists and feeds bounded with this stack's data layer: paging in SQL, preloading related rows, and counts that agree with the returned page.

## Boundaries

How to decode and validate requests, reject unexpected fields where the contract requires it, and shape responses in one place.

## Production

The idiomatic production build and process model, including how the app uses more than one CPU within the contract.

## Known traps

Version-specific traps in the pinned toolchain, each with what to do instead.

## About this brief

- Authors:
- Reviewer:
- Pinned versions checked:
