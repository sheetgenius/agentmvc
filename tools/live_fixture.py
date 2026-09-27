"""Freeze and verify the identical step-8 inputs given to every backend agent."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "spec/features/live-editing/fixture-manifest.json"
EXCLUDED = {"node_modules", "dist", "test-results", "playwright-report", "__pycache__", "validation"}


def files():
    paths = [ROOT / "steps/8-live-editing.md"]
    for directory in (ROOT / "spec", ROOT / "frontend", ROOT / "tools/security"):
        paths.extend(path for path in directory.rglob("*") if path.is_file()
                     and path != MANIFEST and not EXCLUDED.intersection(path.relative_to(ROOT).parts)
                     and not path.name.startswith(".DS_Store"))
    return sorted(paths)


def snapshot():
    digests = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files()}
    data = json.dumps(digests, sort_keys=True, separators=(",", ":")).encode()
    return {"sha256": hashlib.sha256(data).hexdigest(), "files": digests}


def workdir_changes(workdir):
    manifest = json.loads(MANIFEST.read_text())["files"]
    changed = []
    copied_manifest = workdir / "realworld_spec/features/live-editing/fixture-manifest.json"
    if not copied_manifest.exists() or copied_manifest.read_bytes() != MANIFEST.read_bytes():
        changed.append("spec/features/live-editing/fixture-manifest.json")
    for source, digest in manifest.items():
        if source.startswith("steps/") or source in {"spec/LICENSE", "spec/README.md"}:
            continue
        if source.startswith("tools/security/"):
            if source not in {"tools/security/run-hurl.sh"} and not source.startswith("tools/security/hurl/"):
                continue
            target = workdir / source.removeprefix("tools/")
        elif source.startswith("spec/"):
            target = workdir / "realworld_spec" / source.removeprefix("spec/")
        else:
            target = workdir / "realworld_spec" / source
        if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            changed.append(source)
    frontend = workdir / "realworld_spec/frontend"
    expected = {name.removeprefix("frontend/") for name in manifest if name.startswith("frontend/")}
    for path in frontend.rglob("*"):
        if path.is_file() and not EXCLUDED.intersection(path.relative_to(frontend).parts) \
                and str(path.relative_to(frontend)) not in expected:
            changed.append("frontend/" + str(path.relative_to(frontend)))
    return changed


if __name__ == "__main__":
    current = snapshot()
    if sys.argv[1:] == ["freeze"]:
        MANIFEST.write_text(json.dumps(current, indent=2) + "\n")
    elif sys.argv[1:] == ["verify"]:
        if not MANIFEST.exists() or json.loads(MANIFEST.read_text()) != current:
            raise SystemExit("step-8 fixture changed after freeze")
    elif len(sys.argv) == 3 and sys.argv[1] == "verify-workdir":
        changed = workdir_changes(Path(sys.argv[2]))
        if changed:
            raise SystemExit("agent modified frozen inputs: " + ", ".join(changed))
    else:
        raise SystemExit("usage: tools/live_fixture.py freeze|verify|verify-workdir DIR")
    print(current["sha256"])
