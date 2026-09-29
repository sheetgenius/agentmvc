"""Prove the product-free Go toolchain in disposable copies, before any agent run."""
import hashlib
import json
import shutil
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAFFOLD = ROOT / "stacks/go/scaffold"
WORK = ROOT / ".work/go-track-preflight"
OUT = ROOT / "results/lanes/go"
IMAGE = "agentmvc-go-toolchain:preflight"
PRODUCTION = "agentmvc-go-preflight:production"
NETWORK = "agentmvc-go-preflight"
DB = "agentmvc-go-preflight-db"
SERVER = "agentmvc-go-preflight-app"
URL = "postgres://agentmvc:agentmvc@db:5432/agentmvc?sslmode=disable"
PORT = 4110

TEST = r'''package platform

import (
    "context"
    "database/sql"
    "net/http"
    "net/http/httptest"
    "os"
    "strings"
    "testing"
    "time"

    "github.com/coder/websocket"
    "github.com/golang-jwt/jwt/v5"
    "github.com/riverqueue/river"
    "golang.org/x/crypto/bcrypt"
)

type probeArgs struct { Value string `json:"value"` }
func (probeArgs) Kind() string { return "agentmvc_preflight" }
type probeWorker struct { river.WorkerDefaults[probeArgs]; db *sql.DB }
func (w *probeWorker) Work(ctx context.Context, job *river.Job[probeArgs]) error {
    _, err := w.db.ExecContext(ctx, "INSERT INTO preflight_events (value) VALUES ($1)", job.Args.Value)
    return err
}

func TestPreflightDatabaseAndDurableQueue(t *testing.T) {
    ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
    defer cancel()
    db, err := Open(ctx, os.Getenv("DATABASE_URL")); if err != nil { t.Fatal(err) }; defer db.Close()
    for range 2 { if err := Migrate(ctx, db.DB); err != nil { t.Fatal(err) } }
    _, err = db.ExecContext(ctx, "CREATE TABLE preflight_events (value text NOT NULL)")
    if err != nil { t.Fatal(err) }
    workers := river.NewWorkers(); river.AddWorker(workers, &probeWorker{db: db.DB})
    client, closeListener, err := Queue(ctx, db.DB, os.Getenv("DATABASE_URL"), workers)
    if err != nil { t.Fatal(err) }; defer closeListener()
    tx, err := db.BeginTx(ctx, nil); if err != nil { t.Fatal(err) }
    if _, err := client.InsertTx(ctx, tx.Tx, probeArgs{Value: "rolled-back"}, nil); err != nil { t.Fatal(err) }
    if err := tx.Rollback(); err != nil { t.Fatal(err) }
    var count int
    if err := db.QueryRowContext(ctx, "SELECT count(*) FROM river_job WHERE kind='agentmvc_preflight'").Scan(&count); err != nil || count != 0 { t.Fatalf("rollback count=%d err=%v", count, err) }
    tx, err = db.BeginTx(ctx, nil); if err != nil { t.Fatal(err) }
    if _, err := client.InsertTx(ctx, tx.Tx, probeArgs{Value: "committed"}, nil); err != nil { t.Fatal(err) }
    if err := tx.Commit(); err != nil { t.Fatal(err) }
    if err := db.QueryRowContext(ctx, "SELECT count(*) FROM river_job WHERE kind='agentmvc_preflight'").Scan(&count); err != nil || count != 1 { t.Fatalf("persisted count=%d err=%v", count, err) }
    if err := client.Start(ctx); err != nil { t.Fatal(err) }
    defer func() { if err := client.Stop(ctx); err != nil { t.Error(err) } }()
    deadline := time.Now().Add(10*time.Second)
    for time.Now().Before(deadline) {
        err := db.QueryRowContext(ctx, "SELECT count(*) FROM preflight_events WHERE value='committed'").Scan(&count)
        if err != nil { t.Fatal(err) }; if count == 1 { return }; time.Sleep(25*time.Millisecond)
    }
    t.Fatal("committed job did not execute")
}

func TestPreflightRawSocket(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        c, err := websocket.Accept(w, r, nil); if err != nil { return }; defer c.CloseNow()
        typ, data, err := c.Read(r.Context()); if err == nil { _ = c.Write(r.Context(), typ, data) }
    })); defer server.Close()
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second); defer cancel()
    c, _, err := websocket.Dial(ctx, "ws"+strings.TrimPrefix(server.URL,"http"), nil)
    if err != nil { t.Fatal(err) }; defer c.CloseNow()
    if err := c.Write(ctx, websocket.MessageText, []byte(`{"probe":"你好"}`)); err != nil { t.Fatal(err) }
    _, payload, err := c.Read(ctx); if err != nil || string(payload) != `{"probe":"你好"}` { t.Fatalf("echo=%s err=%v",payload,err) }
}

func TestPreflightMaintainedAuthLibraries(t *testing.T) {
    hash, err := bcrypt.GenerateFromPassword([]byte("preflight-password"), bcrypt.MinCost)
    if err != nil || bcrypt.CompareHashAndPassword(hash, []byte("preflight-password")) != nil { t.Fatal("bcrypt round trip") }
    secret := []byte("synthetic-preflight-secret")
    encoded, err := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{"sub":"preflight"}).SignedString(secret)
    if err != nil { t.Fatal(err) }
    key := func(*jwt.Token) (any, error) { return secret, nil }
    token, err := jwt.Parse(encoded, key, jwt.WithValidMethods([]string{"HS256"}))
    if err != nil || !token.Valid { t.Fatal("JWT round trip",err) }
    if _, err := jwt.Parse(encoded, key, jwt.WithValidMethods([]string{"HS512"})); err == nil { t.Fatal("algorithm restriction not enforced") }
}
'''

