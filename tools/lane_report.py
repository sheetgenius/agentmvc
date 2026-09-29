"""Render the Go/Python overview from published evidence only."""
import json
import re
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
    low_text, high_text = format(low, fmt), format(high, fmt)
    return low_text if low_text == high_text else f'{low_text}–{high_text}'


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


def references(data, *, latest=False):
    rows = []
    for stack in ('go', 'python'):
        for phase in ('8-live-editing', 'one-shot'):
            parent = data[stack][phase]
            if not parent:
                continue
            candidates = []
            for folder in parent['folder'].glob('reference-*'):
                match = re.fullmatch(r'reference-(\d+)', folder.name)
                if not match:
                    continue
                size, verification, snapshot, reference = (read(folder/name) for name in
                    ('size.json', 'verification.json', 'source-snapshot.json', 'reference.json'))
                if (size and verification and verification.get('passed') and snapshot and reference
                        and verification.get('source_sha256') == snapshot['sha256']):
                    label = f'{stack.title()} · '+('eight-step' if phase!='one-shot' else 'one-shot')
                    candidates.append({'folder':folder, 'size':size, 'snapshot':snapshot,
                                       'session':reference['session'], 'revision':int(match[1]),
                                       'label':f'{label} reference {int(match[1])}'})
            candidates.sort(key=lambda row: row['revision'])
            rows.extend(candidates[-1:] if latest else candidates)
    return rows


def reference_tables(data):
    references_now = references(data, latest=True)
    rows = [f'| {link(ROOT/row["snapshot"]["path"],row["label"])} | {row["size"]["owned_tokens"]:,} tokens | {review_cell(row["folder"])} |'
            for row in references_now]
    if not rows:
        return []
    return ['', '## Reviewed references', '',
            'Each row selects the latest independently verified reference for that application. These repairs preserve earlier attempts and measured originals; their editing effort is not pooled with coding effort. Reviewer checks remain separately visible.', '',
            '| Reference source | Owned backend | Reviewer checks |',
            '| --- | ---: | --- |', *rows,
            *runtime_table('reference', references(data), 'Repeated reference runtime')]


def runtime_table(condition, sources, heading):
    base = OUT/'runtime'/condition
    summary = read(base/'summary.json')
    if not summary:
        return []
    known = {row['session']:row for row in sources}
    lines = ['', f'### {heading}', '',
             'Two rounds; 16 concurrent users; 3-second warmup and 15-second samples; app and database each limited to 2 CPUs and 1 GiB. The HTTP fixture has 50 users and 500 articles. Ranges show both rounds. Source and image hashes must match the runtime manifest before metrics are shown; all nine HTTP workloads and 10/100/500-subscriber socket results are linked.', '',
             '| Application | List req/s | Article req/s | SQL / list | Image MB | Cold start seconds | Runtime checks |',
             '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for sid, identity in summary.get('applications',{}).items():
        row = known.get(sid)
        folder = base/sid
        samples = [read(folder/f'round{n}/http/results.json') for n in (1,2)]
        sockets = [read(folder/f'round{n}/socket/results.json') for n in (1,2)]
        records = {(entry.get('round'),entry.get('kind')) for entry in summary.get('records',[])
                   if entry.get('session') == sid}
        mismatch = (not row or identity.get('source_sha256') != row['snapshot']['sha256'] or
                    any(sample and any(sample.get(key) != identity.get(key)
                        for key in ('source_sha256','image_sha256')) for sample in samples+sockets))
        complete = all(samples+sockets) and records == {(n,kind) for n in (1,2) for kind in ('http','socket')}
        checks = ('**identity mismatch**' if mismatch else 'pass' if complete and
                  all(sample.get('passed') for sample in samples+sockets) else '**failed or incomplete**')
        label = row['label'] if row else sid
        metric = lambda scenario,key: [sample.get('scenarios',{}).get(scenario,{}).get(key) if sample else None for sample in samples]
        values = ['—']*5 if mismatch else [span(metric('list_anonymous','rps')),span(metric('article','rps')),
            span(metric('list_anonymous','sql_statements_per_request'),2),
            span([s.get('image_mb') if s else None for s in samples],1),
            span([s.get('cold_start_seconds') if s else None for s in samples],2)]
        lines.append(f'| {link(folder,label)} | '+ ' | '.join(values)+f' | {checks} |')
    lines += ['', link(base/'summary.json','Runtime manifest and all workloads')+'. '+
              ('Runtime success does not imply supplemental reviewer parity; see the parity column above.'
               if condition=='measured' else 'Each runtime label names the exact reference version measured, which may precede a newer verified reference.')]
    return lines


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
    sources = [{**row,'session':row['run']['id'],
                'label':f'{stack.title()} · '+('eight steps' if phase!='one-shot' else 'expert one-shot')}
               for stack,phase,row in finals if row['run']]
    lines += runtime_table('measured', sources, 'Repeated production runtime')
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
              '**Go:** the sequential implementation uses **chi + Bun** and removed Huma in step 1. The expert one-shot uses Huma for only `/api/tags` and `/health`; most product handlers use chi directly, alongside Bun, Goose and River. These are the observed implementations of the supplied Huma/chi guidance. [Why this toolkit](../../stacks/go/SELECTION.md).','',
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
              '# Or use the independently built expert app:','tools/lane_demo.sh python one-shot',
              '# Reviewed repairs require passed independent and reviewer checks:',
              'tools/lane_demo.sh python eight-reference','tools/lane_demo.sh python one-shot-reference','```','',
              'Set `DEMO_BACKEND_PORT` and `DEMO_FRONTEND_PORT` to override the localhost ports.','',
              '## Evidence and limits','',
              '- [Go preflight](go/preflight.json) and [Python preflight](python/preflight.json): migrations, durable jobs, sockets, reload, production packaging and image identities.',
              '- Each checkpoint directory contains its measured agent report, effort/failure counts, source inventory, actual isolation probe and independent verification.',
              '- [Comprehension](comprehension/): fresh read-only agents answer the original twelve questions after steps 1 and 6. Scores require source-supported grading.',
              '- Reviewer parity adds the same 21 contract and 3 quality HTTP probes used for the current references. Original failures remain visible; later repairs must be separate snapshots.',
              '- A [source review](REVIEW-NOTES.md) prompted a separate 48-case favorite-count diagnostic, applied equally to every final Go/Python app. It does not change the frozen coding requirements.',
              '- The later [expert review](EXPERT-REVIEW.md) adds three shared-edit contract cases and one envelope-quality case, recorded separately for each final app. References must also pass these checks.',
              '- Tuning feedback uses short 3-second samples. Final HTTP measurements use all nine workloads, 16 users and two 15-second rounds, with app and database each limited to 2 CPUs and 1 GiB. Socket measurements cover 10, 100 and 500 subscribers.',
              '- [Scrubbed transcripts and raw measurements](https://github.com/sheetgenius/agentmvc/releases/tag/go-python-lanes-v1) are published as external release assets. The [artifact manifest](artifacts-v1.json) records per-file hashes, source provenance and download checksums. Full transcripts and raw streams are not committed to Git.','',
              '[Detailed method and reproduction commands](METHODOLOGY.md) · [Main comparison](../../README.md) · [Contributing](../../CONTRIBUTING.md)','']
    (OUT/'README.md').write_text('\n'.join(lines))
    print(f'Overview updated: {total}/18 independently verified')


if __name__=='__main__':
    main()
