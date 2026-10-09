# Practitioner briefs

A practitioner brief is short, stack-specific guidance from someone who knows the stack well. The agent receives it alongside the shared, stack-neutral prompt. Briefs are how a stack's community can show how they would prompt a model to build good software in their stack, and once a stack's brief is reviewed, [experiment v3](../docs/experiment-v3.md) runs it as its own condition beside that stack's build without one.

## Rules

- **Six sections, in order,** as in [TEMPLATE.md](TEMPLATE.md): rule ownership, framework features to use, bounded queries, boundaries, production, and known traps.
- **At most 500 words** across those six sections. The title and the closing "About this brief" section don't count.
- **Guidance only.** Commands, ports, versions and other toolchain facts belong in the stack's neutral environment file, which has the same sections for every stack; see [ENVIRONMENT-TEMPLATE.md](ENVIRONMENT-TEMPLATE.md).
- **Instructions, not solutions.** No application code for this product and no fenced code blocks. Naming APIs, libraries, options and commands is fine.
- **Stack knowledge, not test cases.** Say how the stack behaves and what to do about it, such as a library default that drops unknown fields. Don't restate a reviewer probe's case or an earlier build's failing input. Brief conditions are also scored on held-out checks that brief authors don't see.
- **Verified.** Every API, option or command a brief names must exist in the pinned versions. Check installed source or the official docs, and say which versions you checked.
- **Practitioner-written and reviewed.** Someone who works in the stack writes it, and a second practitioner reviews it.
- **Frozen before use.** A brief is hashed with the other inputs before any measured run. Changing it afterwards creates a new brief version and a new condition.

Check a brief before you submit it:

```bash
python3 tools/brief_check.py briefs/rails.md
```

## Why 500 words

- The Rails expert run had about 500 words of implementation notes, and its app came out with named rule owners, preloaded lists and database constraints.
- The IHP expert brief ran about 1,300 words, longer than the 708-word shared prompt, and mixed advice with toolchain workarounds. A brief longer than the prompt becomes the experiment.
- The cap forces every line to change a decision the model would otherwise get wrong. Token cost is not the reason: 500 words is a rounding error in what an agent reads during a run.

## Submit a brief

1. Start from [`seeds/<stack>.md`](seeds/) if one exists, where `<stack>` is the stack's directory under `stacks/`, such as `rails`, or `typescript` for AdonisJS. Seeds were distilled from the expert environments and the reviews of earlier runs, and no practitioner has reviewed them yet.
2. Write your brief as `briefs/<stack>.md`, and fill in the "About this brief" section: authors, reviewer, and the pinned versions you checked.
3. Run `tools/brief_check.py` on it.
4. Open a pull request with the brief, the checker output, and your prediction of what it will change in the agent's app.

Maintainers run submitted briefs in the A/B design, and the results appear per stack. Nobody's brief is scored against another stack's.