PROBE = r'''package main

import (
    "context"
    "database/sql"
    "net/http"
    "os"
    "log/slog"
    "time"

    "conduit/internal/platform"
    "github.com/coder/websocket"
    "github.com/go-chi/chi/v5"
    "github.com/riverqueue/river"
    "github.com/uptrace/bun"
)
type bootArgs struct{}
func (bootArgs) Kind() string { return "agentmvc_boot_probe" }
type bootWorker struct { river.WorkerDefaults[bootArgs]; db *sql.DB }
func (w *bootWorker) Work(ctx context.Context, job *river.Job[bootArgs]) error {
    _, err := w.db.ExecContext(ctx, "INSERT INTO preflight_boot (value) VALUES ('completed')")
    return err
}
func preflight(ctx context.Context, router *chi.Mux, db *bun.DB) error {
    if _, err := db.ExecContext(ctx, "CREATE TABLE IF NOT EXISTS preflight_boot (value text NOT NULL)"); err != nil { return err }
    workers := river.NewWorkers(); river.AddWorker(workers, &bootWorker{db:db.DB})
    queue, closeListener, err := platform.Queue(ctx, db.DB, os.Getenv("DATABASE_URL"), workers)
    if err != nil { return err }
    if err := queue.Start(ctx); err != nil { closeListener(); return err }
    go func() { <-ctx.Done(); _ = queue.Stop(context.Background()); closeListener() }()
    if _, err := queue.Insert(ctx, bootArgs{}, nil); err != nil { return err }
    router.Get("/__preflight/socket", func(w http.ResponseWriter, r *http.Request) {
        c, err := websocket.Accept(w,r,nil); if err != nil { slog.Error("socket accept", "error", err); return }; defer c.Close(websocket.StatusNormalClosure,"probe complete")
        typ, payload, err := c.Read(r.Context()); if err == nil { err = c.Write(r.Context(),typ,payload) }; if err != nil { slog.Error("socket echo", "error", err) }
    })
    router.Get("/__preflight/drain", func(w http.ResponseWriter, r *http.Request) {
        _, _ = db.ExecContext(r.Context(), "INSERT INTO preflight_boot (value) VALUES ('draining')")
        time.Sleep(300*time.Millisecond)
        if err := db.PingContext(r.Context()); err != nil { http.Error(w,err.Error(),500); return }
        _, _ = w.Write([]byte("drained"))
    })
    return nil
}
'''

