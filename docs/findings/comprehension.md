# Comprehension: how well does a fresh agent understand the code?

After steps 1 and 6, a new agent with a read-only sandbox answered [12 questions](../../comprehension/questions.md) about each implementation's domain rules. It had to cite the file and function behind each answer. It saw only the application source, the same files counted as the whole app. The questions cover:
- slugs;
- duplicate registration;
- the feed;
- favorite counts;
- comment ownership;
- empty profile fields;
- tag storage;
- pagination;
- tokens;
- the author-only rule;
- null tag lists;
- password storage.

## Hypotheses, written before the first run

- **H1:** accuracy is similar across stacks, because the apps are small.
- **H2:** reading cost scales with code size, roughly following the size ratios.
- **H3:** wall-clock time follows reading cost.

## Results

| After step 1 | Rails | Phoenix | Loco |
| --- | ---: | ---: | ---: |
| Accuracy (of 12) | 12 | 11.5 | 11.5 |
| Agent tokens (uncached input + output) | 10,233 | 18,834 (1.84×) | 18,638 (1.82×) |
| Total input processed, cached or not | 86,881 | 104,751 (1.21×) | 103,905 (1.20×) |
| Wall-clock time | 54 s | 82 s | 197 s |
| Size of the code, tokens | 3,514 | 6,196 (1.76×) | 8,804 (2.51×) |

| After step 6 | Rails | Phoenix | Loco |
| --- | ---: | ---: | ---: |
| Accuracy (of 12) | 11.5 | 12 | 11.5 |
| Agent tokens (uncached input + output) | 22,045 | 20,555 (0.93×) | 25,218 (1.14×) |
| Total input processed, cached or not | 90,819 | 110,489 (1.22×) | 159,009 (1.75×) |
| Wall-clock time | 80 s | 88 s | 87 s |
| Size of the code, tokens | 4,319 | 8,138 (1.88×) | 11,373 (2.63×) |

The answer keys, grades and every answer are in [`comprehension/`](../../comprehension/).

## Reading

- **H1 holds.** Every agent scored 11.5 or 12 in both runs.
- **No miss was about syntax.** Each came from behavior the app never states, or states somewhere else:
  - **Phoenix, after step 1:** the token lifetime is Joken's 2-hour default, set nowhere in the app. The reader found it after step 6.
  - **Loco, both times:** the password hash is Argon2, inside `loco_rs::hash`, and no reader of the app can see it.
  - **Rails, after step 6:** the reader saw `favorites.size` in the view but missed that lists count preloaded favorites in memory. The preload is in the controller, one file away.
- **H2 holds only weakly, and the pre-registered metric turned out to be noisy.**
  - After step 1, Rails was cheapest by a clear margin on agent tokens.
  - After step 6, Rails' run cost more than double, for code that grew 23%. Its total input rose only 5%, but the cached share of that input fell from 90% to 79%. The likely cause is a prompt-cache miss on the fixed instructions: one run moved by 11.8k tokens, more than twice the size of the whole Rails app.
  - On total input processed, which doesn't depend on caching, Rails is cheapest both times. Phoenix sits at 1.21–1.22×. Loco went from 1.20× to 1.75× on its larger step-6 code.
  - Those gaps are smaller than the code-size gaps. Readers don't read everything.
- **H3 doesn't hold as a straight line.** After step 1, Loco took 3.6× Rails' time for about Phoenix's tokens. After step 6, all three took 80–88 seconds.

## Process note

The first launch after step 1 was stopped: a counting bug had left Rails' Jbuilder views out of its reading copy. All three runs were rerun on corrected copies, and the numbers above come from the reruns; see the [research log](../research-log.md).
