#!/usr/bin/env python3
"""Exercise the product-free Clojure foundation in a disposable source copy."""
import argparse
import fcntl
import hashlib
import json
import re
import shutil
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAFFOLD = ROOT / "stacks/clojure/scaffold"
WORK = ROOT / ".work/clojure-track-preflight"
OUT = ROOT / "results/lanes/clojure"
IMAGE = "agentmvc-clojure-toolchain:preflight"
PRODUCTION = "agentmvc-clojure-preflight:production"
NETWORK = "agentmvc-clojure-preflight"
DB = NETWORK + "-db"
SERVER = NETWORK + "-app"
PORT = 4112
URL = "postgres://agentmvc:agentmvc@db:5432/agentmvc?sslmode=disable"
SECRET = "agentmvc-synthetic-preflight-secret"

TEST = r'''(ns conduit.preflight-test
  (:require [buddy.hashers :as hashers]
            [buddy.sign.jwt :as jwt]
            [clojure.test :refer [deftest is]]
            [conduit.database :as database]
            [conduit.migrations :as migrations]
            [conduit.queue :as queue]
            [honey.sql :as sql]
            [malli.core :as malli]
            [muuntaja.core :as muuntaja]
            [reitit.coercion.malli :as rc]
            [reitit.ring :as ring]
            [reitit.ring.coercion :as coercion]
            [reitit.ring.middleware.exception :as exception]
            [reitit.ring.middleware.muuntaja :as format]
            [next.jdbc :as jdbc]
            [proletarian.job :as job]))

(defn scalar [ds statement]
  (-> (jdbc/execute-one! ds [statement]) vals first))

(deftest transaction-and-restarted-worker
  (with-open [ds (database/open-pool (System/getenv "DATABASE_URL"))]
    (dotimes [_ 2] (migrations/migrate! ds))
    (is (= 1 (scalar ds "SELECT count(*) FROM schema_migrations WHERE id=2")))
    (try
      (jdbc/with-transaction [tx ds]
        (jdbc/execute-one! tx (sql/format {:insert-into :preflight_events
                                          :values [{:value "rolled-back"}]}))
        (job/enqueue! tx :preflight/event {:value "rolled-back-job"})
        (throw (ex-info "intentional rollback" {})))
      (catch clojure.lang.ExceptionInfo _))
    (is (zero? (scalar ds "SELECT count(*) FROM preflight_events")))
    (is (zero? (scalar ds "SELECT count(*) FROM proletarian.job")))
    (jdbc/with-transaction [tx ds]
      (jdbc/execute-one! tx (sql/format {:insert-into :preflight_events
                                        :values [{:value "committed"}]}))
      (job/enqueue! tx :preflight/event {:value "committed-job"}))
    (is (= 1 (scalar ds "SELECT count(*) FROM preflight_events")))
    (is (= 1 (scalar ds "SELECT count(*) FROM proletarian.job")))
    (let [handle (fn [_ {:keys [value]}]
                   (jdbc/execute-one! ds (sql/format {:insert-into :preflight_events
                                                      :values [{:value value}]})))
          worker (queue/start! (queue/create-worker ds handle))]
      (try
        (loop [n 100]
          (when (and (pos? n) (zero? (scalar ds "SELECT count(*) FROM preflight_events WHERE value='committed-job'")))
            (Thread/sleep 50)
            (recur (dec n))))
        (is (= 1 (scalar ds "SELECT count(*) FROM preflight_events WHERE value='committed-job'")))
        (finally (queue/stop! worker)))
      (jdbc/with-transaction [tx ds]
        (job/enqueue! tx :preflight/event {:value "after-worker-stop"}))
      (let [restarted (queue/start! (queue/create-worker ds handle))]
        (try
          (loop [n 100]
            (when (and (pos? n) (zero? (scalar ds "SELECT count(*) FROM preflight_events WHERE value='after-worker-stop'")))
              (Thread/sleep 50)
              (recur (dec n))))
          (is (= 1 (scalar ds "SELECT count(*) FROM preflight_events WHERE value='after-worker-stop'")))
          (finally (queue/stop! restarted)))))))

(deftest boundary-and-auth-libraries
  (is (malli/validate [:map {:closed true} [:name :string]] {:name "probe"}))
  (is (not (malli/validate [:map {:closed true} [:name :string]] {:name "probe" :extra 1})))
  (let [encoded (hashers/derive "synthetic-password" {:alg :argon2id})]
    (is (:valid (hashers/verify "synthetic-password" encoded)))
    (is (false? (:valid (hashers/verify "wrong" encoded)))))
  (let [secret (System/getenv "SECRET_KEY_BASE")
        token (jwt/sign {:sub "probe" :exp (+ 60 (quot (System/currentTimeMillis) 1000))}
                        secret {:alg :hs256})]
    (is (= "probe" (:sub (jwt/unsign token secret {:alg :hs256}))))
    (is (thrown? Exception (jwt/unsign token secret {:alg :hs512})))
    (is (thrown? Exception (jwt/unsign token "wrong-secret" {:alg :hs256})))
    (is (thrown? Exception
                 (jwt/unsign (jwt/sign {:sub "probe" :exp 1} secret {:alg :hs256})
                             secret {:alg :hs256})))))

(deftest reitit-strict-route-coercion
  (let [handler (ring/ring-handler
                 (ring/router
                   [["/probe" {:post {:parameters {:body [:map {:closed true} [:value :string]]}
                                     :handler (fn [_] {:status 200 :body {:accepted true}})}}]]
                   {:data {:muuntaja muuntaja/instance
                           :coercion (rc/create {:strip-extra-keys false})
                           :middleware [format/format-middleware
                                        (exception/create-exception-middleware
                                          (assoc exception/default-handlers
                                                 :reitit.coercion/request-coercion
                                                 (fn [_ _] {:status 422 :body {:errors {:body ["invalid"]}}})))
                                        coercion/coerce-request-middleware]}}))
        request (fn [body]
                  (handler {:request-method :post :uri "/probe"
                            :headers {"content-type" "application/json" "accept" "application/json"}
                            :body (java.io.ByteArrayInputStream. (.getBytes body "UTF-8"))}))]
    (is (= 200 (:status (request "{\"value\":\"probe\"}"))))
    (is (= 422 (:status (request "{\"value\":\"probe\",\"extra\":1}"))))
    (is (= 422 (:status (request "{\"value\":1}"))))))
'''

