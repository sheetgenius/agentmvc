# Comprehension

After steps 1 and 6, a fresh agent with a read-only sandbox answers [12 questions](questions.md) about each implementation's domain rules, citing the file and function for each answer. It sees only the application source: the same files `tools/measure.py` counts as the whole app.

- `answer-key-after-1-build.md`, `answer-key-after-6-polish.md`: each written by reading the code before any answer it grades was opened.
- `grades.json`: 1 point for the right behavior in the right place, 0.5 for the right behavior with the place wrong or missing, and 0 otherwise.
- The readers' answers and sessions are agent messages, so they left the working tree. [`results/message-archive.json`](../results/message-archive.json) lists each one and the commit that holds it.
