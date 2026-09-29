"""Run the frozen lane runner with a versioned reviewer publication adapter.

JSON escape sequences are syntax, not transcript text: ``\\n@api.get`` must
not be interpreted as the email ``n@api.get``. Validate every decoded string
and object key, plus the rendered Markdown. All original scrub rules remain.
This adapter changes no coding prompt, workspace fixture, or measured source.
Usage is identical to tools/lane_run.py.
"""
import json
from pathlib import Path

import lane_run
import lane_launch
import lane_review
import scrub


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from strings(item)


def scrub_events(events_path, workdir, out_stem, deny=(), keep=(), header=None, maps=()):
    cleaner = scrub.Scrubber(workdir, deny, keep, maps)
    with open(events_path) as source:
        events = [cleaner.event(json.loads(line)) for line in source if line.strip()]
    readable = scrub.render(events, cleaner.value(header or {}))
    leaks = {label for value in [*strings(events), readable] for label in cleaner.leaks(value)}
    if leaks:
        raise SystemExit(f'{events_path}: decoded transcript still contains sensitive material: {sorted(leaks)}')
    raw = ''.join(json.dumps(event, ensure_ascii=False) + '\n' for event in events)
    # Round-trip verification also checks the exact bytes that will be published.
    decoded = [json.loads(line) for line in raw.splitlines()]
    if decoded != events or any(cleaner.leaks(value) for value in strings(decoded)):
        raise SystemExit('Serialized transcript failed decoded validation')
    stem = Path(out_stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    stem.with_suffix('.jsonl').write_text(raw)
    stem.with_suffix('.md').write_text(readable)
    return events


original_publish = lane_run.publish


def publish(path):
    original_publish(path)
    session = lane_run.load(path)
    lane_run.save(Path(session['result'])/'publication-adapter.json', {
        'adapter': 'tools/lane_continue.py',
        'sha256': lane_run.digest(Path(__file__)),
        'validation': 'All decoded JSON strings and keys plus rendered Markdown; unchanged scrub patterns',
        'reason': 'Avoid interpreting JSON newline escapes followed by decorators as email addresses',
        'original_runner_sha256': lane_run.digest(Path(lane_run.__file__)),
        'coding_inputs_changed': False,
    })
    launch_record = Path(session['logs']) / 'launch-adapter.json'
    if launch_record.exists():
        lane_run.save(Path(session['result']) / 'launch-adapter.json', lane_run.load(launch_record))


def install():
    scrub.scrub_file = scrub_events
    lane_run.publish = publish
    lane_run.independently_check = lane_review.independently_check
    lane_run.launch = lane_launch.launch


if __name__ == '__main__':
    install()
    raise SystemExit(lane_run.main())