PROBE = r'''(ns conduit.preflight
  (:require [conduit.queue :as queue]
            [next.jdbc :as jdbc]
            [proletarian.job :as job]))

(defn start! [ds]
  (jdbc/with-transaction [tx ds]
    (job/enqueue! tx :preflight/event {:value "boot"}))
  (queue/start!
   (queue/create-worker ds
                        (fn [_ {:keys [value]}]
                          (jdbc/execute-one! ds ["INSERT INTO preflight_events(value) VALUES (?)" value])))))
'''


def scrub(value):
    value = value.replace(SECRET, "[REDACTED]").replace(URL, "postgres://[REDACTED]@db:5432/agentmvc")
    return re.sub(r"(postgres(?:ql)?://)[^\s/@]+:[^\s/@]+@", r"\1[REDACTED]@", value)


def command(args, logfile=None, check=True, timeout=900):
    print("preflight:", logfile or " ".join(args[:3]), flush=True)
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    output = scrub(result.stdout)
    if logfile:
        (OUT / ("preflight-" + logfile)).write_text(output)
    if check and result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(args[:3])}; see {logfile}\n{output[-3500:]}")
    return output.strip()


def container(*args, detached=False):
    return ["docker", "run", "-d" if detached else "--rm", "--cpus=2", "--memory=1g",
            "--network", NETWORK, "-e", f"DATABASE_URL={URL}", "-e", f"PORT={PORT}",
            "-e", f"SECRET_KEY_BASE={SECRET}", "-v", "agentmvc-clojure-m2:/root/.m2",
            "-v", "agentmvc-clojure-gitlibs:/root/.gitlibs", "-v", f"{WORK}:/work/app",
            "-w", "/work/app", *args]


def health(expected="ok", timeout=120):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2) as response:
                if json.load(response).get("status") == expected:
                    return
        except Exception:
            pass
        time.sleep(.1)
    raise RuntimeError(f"health did not become {expected}")


