## What changed

<!-- The question, the condition or reference it belongs to, and the files changed. -->

## Evidence

<!-- Prompt and fixture hashes, model and CLI, source revision, gates, and any measurements. Link release downloads for transcripts and raw data. -->

## Checklist

- [ ] Measured runs and unscored references are labeled separately.
- [ ] Frozen inputs are unchanged, or the change creates a newly labeled, re-frozen condition.
- [ ] A comparison states its condition and compares only within it.
- [ ] No transcripts, agent reports, chat exports, credentials or local workdirs are added to Git.
- [ ] A new practitioner brief passes `tools/brief_check.py`.
- [ ] `python3 tools/cohort_index.py --check` passes if run records changed.
