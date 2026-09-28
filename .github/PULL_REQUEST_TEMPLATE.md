## What changed

<!-- The question, and the files changed. -->

## Runs

<!-- Ledger rows added, the prompt or brief they used, and an archive link for each run's transcript and logs. -->

## Verification

<!-- Commands you ran and their results, including failed attempts that explain the outcome. -->

## Checklist

- [ ] Frozen inputs are unchanged, or the change is labeled and re-frozen with `tools/one_shot.py freeze` or `tools/ihp_candidate.py freeze`.
- [ ] A prompt or brief comparison has at least three runs per stack on one model, with every run in the ledger, failures included.
- [ ] Prompts and briefs contain instructions, not application code.
- [ ] No transcripts, agent reports, logs or raw benchmark data are committed, and the archives were checked for secrets and personal paths.
- [ ] A new reference app was copied with `tools/reference.py`, and its size matches its ledger row.
