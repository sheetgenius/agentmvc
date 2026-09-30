"""Offline checks for the new Clojure coordinator; never starts Docker/Codex."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import clojure_lane as adapter
import lane_broker
import lane_run
import measure


class ClojureLaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        adapter.install()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def write(self, relative, text="(ns example)\n"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def test_source_publication_and_measurement_keep_clojure_and_omit_caches(self):
        for name in ("src/core.clj", "src/shared.cljc", "src/client.cljs", "deps.edn",
                     "src/core_test.clj", "test/example.clj", "docs/README.md", ".clj-kondo/config.edn"):
            self.write(name)
        for cache in adapter.CACHE_DIRS:
            self.write(f"{cache}/cached.clj")
        self.write(".clj-kondo/.cache/exported.clj")
        published = {str(path.relative_to(self.root)) for path in lane_run.product_files(self.root)}
        self.assertEqual(published, {"src/core.clj", "src/shared.cljc", "src/client.cljs", "deps.edn",
                                     "src/core_test.clj", "test/example.clj", "docs/README.md", ".clj-kondo/config.edn"})
        rules = {"stack": "clojure", "code": {"extensions": dict.fromkeys(adapter.SOURCE_SUFFIXES, ";"),
                                                "skip_dirs": [".clj-kondo"]}}
        measured = {name for name, _ in measure.source_files(rules, self.root)}
        self.assertEqual(measured, {"src/core.clj", "src/shared.cljc", "src/client.cljs", "deps.edn"})
        extras = adapter.supplementary_size(self.root)
        self.assertEqual(set(extras["tests"]["files"]), {"src/core_test.clj", "test/example.clj"})
        self.assertEqual(extras["docs"]["files"], ["docs/README.md"])
        self.assertGreater(extras["tests"]["tokens"], 0)

    def test_linter_config_survives_copy_and_fixture_hashing_without_dependency_cache(self):
        self.write("scaffold/.clj-kondo/config.edn", "{}\n")
        self.write("scaffold/.clj-kondo/.cache/dependency-export.clj", "generated\n")
        source, target = self.root / "scaffold", self.root / "app"
        lane_run.copy_tree(source, target)
        expected = {".clj-kondo/config.edn"}
        self.assertEqual({str(path.relative_to(source)) for path in lane_run.checked_files(source, lane_run.SKIP)}, expected)
        self.assertEqual({str(path.relative_to(target)) for path in lane_run.checked_files(target)}, expected)
        self.assertEqual((source / ".clj-kondo/config.edn").read_bytes(), (target / ".clj-kondo/config.edn").read_bytes())

    def test_snapshot_tracks_transitive_helpers_source_and_modes_without_self_hash(self):
        self.write("tools/clojure_lane.py", "import adapter_helper\n")
        self.write("tools/one_shot_publish.py", "import publisher_helper\n")
        helper = self.write("tools/adapter_helper.py", "import nested_helper\n")
        self.write("tools/nested_helper.py", "VALUE = 1\n")
        self.write("tools/publisher_helper.py", "VALUE = 2\n")
        source = self.write("stacks/clojure/scaffold/src/core.clj")

        def base(_stack):
            relative = str(source.relative_to(self.root))
            return {"files": {relative: lane_run.digest(source)}, "modes": {relative: 0}}

        with patch.object(lane_run, "ROOT", self.root), patch.object(adapter, "_source_snapshot", side_effect=base):
            first = adapter.source_snapshot("clojure")
            self.assertIn("tools/nested_helper.py", first["files"])
            self.assertIn("tools/publisher_helper.py", first["files"])
            self.write("stacks/clojure/lane-fixture.json", json.dumps(first))
            self.assertEqual(first, adapter.source_snapshot("clojure"))
            self.assertNotIn("stacks/clojure/lane-fixture.json", first["files"])
            source.write_text("(ns changed)\n")
            second = adapter.source_snapshot("clojure")
            self.assertNotEqual(first["sha256"], second["sha256"])
            helper.write_text("import nested_helper\nCHANGED = True\n")
            third = adapter.source_snapshot("clojure")
            self.assertNotEqual(second["sha256"], third["sha256"])
            helper.chmod(0o755)
            self.assertNotEqual(third["sha256"], adapter.source_snapshot("clojure")["sha256"])

    def fixture_inputs(self):
        real_root = lane_run.ROOT
        self.write("stacks/clojure/runtime.json", json.dumps({
            "port": 4112, "image": "offline-clojure", "volumes": [], "commands": {}}))
        self.write("stacks/clojure/scaffold/src/core.clj")
        self.write("stacks/clojure/ENVIRONMENT.md", "Clojure environment\n")
        self.write("one-shot-v2-clojure-expert/ENVIRONMENT.md", "Clojure expert environment\n")
        prompts = [f"steps/{lane_run.workdir.step_name(n)}.md" for n in range(1, 9)]
        for path in [*prompts, "one-shot-v2-expert/PROMPT.md", "one-shot-v2-expert/MEASUREMENT.md"]:
            self.write(path, (real_root / path).read_text())
        for folder in ("api", "docs", "bin"):
            self.write(f"spec/{folder}/fixture.txt", "frozen input\n")
        for feature in lane_run.workdir.FEATURES:
            self.write(f"spec/features/{feature}/fixture.txt", "frozen feature\n")
        self.write("one-shot/frontend/index.html", "frozen frontend\n")
        for path in ("one-shot/harness/check-client.py", "one-shot/harness/run-live-container.sh",
                     "tools/bench/bench.py", "tools/bench/load.js", "tools/bench/seed.py",
                     "tools/security/hurl/probe.hurl"):
            self.write(path, "frozen helper\n")

    def test_prepare_sets_condition_before_prewarm_preserves_prompts_and_fresh_homes(self):
        self.fixture_inputs()
        fixture = {"sha256": "frozen-source", "toolchain_image_id": "toolchain", "browser_image_id": "browser"}
        warmed = []

        def home(path, config):
            path.mkdir(mode=0o700)
            (path / "config.toml").write_text(config)

        def warmed_session(path):
            session = lane_run.load(path)
            adapter.verify(session)
            lane_run.verify_workspace(session)
            self.assertEqual(session["broker_port"], 49682)
            self.assertEqual(lane_run.load(Path(session["work"]) / "FIXTURE.json")["condition"], "prepared-clojure")
            warmed.append(session)

        with (patch.object(lane_run, "ROOT", self.root),
              patch.object(lane_run, "LANES", self.root / ".work/lanes"),
              patch.object(lane_run, "verify_source", return_value=fixture),
              patch.object(lane_run, "make_home", side_effect=home),
              patch.object(adapter, "_prewarm", side_effect=warmed_session)):
            paths = []
            for number in range(1, 9):
                paths.append(adapter.prepare("clojure", str(number)))
                session = lane_run.load(paths[-1])
                work, published = Path(session["work"]), Path(session["publish_source"])
                if number == 1:
                    (work / "src/continued.clj").write_text("(ns inherited-from-step-one)\n")
                else:
                    self.assertEqual((work / "src/continued.clj").read_text(), "(ns inherited-from-step-one)\n")
                for source in lane_run.product_files(work):
                    target = published / source.relative_to(work)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                lane_run.save(Path(session["result"]) / "verification.json", {"passed": True})
                if number in (3, 4):
                    kind = "perf" if number == 3 else "security"
                    lane_run.save(work / f".checks/{kind}/latest/results.json", {"baseline": number})
            paths.append(adapter.prepare("clojure", "one-shot"))
            self.assertEqual(len(warmed), 9)
            prompts = [f"steps/{lane_run.workdir.step_name(n)}.md" for n in range(1, 9)]
            for session, prompt in zip(warmed, [*prompts, "one-shot-v2-expert/PROMPT.md"]):
                work = Path(session["work"])
                self.assertEqual((work / "PROMPT.md").read_bytes(), (self.root / prompt).read_bytes())
                config = (Path(session["home"]) / "config.toml").read_text()
                for text in ('approval_policy = "never"', 'memories = false', 'multi_agent = false',
                             '":root" = "deny"', '"/var/run/docker.sock" = "deny"'):
                    self.assertIn(text, config)
                self.assertFalse(adapter.used(session))
                self.assertTrue((work / "src/core.clj").is_file())
            self.assertEqual(len({session["home"] for session in warmed}), 9)
            self.assertFalse((Path(warmed[-1]["work"]) / "src/continued.clj").exists())
            before = {str(path): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
            adapter.prepare("clojure", "1")
            after = {str(path): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
            self.assertEqual(before, after)
            self.assertEqual(len(paths), 9)

    def test_used_session_cannot_gain_a_new_condition(self):
        work, logs, home, control = (self.root / part for part in ("app", "logs", "home", "control"))
        for folder in (work, logs, home, control):
            folder.mkdir()
        (logs / "events.jsonl").write_text("{}\n")
        (work / "FIXTURE.json").write_text('{"condition":"older-condition"}\n')
        session = {"stack": "clojure", "work": str(work), "logs": str(logs), "home": str(home)}
        path = control / "session.json"
        lane_run.save(path, session)
        original = (work / "FIXTURE.json").read_bytes()
        with self.assertRaisesRegex(RuntimeError, "used coding session"):
            adapter.establish_condition(path)
        self.assertEqual((work / "FIXTURE.json").read_bytes(), original)
        self.assertEqual(lane_run.load(path), session)

    def test_verification_requires_condition_identity_and_supports_references(self):
        record = {"sha256": "condition-hash"}
        fixture = {"condition": "prepared-clojure", "runtime_adapter": record}
        self.write("app/FIXTURE.json", json.dumps(fixture))
        session = {"stack": "clojure", "phase": "1-build", "work": str(self.root / "app"),
                   "broker_port": 49682, "effective_fixture_sha256": "condition-hash"}
        with patch.object(adapter, "identity", return_value=record):
            self.assertEqual(adapter.verify(session), record)
            for change in ({"broker_port": 49680}, {"effective_fixture_sha256": "wrong"}):
                with self.assertRaises(RuntimeError):
                    adapter.verify(dict(session, **change))
            fixture["condition"] = "unscored-reference-repair"
            self.write("app/FIXTURE.json", json.dumps(fixture))
            self.assertEqual(adapter.verify(dict(session, phase="reference")), record)
            with self.assertRaises(RuntimeError):
                adapter.verify(session)
            with self.assertRaises(ValueError):
                adapter.verify(dict(session, stack="go"))

    def test_subprocess_routes_and_restores_scope_without_touching_agent_command(self):
        targets = {"lane_broker.py": "broker", "lane_check.py": "check-worker", "bench/bench.py": "benchmark"}
        for relative, action in targets.items():
            argv = ["python", str(lane_run.ROOT / "tools" / relative), "--session", "example"]
            expected = ["python", str(adapter.ADAPTER), action, "--session", "example"]
            self.assertEqual(adapter.route_command(argv), expected)
            self.assertEqual(adapter.route_command(expected), expected)
        agent = ["codex", "exec", "-m", "gpt-6-sol", "-c", 'model_reasoning_effort="xhigh"']
        self.assertEqual(adapter.route_command(agent), agent)
        argv = ["python", str(lane_run.ROOT / "tools/lane_check.py"), "--session", "example"]
        with patch.object(adapter.subprocess, "Popen") as popen:
            with adapter.routed_processes():
                adapter.subprocess.Popen(argv, stdout="sentinel")
            popen.assert_called_once_with(adapter.route_command(argv), stdout="sentinel")
            self.assertIs(adapter.subprocess.Popen, popen)

    def test_tcp_readiness_in_broker_and_benchmark_worker(self):
        argv = ["docker", "exec", "db", "pg_isready", "-U", "agentmvc"]
        with patch.object(adapter, "_command", return_value=(0, "ready")) as command:
            self.assertEqual(adapter.command(argv, timeout=10), (0, "ready"))
            command.assert_called_once_with([*argv, "-h", "127.0.0.1"], timeout=10)
        explicit = [*argv, "--host=db"]
        self.assertEqual(adapter.tcp_argv(explicit), explicit)
        bench_args = ["image", "label", "/tmp/output"]

        def workload(path, run_name):
            self.assertEqual(Path(path), lane_run.ROOT / "tools/bench/bench.py")
            self.assertEqual(run_name, "__main__")
            self.assertEqual(adapter.sys.argv[1:], bench_args)
            adapter.subprocess.run(argv, capture_output=True)

        original_argv = copy.copy(adapter.sys.argv)
        with (patch.object(adapter.subprocess, "run") as run,
              patch.object(adapter.runpy, "run_path", side_effect=workload)):
            adapter.benchmark(bench_args)
            run.assert_called_once_with([*argv, "-h", "127.0.0.1"], capture_output=True)
            self.assertIs(adapter.subprocess.run, run)
        self.assertEqual(adapter.sys.argv, original_argv)

    def test_install_is_idempotent_and_does_not_install_oneshot_overrides(self):
        snapshot = (lane_run.prepare, lane_run.publish, lane_run.launch, lane_broker.command)
        adapter.install()
        self.assertEqual(snapshot, (lane_run.prepare, lane_run.publish, lane_run.launch, lane_broker.command))
        self.assertIs(lane_run.prepare, adapter.prepare)
        self.assertIs(lane_run.publish, adapter.publish)

    def test_repeated_check_retains_previous_result_and_log_bytes(self):
        session = {"result": str(self.root / "result"), "control": str(self.root / "control")}
        descriptor = self.write("control/session.json", json.dumps(session))
        prior = self.write("result/verification.json", '{"passed":false}\n').read_bytes()
        log = self.write("control/independent-development.log", "original failure\n")
        self.write("control/independent-production.log", "original production output\n")

        def recheck(path):
            self.assertEqual(path, descriptor)
            log.write_text("later result\n")
            return True

        with (patch.object(adapter, "verify"),
              patch.object(adapter, "_independently_check", side_effect=recheck)):
            self.assertTrue(adapter.independently_check(descriptor))
        self.assertEqual((self.root / "result/verification-attempts/01.json").read_bytes(), prior)
        archived = self.root / "control/independent-attempts/01"
        self.assertEqual((archived / "independent-development.log").read_text(), "original failure\n")
        self.assertEqual((archived / "independent-production.log").read_text(), "original production output\n")


if __name__ == "__main__":
    unittest.main()
