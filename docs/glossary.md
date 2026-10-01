# Glossary

The few terms the result pages rely on, in plain language.

| Term | Meaning |
| --- | --- |
| **Stack** | The language, framework and supporting libraries an app is built with. |
| **Product contract** | The behavior every implementation must provide: the RealWorld API, drafts, background exports and live shared editing. It lives in [`spec/`](../spec/). |
| **Gates** | The required checks for a step or run, rerun independently after the agent stops. For a full build these are the API suites, WebSocket and browser tests, and 13 security checks, in development and against a fresh production image. Earlier steps of the eight-step study had fewer; production checks start at step 3. |
| **Reviewer probes** | Extra checks of edge cases the gates don't cover, such as huge IDs, malformed or stale edits, and bursts of bad logins. They are reported separately from the gates. |
| **Measured build** | The app exactly as one timed agent session left it, preserved with its results. |
| **Reviewed version** (also "reference") | A later repair or improvement of a measured build, published beside it with its own checks. Its work isn't counted as the agent's effort. |
| **One session / one-shot** | The agent builds the whole app in a single session, editing and testing as it goes. |
| **Eight steps / sequential** | The agent grows the app across eight prompts: build, drafts, packaging, tuning, hardening, polish, exports and live editing. |
| **Setup** (also "condition") | Everything that defines a run: model, prompt, stack guidance, starting scaffold, build protocol and checks. Compare numbers only within one setup. |
| **Owned code** | Backend source the agent added or changed relative to its starting scaffold, counted in model tokens (`o200k`) and nonblank, noncomment lines. Tests, docs, lockfiles and the shared client are excluded. |

Specialist pages also use **lane** (a stack's track through the lane runner), **cohort** (an entry in the [cohort index](../results/cohorts.json)) and **expert v2** (the prompt version used with stack-specific guidance). [How to read the results](cohorts.md) covers them.