def socket_probe():
    script = f"const w=new WebSocket('ws://127.0.0.1:{PORT}/__preflight/socket');const p=JSON.stringify({{probe:'你好'}});const t=setTimeout(()=>process.exit(2),5000);w.onopen=()=>w.send(p);w.onmessage=e=>{{if(e.data!==p)process.exit(3);clearTimeout(t);w.close();}};w.onerror=()=>process.exit(4);"
    command(["node", "-e", script], timeout=10)


def sql(statement):
    return command(["docker", "exec", DB, "psql", "-U", "agentmvc", "-d", "agentmvc", "-Atc", statement])


def await_event(value, minimum=1):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if int(sql(f"SELECT count(*) FROM preflight_events WHERE value='{value}'")) >= minimum:
            return
        time.sleep(.1)
    raise RuntimeError(f"worker did not produce {value}")


def graceful_drain():
    def request():
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/__preflight/drain", timeout=10) as response:
            return response.read().decode()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(request)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if sql("SELECT count(*) FROM preflight_events WHERE value='draining'") == "1":
                break
            time.sleep(.02)
        else:
            raise RuntimeError("drain request did not start")
        command(["docker", "kill", "--signal=TERM", SERVER])
        if future.result() != "drained":
            raise RuntimeError("in-flight request failed during shutdown")
        exit_code = command(["docker", "wait", SERVER], timeout=20)
        if exit_code not in {"0", "143"}:
            raise RuntimeError(f"JVM shutdown failed: {exit_code}")
        return int(exit_code)


