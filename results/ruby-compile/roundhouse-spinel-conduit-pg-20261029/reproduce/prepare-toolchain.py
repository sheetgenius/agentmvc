"""Recreate the recorded toolchain context with a clean, verified patch replay."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

P = Path(__file__).resolve().parent.parent
pins = json.loads((P / 'evidence/final-pins.json').read_text())
build = Path(sys.argv[1] if len(sys.argv) > 1 else P / 'reproduce/build').resolve()
context = build / 'toolchain-context'
sources = build / 'src'
if context.exists() or sources.exists():
    raise SystemExit('Use a fresh BUILD_DIR; existing exported sources are preserved.')
context.mkdir(parents=True)
sources.mkdir(parents=True)

def run(*args):
    return subprocess.check_output(args, text=True).strip()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def tree(root):
    rows = []
    for directory, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name != '.git']
        for name in files:
            path = Path(directory) / name
            data = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
            rows.append(hashlib.sha256(data).hexdigest() + '  ' + str(path.relative_to(root)) + '\n')
    return hashlib.sha256(''.join(sorted(rows, key=lambda line: line[66:])).encode()).hexdigest()

for name, url, dest in [('roundhouse', 'https://github.com/rubys/roundhouse.git', 'patches'),
                        ('spinel', 'https://github.com/matz/spinel.git', 'spinel-patches')]:
    source = sources / name
    run('git', 'init', '-q', str(source))
    run('git', '-C', str(source), 'remote', 'add', 'origin', url)
    run('git', '-C', str(source), 'fetch', '-q', '--depth=1', 'origin', pins[name])
    run('git', '-C', str(source), '-c', 'advice.detachedHead=false', 'checkout', '-q', pins[name])
    patchdir = P / 'patches' / name
    assert sha(patchdir / 'SHA256SUMS') == pins[name + '_manifest_sha256']
    for line in (patchdir / 'SHA256SUMS').read_text().splitlines():
        expected, path = line.split(None, 1)
        assert sha(patchdir / path) == expected, path
    for patch in (patchdir / 'series').read_text().split():
        run('git', '-C', str(source), 'apply', '--check', str(patchdir / patch))
        run('git', '-C', str(source), 'apply', str(patchdir / patch))
    shutil.copytree(source, context / 'vendor' / name, ignore=shutil.ignore_patterns('.git'))
    if name == 'spinel':
        (context / 'vendor/spinel/.spinel-dist').write_text(pins['spinel'][:9] + '\n'
                                                          + pins['spinel_version'] + '\n')
    actual = tree(context / 'vendor' / name)
    assert actual == pins[name + '_tree_sha256'], (name, actual)
    shutil.copytree(patchdir, context / dest)
    print(name + ' clean replay matches recorded source digest: ' + actual, flush=True)
shutil.copy2(P / 'toolchain/Dockerfile.toolchain', context / 'Dockerfile')
for base in ['src', 'runtime']:
    for path in (context / 'vendor/roundhouse' / base).rglob('*'):
        if path.is_file():
            os.utime(path, None)
os.utime(context / 'vendor/roundhouse/build.rs', None)
print('context: ' + str(context))
