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
              'Backend size excludes tests, docs, dependencies, lockfiles and the fixed client. Owned size is the change from the supplied scaffold. Each checkpoint also records whole-app size and tests/docs separately.','',
              '## Try a completed app','',
              'With Docker, Node.js and npm installed, these commands build a published step-8 source, create a fresh database, and open the fixed Lit editor. They become available when the corresponding step-8 checkpoint is published. Ctrl-C removes their containers.','',
              '```sh','tools/lane_demo.sh go','tools/lane_demo.sh python',
              '# Or use the independently built expert app:','tools/lane_demo.sh python one-shot','```','',
              '## Evidence and limits','',
              '- [Go preflight](go/preflight.json) and [Python preflight](python/preflight.json): migrations, durable jobs, sockets, reload, production packaging and image identities.',
              '- Each checkpoint directory contains its measured agent report, effort/failure counts, source inventory, actual isolation probe and independent verification.',
              '- [Comprehension](comprehension/): fresh read-only agents answer the original twelve questions after steps 1 and 6. Scores require source-supported grading.',
              '- Reviewer parity adds the same 21 contract and 3 quality HTTP probes used for the current references. Original failures remain visible; later repairs must be separate snapshots.',
              '- Tuning feedback uses short 3-second samples. Final HTTP measurements use all nine workloads, 16 users and two 15-second rounds, with app and database each limited to 2 CPUs and 1 GiB. Socket measurements cover 10, 100 and 500 subscribers.',
              '- Full transcripts and compressed raw streams belong in external release assets, with checked hashes and links recorded here when published. They are not committed to Git.','',
              '[Detailed method and reproduction commands](METHODOLOGY.md) · [Main comparison](../../README.md) · [Contributing](../../CONTRIBUTING.md)','']
    (OUT/'README.md').write_text('\n'.join(lines))
    print(f'Overview updated: {total}/18 independently verified')


if __name__=='__main__':
    main()