def scaffold_files():
    return {str(p.relative_to(SCAFFOLD)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(SCAFFOLD.rglob("*")) if p.is_file() and not any(x in p.parts for x in {".cpcache", "target", ".cache"})}


def add_probes():
    (WORK / "test/conduit/preflight_test.clj").write_text(TEST)
    (WORK / "src/conduit/preflight.clj").write_text(PROBE)
    (WORK / "resources/migrations/002-preflight.up.sql").write_text("CREATE TABLE preflight_events (value TEXT NOT NULL);\n")
    (WORK / "resources/migrations/002-preflight.down.sql").write_text("DROP TABLE preflight_events;\n")
    path = WORK / "src/conduit/http.clj"
    source = path.read_text().replace("(:require", "(:require [next.jdbc :as jdbc] [ring.websocket :as ws]")
    source = source.replace("[_data-source]", "[data-source]")
    needle = '[["/health" {:get (fn [_] {:status 200 :body {:status "ok"}})}]]'
    replacement = '''[["/health" {:get (fn [_] {:status 200 :body {:status "ok"}})}]
     ["/__preflight/socket" {:get (fn [_] {:ring.websocket/listener
                                          {:on-message (fn [socket message] (ws/send socket message))}})}]
     ["/__preflight/drain" {:get (fn [_]
                                    (jdbc/execute-one! data-source ["INSERT INTO preflight_events(value) VALUES ('draining')"])
                                    (Thread/sleep 600)
                                    (jdbc/execute-one! data-source ["SELECT 1"])
                                    {:status 200 :headers {"Content-Type" "text/plain"} :body "drained"})}]]'''
    if needle not in source:
        raise RuntimeError("health scaffold probe insertion point changed")
    path.write_text(source.replace(needle, replacement))
    path = WORK / "src/conduit/system.clj"
    source = path.read_text().replace("(:require", "(:require [conduit.preflight :as preflight] [conduit.queue :as queue]")
    source = source.replace("::handler {:database", "::worker {:database (ig/ref ::database) :migrations (ig/ref ::migrations)}\n     ::handler {:worker (ig/ref ::worker) :database")
    source += '''\n(defmethod ig/init-key ::worker [_ {:keys [database]}] (preflight/start! database))
(defmethod ig/halt-key! ::worker [_ worker] (queue/stop! worker))\n'''
    path.write_text(source)


def production_start():
    command(["docker", "run", "-d", "--name", SERVER, "--cpus=2", "--memory=1g", "--network", NETWORK,
             "-p", f"127.0.0.1:{PORT}:{PORT}", "-e", f"DATABASE_URL={URL}", "-e", f"PORT={PORT}",
             "-e", f"SECRET_KEY_BASE={SECRET}", PRODUCTION])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "preflight.json").exists():
        attempts = OUT / "preflight-attempts"
        attempts.mkdir(exist_ok=True)
        attempt = attempts / ("attempt-" + str(len(list(attempts.glob("attempt-*"))) + 1))
        attempt.mkdir()
        for previous in OUT.glob("preflight*"):
            if previous.is_file():
                shutil.copy2(previous, attempt / previous.name)
                previous.unlink()
    started = time.monotonic()
    record = {"passed": False, "condition": "product-free Clojure infrastructure preflight",
              "production_image": PRODUCTION, "checks": {},
              "application_limits": {"cpus": 2, "memory": "1g"}}
    original_files = scaffold_files()
    record["scaffold_files"] = original_files
    record["scaffold_sha256"] = hashlib.sha256(json.dumps(original_files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    record["probe"] = {"condition": "throwaway infrastructure fixtures only; excluded from scaffold",
                       "generator": "tools/clojure_track_preflight.py",
                       "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    lock = (ROOT / ".work/lane-docker.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX)
    try:
        if not args.skip_build:
            command(["docker", "build", "-t", IMAGE, "-f", str(ROOT / "stacks/clojure/Dockerfile.toolchain"), str(ROOT / "stacks/clojure")], "toolchain-build.log")
        record["toolchain_image_id"] = command(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"])
        shutil.rmtree(WORK, ignore_errors=True)
        shutil.copytree(SCAFFOLD, WORK, ignore=shutil.ignore_patterns(".cpcache", "target", ".cache"))
        command(["docker", "rm", "-f", SERVER, DB], check=False)
        command(["docker", "network", "rm", NETWORK], check=False)
        command(["docker", "network", "create", NETWORK])
        command(["docker", "run", "-d", "--name", DB, "--network", NETWORK, "--network-alias", "db",
                 "-e", "POSTGRES_USER=agentmvc", "-e", "POSTGRES_PASSWORD=agentmvc", "-e", "POSTGRES_DB=agentmvc", "postgres:17-alpine"])
        for _ in range(100):
            if "accepting connections" in command(["docker", "exec", DB, "pg_isready", "-U", "agentmvc"], check=False):
                break
            time.sleep(.1)
        else:
            raise RuntimeError("PostgreSQL did not become ready")
        command(container(IMAGE, "sh", "-c", "clojure -P -M:dev:test:lint:format && clojure -P -T:build && clojure -M:test && bin/lint"), "baseline.log")
        record["checks"]["clean_scaffold_tests_lint_and_prewarm"] = True
        scan = subprocess.run(container(IMAGE, "bin/dependency-scan"), text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
        (OUT / "preflight-dependency-scan.log").write_text(scrub(scan.stdout))
        if scan.returncode not in {0, 1}:
            raise RuntimeError(f"dependency scanner failed ({scan.returncode}): {scrub(scan.stdout[-2500:])}")
        for filename in ("resolved-basis.edn", "resolved-artifacts.json", "resolved-osv.json", "dependency-scan.json"):
            output = WORK / "target" / filename
            if not output.exists():
                raise RuntimeError(f"dependency scan did not produce {filename}")
            (OUT / ("preflight-" + filename)).write_text(scrub(output.read_text()))
        inventory = json.loads((WORK / "target/resolved-artifacts.json").read_text())
        jetty = [item for item in inventory["artifacts"]
                 if item["library"].startswith("org.eclipse.jetty")
                 and not item["library"].startswith("org.eclipse.jetty.toolchain/")]
        crypto = [item for item in inventory["artifacts"] if item["library"].startswith("org.bouncycastle/")]
        if not jetty or any(item["version"] != "12.1.13" for item in jetty):
            raise RuntimeError("Jetty runtime artifacts do not share the pinned 12.1.13 release")
        if len(crypto) != 3 or any(item["version"] != "1.86" for item in crypto):
            raise RuntimeError("Bouncy Castle runtime artifacts do not share the pinned 1.86 release")
        record["checks"]["coherent_patched_jetty_and_bouncycastle_runtime_graph"] = True
        record["dependency_scan"] = {"scanner": "OSV-Scanner 2.6.0", "exit_code": scan.returncode,
                                     "scope": "resolved production runtime Maven/Clojars dependencies",
                                     "dedicated_clojure_sast": "not configured",
                                     "reachability": "unsupported"}
        scan_report = json.loads((WORK / "target/dependency-scan.json").read_text())
        findings = [package for result in scan_report.get("results", [])
                    for package in result.get("packages", []) if package.get("vulnerabilities")]
        record["dependency_scan"]["vulnerable_packages"] = len(findings)
        record["dependency_scan"]["advisory_ids"] = sorted({item["id"] for package in findings
                                                           for item in package["vulnerabilities"]})
        record["checks"]["resolved_runtime_inventory_and_osv_scan_completed"] = True
        add_probes()
        command(container(IMAGE, "clojure", "-M:test"), "infrastructure-tests.log")
        record["checks"]["migration_repeat_honeysql_transaction_commit_rollback_auth_validation_worker_restart"] = True
        command(container("--name", SERVER, "-p", f"127.0.0.1:{PORT}:{PORT}", IMAGE, "bin/dev", detached=True))
        health(); socket_probe(); await_event("boot")
        record["checks"]["development_http_raw_websocket_queue"] = True
        source = WORK / "src/conduit/http.clj"
        before = source.read_text()
        reload_start = time.monotonic()
        source.write_text(before.replace(':status "ok"', ':status "reloaded"'))
        health("reloaded", timeout=30)
        record["reload_seconds"] = round(time.monotonic() - reload_start, 3)
        socket_probe()
        source.write_text(before)
        health(timeout=30)
        record["checks"]["live_reload_and_socket_after_reload"] = True
        command(["docker", "stop", "--time", "20", SERVER])
        command(["docker", "logs", SERVER], "development.log")
        command(["docker", "rm", SERVER])
        command(["docker", "build", "-t", PRODUCTION, str(WORK)], "production-build.log")
        sql("DROP SCHEMA proletarian CASCADE; DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        production_start()
        health(); socket_probe(); await_event("boot")
        record["checks"]["fresh_production_migration_http_socket_queue"] = True
        record["production_signal_exit_code"] = graceful_drain()
        record["checks"]["production_graceful_drain"] = True
        command(["docker", "logs", SERVER], "production.log")
        command(["docker", "rm", SERVER])
        enqueue = '''(require '[conduit.database :as db] '[next.jdbc :as jdbc] '[proletarian.job :as job])
(with-open [ds (db/open-pool (System/getenv "DATABASE_URL"))]
 (jdbc/with-transaction [tx ds] (job/enqueue! tx :preflight/event {:value "after-process-restart"})))'''
        command(container(IMAGE, "clojure", "-M", "-e", enqueue), "durable-enqueue.log")
        if sql("SELECT count(*) FROM proletarian.job") != "1":
            raise RuntimeError("job did not persist while application was stopped")
        production_start()
        health(); await_event("after-process-restart"); socket_probe()
        record["checks"]["durable_job_survives_application_process_restart"] = True
        record["production_image_id"] = command(["docker", "image", "inspect", PRODUCTION, "--format", "{{.Id}}"])
        record["production_image_bytes"] = int(command(["docker", "image", "inspect", PRODUCTION, "--format", "{{.Size}}"] ))
        record["production_user"] = command(["docker", "image", "inspect", PRODUCTION, "--format", "{{.Config.User}}"])
        if record["production_user"] != "10001:10001":
            raise RuntimeError("production image is not the expected nonroot user")
        record["checks"]["nonroot_aot_uberjar_three_runtime_settings"] = True
        record["versions"] = command(container(IMAGE, "sh", "-c", "java -version && clojure -Sdescribe && clojure -Stree"), "versions.log").splitlines()
        current = scaffold_files()
        if current != original_files:
            raise RuntimeError("scaffold changed during preflight; rerun before freeze")
        record["scaffold_files"] = current
        record["scaffold_sha256"] = hashlib.sha256(json.dumps(current, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        record["logs"] = sorted(p.name for p in OUT.glob("preflight-*.log"))
        record["passed"] = True
    except Exception as exc:
        record["error"] = scrub(str(exc))
        command(["docker", "logs", SERVER], "failure-server.log", check=False)
        raise
    finally:
        record["wall_seconds"] = round(time.monotonic() - started, 2)
        (OUT / "preflight.json").write_text(json.dumps(record, indent=2) + "\n")
        command(["docker", "rm", "-f", SERVER, DB], check=False)
        command(["docker", "network", "rm", NETWORK], check=False)
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()
    print(json.dumps({k: v for k, v in record.items() if k not in {"versions", "scaffold_files"}}, indent=2))


if __name__ == "__main__":
    main()
