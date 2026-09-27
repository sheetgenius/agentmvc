# Size: how much code does the same app take?

After every step, [`tools/measure.py`](../../tools/measure.py) counts each implementation in two ways (see [methodology](../methodology.md#code-size)):
- the **whole app**, which is what an agent reads to learn the codebase;
- **owned code**, which is what the agent wrote on top of its generator's output.

![Code size of each stack after every step](../../results/charts/growth.svg)

| After step | Rails, tokens | Phoenix | Loco | Rails, lines of code | Phoenix | Loco |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1. Build | 3,514 | 6,196 (1.76×) | 8,804 (2.51×) | 426 | 704 (1.65×) | 1,335 (3.13×) |
| 2. Add drafts | 3,974 | 7,164 (1.80×) | 10,202 (2.57×) | 471 | 806 (1.71×) | 1,539 (3.27×) |
| 3. Package | 3,974 | 7,197 (1.81×) | 10,194 (2.57×) | 471 | 813 (1.73×) | 1,539 (3.27×) |
| 4. Tune | 4,029 | 7,764 (1.93×) | 11,112 (2.76×) | 476 | 885 (1.86×) | 1,678 (3.53×) |
| 5. Harden | 4,297 | 8,110 (1.89×) | 11,339 (2.64×) | 495 | 910 (1.84×) | 1,715 (3.46×) |
| 6. Polish | 4,319 | 8,138 (1.88×) | 11,373 (2.63×) | 498 | 917 (1.84×) | 1,704 (3.42×) |
| 7. Add a background job | 4,847 | 9,062 (1.87×) | 12,884 (2.66×) | 579 | 1,045 (1.80×) | 1,928 (3.33×) |

Owned code after step 7 is 4,447 tokens for Rails, 8,551 for Phoenix (1.92×) and 12,222 for Loco (2.75×). Every step's figures are in [`results/sizes.json`](../../results/sizes.json).

## Reading

**The gap is set at step 1, and it holds.**
- Phoenix starts at 1.76× Rails and Loco at 2.51×. After six more steps, they're at 1.87× and 2.66×.
- No step closed the gap, not even step 6, where each agent could rework its code however it liked. That pass changed each codebase by less than 1%; see [polish](polish.md).

![Each stack's size relative to Rails after every step](../../results/charts/ratio.svg)

**Growth looks proportional, not accelerating, over this range.**
- **Overall growth:** from step 1 to step 7, Rails grew 38%. Phoenix grew 46%, and so did Loco.
- **Where the ratio moved:** mostly at step 4. There, Rails fixed its slow queries with 143 tokens, while Phoenix needed 756 and Loco 1,318 for the equivalent batching code. At step 5, Loco's hardening was the cheapest of the three, and its ratio fell back by 0.12. Every other step moved it by 0.06 or less.
- **What this can't show:** the app only grew by about a third. That's too narrow to tell proportional growth from mildly superlinear growth in a codebase many times this size.

**Lines overstate Rust's reading cost.**
- Loco has 3.33× Rails' lines of code, but 2.66× its tokens. `rustfmt` puts more on separate lines: Loco averages 6.7 tokens per line, against 8.4 for Rails and 8.7 for Phoenix.
- For an agent's context window, tokens are the unit that matters.

**Where the extra code goes.** In the code, the same rule tends to take more pieces outside Rails.
- **Phoenix** splits a feature across a context function, a schema changeset, and a presenter that shapes the JSON.
- **Loco** adds typed request and response structs, an API error type, explicit SeaORM queries and hand-written views. Its generated entity files are excluded from these counts.
- **Rails** gets most of this from conventions: model validations and associations, `before_action` filters, and Jbuilder partials.

**Starters differ.** Loco's starter ships user authentication, while Rails and Phoenix start closer to empty. Owned code ignores starter code the agent never changed; the whole-app count includes it.