def command(args, logfile=None, check=True, timeout=600):
    if logfile:
        with (OUT / logfile).open("w") as stream:
            result = subprocess.run(args, text=True, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
        result.stdout = (OUT / logfile).read_text()
    else:
        result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(args[:5])}; see {logfile}\n{result.stdout[-2500:]}")
    return result.stdout.strip()

def container(*args, detached=False):
    return ["docker", "run", "-d" if detached else "--rm", "--cpus=2", "--network", NETWORK,
            "-e", f"DATABASE_URL={URL}", "-e", f"PORT={PORT}",
            "-e", "SECRET_KEY_BASE=agentmvc-synthetic-preflight-secret", "-e", "GOFLAGS=-p=2",
            "-e", "GOMAXPROCS=2", "-v", "agentmvc-go-mod:/go/pkg/mod",
            "-v", "agentmvc-go-build:/root/.cache/go-build", "-v", f"{WORK}:/work/app",
            "-w", "/work/app", *args]

def health(expected="ok"):
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2) as response:
                if json.load(response).get("status") == expected:
                    return
        except Exception:
            pass
        time.sleep(0.1)
    raise RuntimeError(f"health did not become {expected}")

def socket_probe():
    script = "const w=new WebSocket('ws://127.0.0.1:4110/__preflight/socket'); const p=JSON.stringify({probe:'你好'}); const t=setTimeout(()=>process.exit(2),3000); w.onopen=()=>w.send(p); w.onmessage=e=>{if(e.data!==p)process.exit(3);clearTimeout(t);w.close();};w.onerror=e=>{console.error(e.error||e);process.exit(4);};"
    command(["node", "-e", script], timeout=10)

def sql(query):
    return command(["docker", "exec", DB, "psql", "-U", "agentmvc", "-d", "agentmvc", "-Atc", query])

def job_probe():
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if sql("SELECT count(*) FROM preflight_boot WHERE value='completed'") != "0":
            return
        time.sleep(.1)
    raise RuntimeError("server's queue did not execute boot probe")

def drain_probe():
    def request():
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/__preflight/drain", timeout=5) as response:
            return response.read().decode()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(request)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if sql("SELECT count(*) FROM preflight_boot WHERE value='draining'") == "1":
                break
            time.sleep(.02)
        else:
            raise RuntimeError("drain request did not start")
        command(["docker", "kill", "--signal=TERM", SERVER])
        if future.result() != "drained":
            raise RuntimeError("in-flight request did not finish with live database")
        if command(["docker", "wait", SERVER], timeout=15) != "0":
            raise RuntimeError("server did not shut down cleanly")

