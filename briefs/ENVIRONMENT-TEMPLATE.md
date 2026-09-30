# <Stack> environment

A neutral environment file holds only facts the agent needs to operate the toolchain. It has the same sections for every stack and contains no design advice; advice belongs in the stack's [brief](README.md).

## Stack

Language, framework and major library versions, as pinned in the scaffold's lockfiles. State that the scaffold is product-free and must not be regenerated.

## Service

The port and bind address, and the environment variables the production app receives: `DATABASE_URL`, `SECRET_KEY_BASE` and `PORT`.

## Commands

Every harness command, with one line each on what it does and whether it needs a running server: database start and stop, development server start, logs and stop, one-shot commands, tests, formatter and linter, the production build, and the full development and production gates.

## Feedback loop

How fast a change can be checked: whether the development server reloads, and how long a compile or release build takes.

## Frozen inputs

Which files and folders are read-only, and that their hashes are checked before and after every harness action.
