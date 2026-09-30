"""Small offline inventory tests; no Docker, coding or archive creation."""
import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import clojure_artifacts as adapter
import lane_artifacts as artifacts
import lane_run


class ClojureArtifactsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.out = self.root / "results/lanes/clojure"
        self.oneshot = self.root / "results/one-shot-v2-clojure-expert"
        self.work = self.root / ".work/clojure-artifacts"
        finals = {"clojure-8-live-editing-1": self.out / "8-live-editing",
                  "clojure-one-shot-1": self.oneshot / "pilot-1"}
        for target, values in ((adapter, dict(ROOT=self.root, OUT=self.out, ONESHOT=self.oneshot,
                                             WORK=self.work, FINALS=finals)),
                               (artifacts, dict(ROOT=self.root, OUT=self.out, WORK=self.work,
                                                SOURCES=(self.out, self.oneshot), runtime_finished=adapter.runtime_finished))):
            context = patch.multiple(target, **values)
            context.start()
            self.addCleanup(context.stop)

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value) + "\n" if not isinstance(value, str) else value)
        return path

    def session(self, sid="clojure-1-build-1"):
        base = self.root / ".work/lanes" / sid
        phase = sid.removeprefix("clojure-").removesuffix("-1")
        result = self.oneshot / "pilot-1" if phase == "one-shot" else self.out / phase
        data = {"id": sid, "stack": "clojure", "phase": phase, "result": str(result),
                **{key: str(base / name) for key, name in
                   (("work", "app"), ("home", "home"), ("logs", "logs"), ("control", "control"))}}
        return self.write(base / "control/session.json", data), data

    def published(self, folder, sid):
        source = self.root / "stacks/clojure" / folder.name if folder.parent == self.out else folder / "source"
        path = self.write(source / "core.clj", f"(ns {sid})\n")
        files = {"core.clj": lane_run.digest(path)}
        sha = lane_run.fingerprint(files)
        self.write(folder / "source-snapshot.json", {"files": files, "sha256": sha,
                                                      "path": str(source.relative_to(self.root))})
        self.write(folder / "verification.json", {"passed": True, "source_sha256": sha,
                                                   "checks": {"development": 0, "production": 0}})
        self.write(folder / "isolation.json", {"passed": True})
        self.write(folder / "run.json", {"id": sid, "condition": "prepared-clojure", "finished": "later"})
        return sha

    def reviewed(self, folder, sha, passed=True):
        for name in ("results.json", "share-boundary.json"):
            self.write(folder / "reviewer-parity" / name, {"source_sha256": sha, "passed": passed})

    def runtime(self, condition, applications):
        records = []
        for sid, identity in applications.items():
            for number in (1, 2):
                for kind in ("http", "socket"):
                    path = f"{sid}/round{number}/{kind}"
                    data = {**identity, "finished": "later", "session": sid, "round": number, "exit": 0, "passed": True}
                    if kind == "http":
                        data["raw_stream_sha256"] = {f"raw-{prefix}{scenario}.json.zst": "fake-raw-hash"
                                                     for prefix in ("", "warmup-") for scenario in adapter.lane_check.SCENARIOS}
                        data.update(scenarios={name: {"requests": 1, "failed_checks": 0} for name in adapter.lane_check.SCENARIOS},
                                    vus=16, warmup="3s", duration="15s", limits=adapter.lane_check.LIMITS)
                    else:
                        data["scenarios"] = [{"subscribers": value, "saves": 20, "missing": 0,
                                               "duplicate_revisions": 0, "regressed_revisions": 0} for value in (10, 100, 500)]
                    self.write(self.out / "runtime" / condition / path / "results.json", data)
                    records.append({"session": sid, "round": number, "kind": kind, "path": path})
        self.write(self.out / "runtime" / condition / "summary.json",
                   {"condition": condition, "finished": "later", "passed": True,
                    "applications": applications, "records": records})

    def test_scope_guard_rejects_cross_cohort_result_and_mismatched_descriptor(self):
        descriptor, data = self.session()
        self.assertEqual(adapter.scoped_session(descriptor), data)
        data["result"] = str(self.root / "results/lanes/go/1-build")
        self.write(descriptor, data)
        with self.assertRaisesRegex(RuntimeError, "allowed cohort"):
            adapter.scoped_session(descriptor)
        data["result"] = str(self.out / "1-build")
        other = self.write(self.root / ".work/lanes/go-1-build-1/control/session.json", data)
        with self.assertRaisesRegex(RuntimeError, "descriptor path"):
            adapter.scoped_session(other)

    def test_feedback_enumeration_never_exports_old_cohort(self):
        descriptor, data = self.session()
        attempt = Path(data["logs"]) / "measurements/failed-feedback"
        attempt.mkdir(parents=True)
        self.write(self.root / ".work/lanes/go-1-build-1/control/session.json", "invalid JSON that must not be read")
        (self.root / ".work/lanes/go-1-build-1/logs/measurements/old").mkdir(parents=True)
        with (patch.object(artifacts, "checker", return_value=object()),
              patch.object(artifacts, "export_feedback_attempt", return_value={"status": "test"}) as export):
            result = adapter.export_feedback()
            export.assert_called_once()
            self.assertEqual(export.call_args.args[0], attempt)
            self.assertEqual(result["feedback_attempts"], [{"status": "test"}])
        self.assertEqual(artifacts.OUT, self.out)

    def test_checks_include_failures_broker_and_history_but_no_credentials(self):
        descriptor, data = self.session()
        base = descriptor.parents[1]
        expected = {"control/independent-development.log", "control/independent-attempts/01/independent-development.log",
                    "logs/broker/failed-run.log", "logs/broker/requests.jsonl", "logs/independent/failed.json",
                    "logs/security-scans/findings.json", "logs/stderr.log"}
        for name in expected | {"control/token", "home/auth.json", "logs/events.jsonl"}:
            self.write(base / name, "placeholder\n")
        self.assertEqual({str(path.relative_to(base)) for path in adapter.check_sources(data)}, expected)

    @unittest.skipUnless(shutil.which("zstd"), "tiny log export requires zstd")
    def test_check_export_scrubs_and_preserves_changed_attempts_in_new_directories(self):
        descriptor, data = self.session()
        base = descriptor.parents[1]
        token = "synthetic-private-broker-token-for-offline-export"
        self.write(base / "control/token", token + "\n")
        log = self.write(base / "control/independent-development.log", "failed: " + token + "\n")
        self.write(base / "logs/broker/requests.jsonl", '{"action":"development","exit":1}\n')
        with patch.object(adapter, "tool_hashes", return_value={}):
            first = adapter.export_checks()["exported"]
            again = adapter.export_checks()["exported"]
            self.assertEqual(first, again)
            exported = self.root / first[0]
            record = adapter.read(exported / "results.json")
            compressed = exported / "control--independent-development.log.zst"
            text = subprocess.check_output(["zstd", "-dc", str(compressed)]).decode()
            self.assertNotIn(token, text)
            self.assertIn("failed:", text)
            self.assertEqual(record["export_file_sha256"][compressed.name], lane_run.digest(compressed))
            self.assertEqual(adapter.read(exported / "logs--broker--requests.json"), [{"action": "development", "exit": 1}])
            before = compressed.read_bytes()
            log.write_text("later independent attempt\n")
            later = adapter.export_checks()["exported"]
            self.assertNotEqual(first, later)
            self.assertEqual(compressed.read_bytes(), before)

    def test_inventory_has_nine_coding_two_readers_and_72_streams_without_cloned_references(self):
        coding = {artifacts.relative(folder / "transcript.jsonl") for folder in adapter.original_results().values()}
        readers = {artifacts.relative(self.out / "comprehension" / f"clojure-after-{phase}" / "transcript.jsonl")
                   for phase in ("1-build", "6-polish")}
        raw = adapter.raw_paths("measured", adapter.FINALS)
        extra = artifacts.relative(self.out / "runtime/feedback/clojure-3-package-1/attempt/raw-feed.json.zst")
        data = {"files": {"transcripts": [{"path": name} for name in coding | readers],
                           "runtime": [{"path": name} for name in raw | {extra}], "evidence": []},
                "provenance": {}}
        with (patch.object(adapter, "_collect", side_effect=lambda: copy.deepcopy(data)),
              patch.object(adapter, "completion", return_value={"ready": True}),
              patch.object(adapter, "runtime_finished", side_effect=lambda condition: condition == "measured")):
            coverage = adapter.collect()["coverage"]
            self.assertEqual(coverage["expected_originals"], {"coding_transcripts": 9, "reader_transcripts": 2, "measured_raw_streams": 72})
            self.assertTrue(coverage["original_inventory_complete"])
            self.assertTrue(coverage["reference_inventory_complete"])
            self.assertEqual(coverage["additional_runtime_streams"], 1)
            data["files"]["transcripts"].pop()
            self.assertFalse(adapter.collect()["coverage"]["original_inventory_complete"])

    def test_runtime_requires_both_rounds_all_stream_names_and_current_source(self):
        identities = {sid: {"source_sha256": self.published(folder, sid), "image_sha256": "sha256:example"}
                      for sid, folder in adapter.FINALS.items()}
        self.runtime("measured", identities)
        self.assertTrue(adapter.runtime_finished("measured"))
        path = self.out / "runtime/measured/clojure-one-shot-1/round2/http/results.json"
        record = adapter.read(path)
        record["raw_stream_sha256"].pop("raw-feed.json.zst")
        self.write(path, record)
        self.assertFalse(adapter.runtime_finished("measured"))
        self.runtime("measured", identities)
        (self.oneshot / "pilot-1/source/core.clj").write_text("(ns changed-after-check)\n")
        self.assertFalse(adapter.runtime_finished("measured"))

    def test_historical_failed_reference_is_retained_but_only_promoted_ref_needs_runtime(self):
        for sid, folder in adapter.original_results().items():
            sha = self.published(folder, sid)
            if sid in adapter.FINALS:
                self.reviewed(folder, sha)
        folder = self.oneshot / "pilot-1/reference-1"
        sid = "clojure-one-shot-reference-1"
        sha = self.published(folder, sid)
        self.write(folder / "reference.json", {"session": sid, "parent_session": "clojure-one-shot-1"})
        self.reviewed(folder, sha, passed=False)
        with (patch.object(adapter, "reader_graded", return_value=True),
              patch.object(adapter, "runtime_finished", return_value=True)):
            result = adapter.completion()
            self.assertTrue(result["ready"])
            self.assertEqual(result["selected_references"], [])
            self.assertEqual(result["selected_finals"]["clojure-one-shot-1"]["session"], "clojure-one-shot-1")
            self.reviewed(folder, sha)
            self.write(self.out / "runtime/reference/summary.json", {"applications": {sid: {"source_sha256": sha}}})
            result = adapter.completion()
            self.assertTrue(result["ready"])
            self.assertEqual(result["selected_references"], [sid])
            self.assertEqual(result["selected_finals"]["clojure-one-shot-1"]["session"], sid)

    def test_reader_grading_binds_source_answer_key_and_prelaunch_time(self):
        phase = "1-build"
        source = self.published(self.out / phase, "clojure-1-build-1")
        folder = self.out / "comprehension/clojure-after-1-build"
        answer = self.write(folder / "answer.md", "A source-supported answer\n")
        key = self.write(folder / "answer-key.md", "The source-derived key\n")
        key_sha = lane_run.digest(key)
        dates = [f"2026-09-30T10:0{number}:00+00:00" for number in range(4)]
        run = {"source_sha256": source, "readable_source_sha256": "readable", "answer_key_sha256_before_reader": key_sha,
               "exit": 0, "source_unchanged": True, "started": dates[1], "finished": dates[2]}
        self.write(folder / "run.json", run)
        self.write(folder / "started.json", run)
        self.write(folder / "prepared.json", {"source_sha256": source, "readable_source_sha256": "readable"})
        self.write(folder / "isolation.json", {"passed": True})
        self.write(folder / "key-preparation.json", {"saved_at": dates[0], "answer_key_sha256": key_sha,
                                                      "reader_answers_consulted": False, "source_snapshot_sha256": source})
        grades = {"source_sha256": source, "answer_key_sha256": key_sha, "answer_sha256": lane_run.digest(answer),
                  "graded_at": dates[3], "reader_started_at": dates[1], "answer_key_saved_at": dates[0],
                  "score": 12, "maximum": 12,
                  "items": [{"question": n, "score": 1, "reason": "Supported", "source": "core.clj:1"} for n in range(1, 13)]}
        self.write(folder / "grades.json", grades)
        self.assertTrue(adapter.reader_graded(phase))
        grades["answer_key_saved_at"] = dates[2]
        self.write(folder / "grades.json", grades)
        self.assertFalse(adapter.reader_graded(phase))
        grades["answer_key_saved_at"] = dates[0]
        self.write(folder / "grades.json", grades)
        answer.write_text("changed answer\n")
        self.assertFalse(adapter.reader_graded(phase))

    def test_reader_answer_can_come_from_the_message_archive(self):
        folder = self.out / "comprehension/clojure-after-1-build"
        answer = self.write(folder / "answer.md", "A source-supported answer\n")
        expected = lane_run.digest(answer)

        def git(*args):
            return subprocess.run(["git", "-C", str(self.root), "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                                   "-c", "commit.gpgsign=false", *args], check=True, capture_output=True, text=True).stdout.strip()

        git("init", "-q")
        git("add", answer.relative_to(self.root).as_posix())
        git("commit", "-q", "--no-verify", "-m", "answer")
        commit = git("rev-parse", "HEAD")
        answer.unlink()
        self.assertIsNone(adapter.answer_digest(answer))
        self.write(self.root / "results/message-archive.json", {"commit": commit})
        self.assertEqual(adapter.answer_digest(answer), expected)
        self.write(self.root / "results/message-archive.json", {"commit": "0" * 40})
        self.assertIsNone(adapter.answer_digest(answer))

    def test_package_refuses_incomplete_evidence_before_exports_or_archives(self):
        with (patch.object(adapter, "completion", return_value={"ready": False}),
              patch.object(adapter, "export_feedback") as feedback,
              patch.object(adapter, "export_checks") as checks,
              patch.object(artifacts, "create_archive") as archive):
            with self.assertRaisesRegex(RuntimeError, "Complete nine coding"):
                adapter.package("v1")
            feedback.assert_not_called()
            checks.assert_not_called()
            archive.assert_not_called()
        self.assertFalse(self.work.exists())


if __name__ == "__main__":
    unittest.main()