def scaffold_files():
    return {str(p.relative_to(SCAFFOLD)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(SCAFFOLD.rglob("*")) if p.is_file()}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    record = {"passed": False, "condition": "product-free Go infrastructure preflight",
              "production_image": PRODUCTION, "checks": {}}
    original_files = scaffold_files()
    command(["docker", "build", "-t", IMAGE, "-f", str(ROOT / "stacks/go/Dockerfile.toolchain"), str(ROOT / "stacks/go")], "toolchain-build.log")
    record["toolchain_image_id"] = command(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"])
    if WORK.exists():
        shutil.rmtree(WORK)
    shutil.copytree(SCAFFOLD, WORK)
    (WORK / "internal/platform/preflight_test.go").write_text(TEST)
    (WORK / "cmd/server/preflight.go").write_text(PROBE)
    mainfile = WORK / "cmd/server/main.go"
    mainfile.write_text(mainfile.read_text().replace("router := chi.NewRouter()", "router := chi.NewRouter()\n\tif err := preflight(ctx, router, db); err != nil { return err }"))
    command(["docker", "network", "create", NETWORK], check=False)
    command(["docker", "rm", "-f", SERVER, DB], check=False)
    try:
        command(["docker", "run", "-d", "--name", DB, "--network", NETWORK, "--network-alias", "db",
                 "-e", "POSTGRES_USER=agentmvc", "-e", "POSTGRES_PASSWORD=agentmvc", "-e", "POSTGRES_DB=agentmvc", "postgres:17-alpine"])
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if "accepting connections" in command(["docker", "exec", DB, "pg_isready", "-U", "agentmvc"], check=False):
                break
            time.sleep(.2)
        command(container(IMAGE, "sh", "-c", "gofmt -w cmd internal && go test -race -v ./... && go vet ./..."), "library-tests.log")
        record["checks"]["migrations_idempotent_queue_commit_rollback_socket_crypto_race"] = True
        command(container("--name", SERVER, "-p", f"127.0.0.1:{PORT}:{PORT}", IMAGE, "sh", "bin/dev", detached=True))
        health(); socket_probe(); job_probe()
        record["checks"]["development_http_socket_queue"] = True
        tick = time.monotonic()
        mainfile.write_text(mainfile.read_text().replace('out.Body.Status = "ok"', 'out.Body.Status = "reloaded"'))
        health("reloaded")
        record["reload_seconds"] = round(time.monotonic() - tick, 3)
        record["checks"]["development_reload"] = True
        command(["docker", "logs", SERVER], "development.log")
        command(["docker", "rm", "-f", SERVER])
        mainfile.write_text(mainfile.read_text().replace('out.Body.Status = "reloaded"', 'out.Body.Status = "ok"'))
        command(["docker", "build", "-t", PRODUCTION, str(WORK)], "production-build.log")
        sql("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        command(["docker", "run", "-d", "--name", SERVER, "--cpus=2", "--memory=1g", "--network", NETWORK,
                 "-p", f"127.0.0.1:{PORT}:{PORT}", "-e", f"DATABASE_URL={URL}", "-e", f"PORT={PORT}",
                 "-e", "SECRET_KEY_BASE=agentmvc-synthetic-preflight-secret", PRODUCTION])
        health(); socket_probe(); job_probe()
        record["checks"]["fresh_production_http_socket_queue"] = True
        drain_probe()
        record["checks"]["production_graceful_drain"] = True
        record["production_image_id"] = command(["docker", "image", "inspect", PRODUCTION, "--format", "{{.Id}}"])
        record["production_image_bytes"] = int(command(["docker", "image", "inspect", PRODUCTION, "--format", "{{.Size}}"] ))
        command(["docker", "logs", SERVER], "production.log")
        record["versions"] = command(container(IMAGE, "sh", "-c", "go version && go version -m /go/bin/air /go/bin/govulncheck /go/bin/gosec && go list -m all"), "versions.log").splitlines()
        files = scaffold_files()
        if files != original_files:
            raise RuntimeError("scaffold changed during preflight; rerun before freeze")
        record["scaffold_files"] = files
        record["scaffold_sha256"] = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        record["logs"] = sorted(p.name for p in OUT.glob("*.log"))
        record["passed"] = True
    except Exception as exc:
        record["error"] = str(exc)
        command(["docker", "logs", SERVER], "failure-server.log", check=False)
        raise
    finally:
        record["wall_seconds"] = round(time.monotonic() - started, 2)
        (OUT / "preflight.json").write_text(json.dumps(record, indent=2) + "\n")
        command(["docker", "rm", "-f", SERVER, DB], check=False)
        command(["docker", "network", "rm", NETWORK], check=False)
    print(json.dumps({k: v for k, v in record.items() if k not in {"versions", "scaffold_files"}}, indent=2))

if __name__ == "__main__":
    main()
