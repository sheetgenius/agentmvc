# The steps

Every stack goes through the same seven steps, in order. Each step is one agent run from the prompt here, byte-identical for every stack. Each run's `runs.json` record holds the prompt's sha256.

Every prompt opens with the same goal: code that reads almost like a description of the domain, reaching Rails-like simplicity through each stack's own idioms. Each prompt then states the task, the hard boundaries, when to stop, and the headings of the final report.

| Step | Starts from | Also receives |
| --- | --- | --- |
| [1-build](1-build.md) | The spec | `ENVIRONMENT.md` |
| [2-add-drafts](2-add-drafts.md) | Step 1 | The drafts feature spec and tests |
| [3-package](3-package.md) | Step 2 | Nothing new |
| [4-tune](4-tune.md) | Step 3 | The benchmark, and step 3's results |
| [5-harden](5-harden.md) | Step 4 | The 13 security checks, and step 4's scan |
| [6-polish](6-polish.md) | Step 5 | Nothing new |
| [7-add-background-job](7-add-background-job.md) | Step 6 | The exports feature spec and test |

[`comprehension.md`](comprehension.md) is the prompt for the read-only agent that answers questions about the code after steps 1 and 6.

The step-1 prompt also covers refining an existing implementation. In step 1 the directory starts empty, so that branch never applies.
