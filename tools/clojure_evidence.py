"""Clojure reviewer evidence using the unchanged lane workloads and probes.

The runtime/comprehension CLI matches lane_evidence.py. Additional commands:
  share --session PATH [--port PORT]
  reference-prepare --session PARENT --port PORT
  reference-publish --session PATH

This reviewer adapter is outside measured coding inputs. It never modifies
the earlier Go/Python cohort and records its own hash with the reused tools.
"""
import argparse
from pathlib import Path

import clojure_lane
import lane_evidence as evidence
import lane_reference
import lane_run
import lane_share_review
import measure


def install():
    clojure_lane.install()
    # The historical reviewer installs its TCP-only command wrapper at each
    # entry point. Keep the new lane's child-process routing as well.
    evidence.reviewer.install = lambda: setattr(evidence.broker, "command", clojure_lane.command)
    evidence.OUT = evidence.ROOT / "results/lanes/clojure"
    evidence.ENTRIES = (("clojure", "8"), ("clojure", "one-shot"))
    evidence.TOOLS = tuple(dict.fromkeys((*evidence.TOOLS, "clojure_lane.py", "clojure_evidence.py")))
    evidence.__doc__ = (__doc__ + "\nMeasured runtime contains the two Clojure final applications, "
                        "with two reversed-order rounds and unchanged workloads.\n")
    # Runtime children must enter this adapter too, rather than loading the
    # historical four-application defaults in a separate Python process.
    evidence.__file__ = str(Path(__file__).resolve())


def require_clojure(path):
    data = lane_run.load(path)
    if data["stack"] != "clojure":
        raise ValueError("This adapter is restricted to the Clojure lane")
    clojure_lane.verify(data)
    lane_run.verify_workspace(data)
    return data


def reference_publish(path):
    data = require_clojure(path)
    lane_reference.publish(path)
    extras = {kind: {"tokens": 0, "lines": 0, "files": []} for kind in ("tests", "docs")}
    work = Path(data["work"])
    for source in lane_run.product_files(work):
        relative = source.relative_to(work)
        kind = ("docs" if source.suffix == ".md" else "tests"
                if {"test", "tests"}.intersection(relative.parts)
                or source.name.endswith(("_test.clj", "_test.cljc", "_test.cljs")) else None)
        if kind:
            lines = measure.read_lines(source.read_text())
            extras[kind]["tokens"] += measure.tokens(lines)
            extras[kind]["lines"] += len(lines)
            extras[kind]["files"].append(str(relative))
    lane_run.save(Path(data["result"]) / "supplementary-size.json", extras)
    lane_run.save(Path(data["result"]) / "reviewer-adapter.json", {
        "adapter": "tools/clojure_evidence.py", "sha256": lane_run.digest(__file__),
        "condition": "unscored reference; unchanged measured inputs",
        "supplementary_accounting": "Clojure test directories and *_test namespaces; Markdown separately",
    })


def reference_prepare(path, port):
    prepared = lane_reference.prepare(path, port)
    data = require_clojure(prepared)
    record_path = Path(data["result"]) / "reference.json"
    record = lane_run.load(record_path)
    record.update(
        checks="Use tools/clojure_lane.py check REFERENCE_SESSION, then the parity and share "
               "commands of tools/clojure_evidence.py with --session REFERENCE_SESSION; "
               "inherited agent wrappers retain their historical ports",
        effective_fixture_sha256=data["effective_fixture_sha256"],
        reviewer_tools_sha256={name: lane_run.digest(evidence.ROOT / "tools" / name)
                              for name in ("clojure_evidence.py", "clojure_lane.py", "lane_reference.py")},
    )
    lane_run.save(record_path, record)
    return prepared


def main():
    import sys

    install()
    if len(sys.argv) > 1 and sys.argv[1] in ("share", "reference-prepare", "reference-publish"):
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("action")
        parser.add_argument("--session", required=True, type=Path)
        parser.add_argument("--port", type=int)
        args = parser.parse_args()
        path = args.session.resolve()
        require_clojure(path)
        if args.action == "reference-prepare":
            if args.port is None:
                parser.error("reference-prepare requires --port")
            reference_prepare(path, args.port)
        elif args.action == "reference-publish":
            reference_publish(path)
        else:
            passed = lane_share_review.run(path, args.port)
            record = Path(lane_run.load(path)["result"]) / "reviewer-parity/share-boundary.json"
            data = lane_run.load(record)
            data["tools_sha256"].update({name: lane_run.digest(evidence.ROOT / "tools" / name)
                                        for name in ("clojure_lane.py", "clojure_evidence.py")})
            evidence.save(record, data, evidence.broker.Session(path))
            return 0 if passed else 1
        return 0
    # Do not let an explicit session bypass the lane-specific cohort boundary.
    session_parser = argparse.ArgumentParser(add_help=False)
    session_parser.add_argument("--session", type=Path, action="append", default=[])
    sessions, _ = session_parser.parse_known_args()
    for path in sessions.session:
        require_clojure(path.resolve())
    return evidence.main()


if __name__ == "__main__":
    raise SystemExit(main())
