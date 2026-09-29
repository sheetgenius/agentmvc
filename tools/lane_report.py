"""Render the Go/Python overview from published evidence only."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT/'results/lanes'
PHASES = ['1-build','2-add-drafts','3-package','4-tune','5-harden','6-polish',
          '7-add-background-job','8-live-editing']
NAMES = ['Base API','Drafts','Production','Performance','Security','Polish','Exports','Live editing']


def read(path):
    return json.loads(path.read_text()) if path.is_file() else None


def result(stack, phase):
    folder = ROOT/f'results/one-shot-v2-{stack}-expert/pilot-1' if phase=='one-shot' else OUT/stack/phase
    size, verification = read(folder/'size.json'), read(folder/'verification.json')
    if not size or not verification:
        return None
    return {'folder':folder,'size':size,'verification':verification,'run':read(folder/'run.json'),
            'snapshot':read(folder/'source-snapshot.json')}


def link(path, label):
    import os
    return f'[{label}]({os.path.relpath(path,OUT)})'


def cell(row):
    if not row: return 'Pending'
    size=row['size']
    status='pass' if row['verification']['passed'] else '**failed**'
    source=ROOT/row['snapshot']['path']
    return f'{link(source,format(size["owned_tokens"],","))} tokens · {link(row["folder"]/"verification.json",status)}'


def span(values, decimals=0):
    if not values or any(value is None for value in values):
        return 'Pending'
    low, high = min(values), max(values)
    fmt = f',.{decimals}f'
    return format(low, fmt) if low == high else f'{format(low, fmt)}–{format(high, fmt)}'


def review_cell(folder):
    proof = read(folder/'reviewer-parity/results.json')
    share = read(folder/'reviewer-parity/share-boundary.json')
    if not proof:
        return 'Pending'
    common = proof.get('http_probe', {}).get('summary', {})
    favorite = proof.get('source_driven_favorites', {}).get('summary', {})
    status = link(folder/'reviewer-parity/results.json',
                  f'{common.get("contract_passed",0)}/21 contract · {common.get("quality_passed",0)}/3 quality · favorites {favorite.get("passed",0)}/48')
    if share:
        summary = share.get('probe', {}).get('summary', {})
        status += ' · '+link(folder/'reviewer-parity/share-boundary.json',
                             f'shared {summary.get("contract_passed",0)}/3 + {summary.get("quality_diagnostic_passed",0)}/1')
    else:
        status += ' · shared pending'
    if not proof.get('passed') or not share or not share.get('passed'):
        status += ' · **not full reviewer parity**'
    return status


def reference_tables(data):
    rows = []
    for stack in ('go', 'python'):
        for phase in ('8-live-editing', 'one-shot'):
            parent = data[stack][phase]
            if not parent:
                continue
            folder = parent['folder']/'reference-1'
            size, verification, snapshot = (read(folder/name) for name in
                                            ('size.json', 'verification.json', 'source-snapshot.json'))
            if size and verification and verification.get('passed'):
                label = f'{stack.title()} · '+('eight-step reference' if phase!='one-shot' else 'one-shot reference')
                rows.append(f'| {link(ROOT/snapshot["path"],label)} | {size["owned_tokens"]:,} tokens | {review_cell(folder)} |')
    if not rows:
        return []
    return ['', '## Reviewed references', '',
            'These separately labeled repairs preserve the measured originals. Their added tests, source size and independent checks are recorded; their editing effort is not pooled with one-shot effort.', '',
            '| Reference source | Owned backend | Reviewer checks |',
            '| --- | ---: | --- |', *rows]


def final_tables(data):
    finals = [(stack, phase, data[stack][phase]) for stack in ('go','python')
              for phase in ('8-live-editing','one-shot') if data[stack][phase]]
    if not finals:
        return []
    lines = ['', '## Full-product builds', '',
             'Each row describes one exact source snapshot. The eight-step effort is the sum of its eight coding sessions; the one-shot starts from a fresh scaffold. Setup, independent checks and later reviewer work are outside these coding totals.', '',
             '| Application | Owned / whole backend tokens | Coding minutes | Uncached + output tokens | Reviewer HTTP parity |',
             '| --- | ---: | ---: | ---: | --- |']
    for stack, phase, row in finals:
        label = f'{stack.title()} · '+('eight steps' if phase!='one-shot' else 'expert one-shot')
        source = link(ROOT/row['snapshot']['path'], label)
        sessions = [data[stack][p] for p in PHASES] if phase!='one-shot' else [row]
        runs = [item['run'] for item in sessions if item and item['run']]
        minutes = f'{sum(run["seconds"] for run in runs)/60:.1f}' if len(runs)==len(sessions) else 'Pending'
        effort = f'{sum(run["tokens"]["uncached_plus_output"] for run in runs):,}' if len(runs)==len(sessions) else 'Pending'
        parity = review_cell(row['folder'])
        size = row['size']
        lines.append(f'| {source} | {size["owned_tokens"]:,} / {size["tokens"]:,} | {minutes} | {effort} | {parity} |')
    runtime = OUT/'runtime/measured'
    if not (runtime/'summary.json').exists():
        return lines
    lines += ['', '### Repeated production runtime', '',
              'Two rounds; 16 users; 3-second warmup and 15-second samples; app and database each limited to 2 CPUs and 1 GiB. Ranges show both rounds, not a selected peak. The linked evidence includes all nine HTTP workloads and the 10/100/500-subscriber socket measurements.', '',
              '| Application | List req/s | Article req/s | SQL / list | Image MB | Cold start seconds | Runtime checks |',
              '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for stack, phase, row in finals:
        sid = row['run']['id']
        folder = runtime/sid
        samples = [read(folder/f'round{n}/http/results.json') for n in (1,2)]
        if not all(samples): continue
        sockets = [read(folder/f'round{n}/socket/results.json') for n in (1,2)]
        checks = 'pass' if all(sample.get('passed') for sample in samples+sockets if sample) and all(sockets) else '**failed or incomplete**'
        label = f'{stack.title()} · '+('eight steps' if phase!='one-shot' else 'expert one-shot')
        metric = lambda scenario, key: [sample.get('scenarios',{}).get(scenario,{}).get(key) for sample in samples]
        lines.append(f'| {link(folder,label)} | {span(metric("list_anonymous","rps"))} | {span(metric("article","rps"))} | {span(metric("list_anonymous","sql_statements_per_request"),2)} | {span([s.get("image_mb") for s in samples],1)} | {span([s.get("cold_start_seconds") for s in samples],2)} | {checks} |')
    lines += ['', '[Runtime manifest and all workloads](runtime/measured/summary.json). Runtime success does not imply that every supplemental reviewer check passed; see the parity column above.']
    return lines


def main():
    data={stack:{phase:result(stack,phase) for phase in [*PHASES,'one-shot']} for stack in ('go','python')}
    total=sum(bool(row and row['verification']['passed']) for rows in data.values() for row in rows.values())
    lines=['# Go and Python','',
           'Two new paths through the same Conduit product: build it in eight successive sessions, then build it again in one fresh expert session. The goal is readable, domain-rich code that uses each stack well, with correctness and production performance measured alongside size.','',
           f'**Progress: {total}/18 coding sessions independently verified.** '+('The full runs are still in progress; intermediate sizes below are not final-product comparisons.' if total<18 else 'Final snapshots, checks and effort records are linked below.'),'',
           '## Start with the code','',
           '| Lane | Latest verified sequential source | Owned backend | Expert one-shot |',
           '| --- | --- | ---: | --- |']
    for stack,label in [('go','Go'),('python','Python')]:
        complete=[(phase,row) for phase,row in data[stack].items() if phase!='one-shot' and row and row['verification']['passed']]
        if complete:
            phase,row=complete[-1]; size=row['size']
            source=link(ROOT/row['snapshot']['path'],phase)
            count=f'{size["owned_tokens"]:,} tokens · {size["owned_lines"]:,} lines'
        else: source=count='Pending'
        lines.append(f'| {label} | {source} | {count} | {cell(data[stack]["one-shot"])} |')
    lines += reference_tables(data)
    lines += ['',
              '**Python:** Django + Django Ninja, with Django associations, migrations and password services; Channels for raw WebSockets; Procrastinate for PostgreSQL jobs. [Why this stack](../../stacks/python/STACK.md).','',
              '**Go:** the prepared expert toolkit is Huma + chi, Bun, Goose and River. The sequential agent chose **chi + Bun** and removed Huma in step 1; that is a recorded implementation choice. The independent expert one-shot explicitly asks for Huma typed operations. [Why this toolkit](../../stacks/go/SELECTION.md).','',
              'The one-shots start from product-free scaffolds and use the [same expert-v2 prompt](../../one-shot-v2-expert/PROMPT.md) as the recent Rails, Phoenix and TypeScript builds. The sequential lanes use the original eight prompt files. Stack guidance and preparation are disclosed separately; these are distinct conditions, not pooled trials.','',
              '## The eight steps','',
              'Every source link is an immutable checkpoint. “Pass” means the coordinator reran the applicable frozen checks; production verification begins at step 3.','',
              '| Step | Go | Python |','| --- | --- | --- |']
    for phase,name in zip(PHASES,NAMES):
        lines.append(f'| {link(ROOT/"steps"/(phase+".md"),phase.split("-")[0]+" · "+name)} | {cell(data["go"][phase])} | {cell(data["python"][phase])} |')
    lines += ['',
              'Backend size excludes tests, docs, dependencies, lockfiles and the fixed client. Owned size is the change from the supplied scaffold. Each checkpoint also records whole-app size and tests/docs separately.']
    lines += final_tables(data)
    lines += ['',
              '## Try a completed app','',
              'From the repository root, use Docker, Node.js 22.12+ (or 20.19+ on the 20.x line), npm, curl and OpenSSL. These commands work from a fresh clone once the corresponding source checkpoint is published. The script installs client dependencies, builds the backend, creates a fresh database, and prints an editor link to open in several tabs. Ctrl-C cleans up the demo.','',
              '```sh','tools/lane_demo.sh go','tools/lane_demo.sh python',
              '# Or use the independently built expert app:','tools/lane_demo.sh python one-shot','```','',
              'Set `DEMO_BACKEND_PORT` and `DEMO_FRONTEND_PORT` to override the localhost ports.','',
              '## Evidence and limits','',
              '- [Go preflight](go/preflight.json) and [Python preflight](python/preflight.json): migrations, durable jobs, sockets, reload, production packaging and image identities.',
              '- Each checkpoint directory contains its measured agent report, effort/failure counts, source inventory, actual isolation probe and independent verification.',
              '- [Comprehension](comprehension/): fresh read-only agents answer the original twelve questions after steps 1 and 6. Scores require source-supported grading.',
              '- Reviewer parity adds the same 21 contract and 3 quality HTTP probes used for the current references. Original failures remain visible; later repairs must be separate snapshots.',
              '- A [source review](REVIEW-NOTES.md) prompted a separate 48-case favorite-count diagnostic, applied equally to every final Go/Python app. It does not change the frozen coding requirements.',
              '- The later [expert review](EXPERT-REVIEW.md) adds three shared-edit contract cases and one envelope-quality case, recorded separately for each final app. References must also pass these checks.',
              '- Tuning feedback uses short 3-second samples. Final HTTP measurements use all nine workloads, 16 users and two 15-second rounds, with app and database each limited to 2 CPUs and 1 GiB. Socket measurements cover 10, 100 and 500 subscribers.',
              '- Full transcripts and compressed raw streams belong in external release assets, with checked hashes and links recorded here when published. They are not committed to Git.','',
              '[Detailed method and reproduction commands](METHODOLOGY.md) · [Main comparison](../../README.md) · [Contributing](../../CONTRIBUTING.md)','']
    (OUT/'README.md').write_text('\n'.join(lines))
    print(f'Overview updated: {total}/18 independently verified')


if __name__=='__main__':
    main()
