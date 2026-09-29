"""Run the separately labeled shared-edit probe on one immutable final app."""
import argparse
import json
import sys
from pathlib import Path

import lane_broker as broker
import lane_check
import lane_evidence as evidence
import lane_review


def run(path, port=None):
    lane_review.install()
    session = broker.Session(path)
    if port is not None:
        if not 1024 <= port <= 15535:
            raise ValueError("Invalid reviewer application port")
        session.port = port
    identity = evidence.source_identity(session)
    dest = evidence.parity_path(session)
    target = dest / "share-boundary.json"
    if target.exists():
        raise RuntimeError("Preserving existing shared-edit evidence")
    dest.mkdir(parents=True, exist_ok=True)
    record = dict(identity, condition="supplemental shared-edit review; not a frozen gate",
                  started=broker.stamp(), passed=False, app_port=session.port,
                  app_environment_keys=["DATABASE_URL", "SECRET_KEY_BASE", "PORT"],
                  tools_sha256={name: broker.digest(broker.ROOT / "tools" / name) for name in
                                ("lane_share_review.py", "lane_share_probe.py", "reviewer_common_http_probe.py",
                                 "lane_check.py", "lane_review.py", "lane_evidence.py")})
    output = []
    try:
        with broker.resources():
            session.verify()
            with lane_check.production_app(session, output):
                record["image_sha256"] = evidence.image_id(session)
                code, text = broker.command([
                    sys.executable, str(broker.ROOT / "tools/lane_share_probe.py"),
                    "--base-url", f"http://127.0.0.1:{session.port}", "--strict-diagnostics"], timeout=120)
                record["probe"] = json.loads(text)
                record["exit"] = code
                summary = record["probe"]["summary"]
                record["passed"] = code == 0 and summary.get("contract_passed") == summary.get("contract_total") == 3 and summary.get("quality_diagnostic_passed") == summary.get("quality_diagnostic_total") == 1
            session.verify()
            if evidence.source_identity(session) != identity:
                raise RuntimeError("Source changed during shared-edit review")
    except Exception as error:
        record.update(passed=False, error=f"{type(error).__name__}: {error}")
    finally:
        record["finished"] = broker.stamp()
        evidence.write_text(dest / "share-boundary.log", "\n".join(output), session)
        evidence.save(target, record, session)
    print(f'{session.id}: shared-edit review {"passed" if record["passed"] else "failed"}', flush=True)
    return record["passed"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=Path)
    parser.add_argument("--port", type=int, help="Review on a free port while another independent session codes")
    args = parser.parse_args()
    raise SystemExit(0 if run(args.session.resolve(), args.port) else 1)
