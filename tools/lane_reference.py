"""Prepare and publish an explicitly unscored repair of a measured lane.

prepare PARENT_SESSION --port PORT; publish REFERENCE_SESSION
Then run lane_review.py development/production and lane_evidence.py parity.
Never changes an original source or invents a measured coding transcript.
"""
import argparse
import re
import secrets
import shutil
from pathlib import Path

import lane_run as lane
import measure
import one_shot_publish


def prepare(parent_path, port):
    if not 1024 <= port <= 15535:
        raise ValueError("Reference port must leave room for the disposable database port")
    parent = lane.load(parent_path)
    proof = lane.load(Path(parent["result"]) / "verification.json")
    snapshot = lane.load(Path(parent["result"]) / "source-snapshot.json")
    if (not proof.get("passed") and parent["phase"] != "reference") or proof["source_sha256"] != snapshot["sha256"]:
        raise RuntimeError("Reference must start from an independently verified source")
    previous = re.fullmatch(r"(.+)-reference-(\d+)", parent["id"])
    revision = int(previous[2]) + 1 if previous else 1
    sid = (previous[1] if previous else parent["id"].removesuffix("-1")) + f"-reference-{revision}"
    base = lane.LANES / sid
    if base.exists():
        raise RuntimeError("Reference already exists; preserve its work")
    work, control, logs, home = (base / name for name in ("app", "control", "logs", "home"))
    lane.copy_tree(Path(parent["publish_source"]), work)
    if {str(p.relative_to(work)): lane.digest(p) for p in lane.product_files(work)} != snapshot["files"]:
        raise RuntimeError("Parent source differs from its published manifest")
    for name in parent["frozen"]:
        original, target = Path(parent["work"]) / name, work / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if original.is_dir():
            shutil.copytree(original, target)
        else:
            shutil.copy2(original, target)
    fixture = lane.load(work / "FIXTURE.json")
    fixture.update(condition="unscored-reference-repair", parent_source_sha256=snapshot["sha256"])
    (work / "FIXTURE.json").chmod(0o644)
    lane.save(work / "FIXTURE.json", fixture)
    (work / "FIXTURE.json").chmod(0o444)
    for folder in (control, logs, home):
        folder.mkdir(mode=0o700)
    (control / "token").write_text(secrets.token_hex(32) + "\n")
    (control / "token").chmod(0o600)
    result_root = Path(parent["result"]).parent if previous else Path(parent["result"])
    result = result_root / f"reference-{revision}"
    session = dict(parent, id=sid, phase="reference", port=port, work=str(work), control=str(control),
                   logs=str(logs), home=str(home), result=str(result), publish_source=str(result / "source"),
                   fixture_file_sha256=lane.digest(work / "FIXTURE.json"),
                   volumes=[dict(v, name=v["name"].replace(parent["id"], sid)) for v in parent["volumes"]])
    path = control / "session.json"
    lane.save(path, session)
    lane.verify_workspace(session)
    lane.save(result / "reference.json", {
        "condition": "unscored-reference-repair", "session": sid,
        "parent_session": parent["id"], "parent_source_sha256": snapshot["sha256"],
        "parent_independent_checks_passed": proof.get("passed", False),
        "revision": revision,
        "created_at": lane.stamp(), "coding_effort": "Not a comparable measured coding session",
        "check_port": port, "originals_modified": False,
        "checks": "Use coordinator lane_review.py and lane_evidence.py; inherited agent wrappers retain their historical ports",
    })
    print(path, flush=True)
    return path


def publish(path):
    session = lane.load(path)
    if session["phase"] != "reference":
        raise RuntimeError("This publisher is only for unscored references")
    lane.verify_workspace(session)
    work, dest, source = (Path(session[key]) for key in ("work", "result", "publish_source"))
    if (dest / "source-snapshot.json").exists():
        raise RuntimeError("Published reference is immutable; prepare a new reference for further edits")
    files = {}
    token = (Path(session["control"]) / "token").read_text().strip().encode()
    extras = {kind: {"tokens": 0, "lines": 0, "files": []} for kind in ("tests", "docs")}
    rules = measure.load_stack(session["stack"])
    tests = []
    for original in lane.product_files(work):
        rel = original.relative_to(work)
        content = original.read_bytes()
        if token in content or str(Path.home()).encode() in content or b"-----BEGIN PRIVATE KEY-----" in content:
            raise RuntimeError(f"Private material in reference source: {rel}")
        target = source / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, target)
        files[str(rel)] = lane.digest(original)
        kind = "docs" if original.suffix == ".md" else "tests" if (
            original.name.endswith("_test.go") or original.name.startswith("test_")
            or original.name == "tests.py") else None
        if kind:
            lines = measure.read_lines(original.read_text())
            extras[kind]["tokens"] += measure.tokens(lines)
            extras[kind]["lines"] += len(lines)
            extras[kind]["files"].append(str(rel))
        if kind == "tests":
            tests.append(original.name)
    rules["code"]["skip_files"] = list(set(rules["code"].get("skip_files", [])) | set(tests))
    size = measure.measure(rules, work, work / ".scaffold")
    size.update(encoding="o200k_base", baseline="same frozen product-free scaffold as parent")
    inventory = one_shot_publish.source_inventory(rules, work)
    assert sum(row["owned_tokens"] for row in inventory) == size["owned_tokens"]
    lane.save(dest / "source-snapshot.json", {"sha256": lane.fingerprint(files),
                                            "path": str(source.relative_to(lane.ROOT)), "files": files})
    lane.save(dest / "size.json", size)
    lane.save(dest / "source-files.json", inventory)
    lane.save(dest / "supplementary-size.json", extras)
    print(f'Published unscored {session["id"]}: {size["owned_tokens"]} owned tokens', flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "publish"))
    parser.add_argument("session", type=Path)
    parser.add_argument("--port", type=int)
    args = parser.parse_args()
    if args.action == "prepare":
        if args.port is None:
            parser.error("prepare requires --port")
        prepare(args.session.resolve(), args.port)
    else:
        publish(args.session.resolve())
