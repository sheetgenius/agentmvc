# Polish: where does each stack land with free rein?

In step 6, each agent could rework its whole codebase the way the language's and framework's best practitioners would, and the way it would most want to read it cold. It could make up to three passes, keeping both checks green.

## Hypotheses, written before the step ran

- **H1:** polishing shrinks Phoenix and Loco more than Rails, because Rails has less to remove. The gap narrows but doesn't close.
- **H2:** reading cost falls for every stack.

## Results

| | Rails | Phoenix | Loco |
| --- | ---: | ---: | ---: |
| Passes | 2 (the second found nothing to change) | 3 (the limit) | 3 (the limit) |
| Code changed, tokens | 175 | 486 (2.78×) | 655 (3.74×) |
| Whole app, before → after | 4,297 → 4,319 (+0.5%) | 8,110 → 8,138 (+0.3%) | 11,339 → 11,373 (+0.3%) |
| Owned code, before → after | 3,898 → 3,920 (+0.6%) | 7,609 → 7,637 (+0.4%) | 10,694 → 10,745 (+0.5%) |
| Agent tokens, wall-clock time | 79k, 6.1 min | 89k, 6.8 min | 129k, 8.9 min |

What each agent did:
- **Rails:** moved locked revision updates and tag replacement from the controller into `Article`, beside publishing.
- **Phoenix:**
  - moved the ownership checks from the controllers into the `Content` context;
  - put the identity and password rules in one place in the user schema;
  - simplified comment creation and listing.
- **Loco:**
  - moved the author and favorited filters into SeaORM queries;
  - put counting and pagination in one model method;
  - moved publishing onto the article model, with one locked ownership lookup for update and publish.

## Reading

- **H1 doesn't hold: no stack got smaller.**
  - Every codebase changed size by less than 1%. Each agent moved rules to where its stack's conventions put them, and none traded clarity for fewer tokens.
  - The ratios stayed where they were: after the pass, Phoenix is 1.88× Rails and Loco 2.63×.
- **The size gap is structural.** It comes from what each stack asks you to write down, not from how carefully the agent wrote it.
- **H2 can't be assessed.** Accuracy stayed at 11.5–12 of 12, but the reading-cost metric proved too noisy at this size; see [comprehension](comprehension.md).
- **The polished images still pass.** They clear all 13 security checks, and show no speed regression; see [speed](speed.md#after-step-6-a-regression-check).
