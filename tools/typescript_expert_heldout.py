"""Post-run probes against an isolated database and the measured production image.

This is reviewer code, never included in the agent fixture or scored source.
It intentionally sends a malformed WebSocket frame last, because the server may exit.
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import base64
import hashlib
import json
import os
import socket
import subprocess
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "results/one-shot-v2-typescript-expert/expert-1"
SOURCE = RESULT / "source"
OUTPUT = RESULT / "held-out.json"
IMAGE = "sha256:f50b766412e4898719f7247798caa5237bddec339212d6b0f0923ed512990bf9"
NETWORK = "agentmvc-ts-expert-heldout-net"
DB = "agentmvc-ts-expert-heldout-db"
APP = "agentmvc-ts-expert-heldout-app"
PORT = 4117
BASE = f"http://127.0.0.1:{PORT}"


def command(*args: str, timeout: float = 30, check: bool = True) -> str:
    proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if check and proc.returncode:
        raise RuntimeError(f"{args[0]} {args[1:3]} returned {proc.returncode}: {proc.stderr[-1000:]}")
    return proc.stdout.strip()


def source_digest() -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in SOURCE.rglob("*") if p.is_file()):
        digest.update(path.relative_to(SOURCE).as_posix().encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def response(method: str, path: str, body=None, *, token=None, key=None, timeout=15):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Token {token}"
    if key:
        headers["X-Share-Key"] = key
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as opened:
            status, content = opened.status, opened.read()
    except urllib.error.HTTPError as error:
        status, content = error.code, error.read()
    try:
        value = json.loads(content) if content else None
    except ValueError:
        value = content.decode(errors="replace")[:300]
    return {"status": status, "body": value}


def public(result):
    """Remove synthetic credentials from the recorded response."""
    if isinstance(result, dict):
        return {key: "[redacted]" if key in ("token", "key", "password_hash")
                else public(value) for key, value in result.items()}
    if isinstance(result, list):
        return [public(value) for value in result]
    return result


def article(title, token, *, body="Initial"):
    made = response("POST", "/api/articles", {
        "article": {"title": title, "description": "Diagnostic", "body": body}
    }, token=token)
    assert made["status"] == 201, public(made)
    return made["body"]["article"]


def sql(query: str) -> str:
    return command("docker", "exec", DB, "psql", "-XqAt", "-U", "agentmvc", "-d",
                   "agentmvc", "-c", query)


@contextmanager
def lock_row(query: str):
    process = subprocess.Popen(
        ["docker", "exec", "-i", DB, "psql", "-XqAt", "-U", "agentmvc", "-d", "agentmvc"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1,
    )
    try:
        assert process.stdin and process.stdout
        process.stdin.write(f"BEGIN;\n{query};\n\\echo LOCKED\n")
        process.stdin.flush()
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            line = process.stdout.readline().strip()
            if line == "LOCKED":
                break
            if process.poll() is not None:
                raise RuntimeError("database lock process exited before acquiring lock")
        else:
            raise TimeoutError("database lock acquisition timed out")
        yield
    finally:
        if process.poll() is None:
            process.stdin.write("COMMIT;\n")
            process.stdin.flush()
            process.stdin.close()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def blocked_updates(prefix: str) -> int:
    return int(sql("select count(*) from pg_stat_activity where pid <> pg_backend_pid() "
                   "and wait_event_type = 'Lock' and query ilike '" + prefix + "%'"))


def concurrent_calls(lock_query, wait_prefix, action):
    with ThreadPoolExecutor(max_workers=2) as pool:
        with lock_row(lock_query):
            futures = [pool.submit(action, number) for number in (1, 2)]
            deadline = time.monotonic() + 10
            blocked = 0
            while time.monotonic() < deadline:
                blocked = blocked_updates(wait_prefix)
                if blocked >= 2:
                    break
                if any(future.done() for future in futures):
                    break
                time.sleep(.05)
        # The row lock has been released. HTTP timeouts cap an unexpected wait.
        return blocked, [future.result(timeout=20) for future in futures]


def startup():
    assert command("docker", "image", "inspect", IMAGE, "--format", "{{.Id}}") == IMAGE
    command("docker", "network", "create", NETWORK)
    command("docker", "run", "-d", "--name", DB, "--network", NETWORK,
            "-e", "POSTGRES_USER=agentmvc", "-e", "POSTGRES_PASSWORD=agentmvc",
            "-e", "POSTGRES_DB=agentmvc",
            "postgres:17-alpine@sha256:742f40ea20b9ff2ff31db5458d127452988a2164df9e17441e191f3b72252193")
    for _ in range(100):
        if not subprocess.run(["docker", "exec", DB, "pg_isready", "-U", "agentmvc", "-d",
                               "agentmvc"], capture_output=True).returncode:
            break
        time.sleep(.1)
    command("docker", "run", "-d", "--name", APP, "--network", NETWORK,
            "-p", f"127.0.0.1:{PORT}:{PORT}",
            "-e", "DATABASE_URL=postgres://agentmvc:agentmvc@" + DB + ":5432/agentmvc",
            "-e", "SECRET_KEY_BASE=" + "d" * 64, "-e", f"PORT={PORT}", IMAGE)
    for _ in range(200):
        try:
            if response("GET", "/api/tags", timeout=1)["status"] == 200:
                return
        except Exception:
            pass
        if command("docker", "inspect", APP, "--format", "{{.State.Running}}") != "true":
            raise RuntimeError("diagnostic app exited during startup")
        time.sleep(.1)
    raise TimeoutError("diagnostic app did not become ready")


def cleanup():
    subprocess.run(["docker", "rm", "-f", APP, DB], capture_output=True, timeout=30)
    subprocess.run(["docker", "network", "rm", NETWORK], capture_output=True, timeout=30)


def malformed_websocket_frame(share_id):
    key = base64.b64encode(os.urandom(16)).decode()
    connection = socket.create_connection(("127.0.0.1", PORT), timeout=5)
    connection.settimeout(5)
    try:
        request = (f"GET /api/shares/{share_id}/live HTTP/1.1\r\n"
                   f"Host: 127.0.0.1:{PORT}\r\nUpgrade: websocket\r\n"
                   f"Connection: Upgrade\r\nSec-WebSocket-Version: 13\r\n"
                   f"Sec-WebSocket-Key: {key}\r\n\r\n")
        connection.sendall(request.encode())
        handshake = b""
        while b"\r\n\r\n" not in handshake and len(handshake) < 4096:
            handshake += connection.recv(4096)
        # Valid masked text frame with invalid UTF-8 payload. The ws receiver
        # emits an error before any JSON subscription callback is invoked.
        mask = b"\x01\x02\x03\x04"
        connection.sendall(b"\x81\x81" + mask + bytes([0xff ^ mask[0]]))
        time.sleep(1.0)
        running = command("docker", "inspect", APP, "--format", "{{.State.Running}}")
        try:
            health = response("GET", "/api/tags", timeout=2)["status"]
        except Exception:
            health = "connection failed"
        log_proc = subprocess.run(["docker", "logs", APP], capture_output=True, text=True,
                                  timeout=10)
        logs = log_proc.stdout + log_proc.stderr
        return {"handshake": handshake.split(b"\r\n", 1)[0].decode(errors="replace"),
                "container_running_after_frame": running == "true", "health_after_frame": health,
                "unhandled_error_in_log": "Unhandled 'error' event" in logs,
                "invalid_utf8_in_log": "Invalid WebSocket frame" in logs}
    finally:
        connection.close()


def main():
    before = source_digest()
    record = {
        "condition": "post-run-held-out-diagnostic",
        "source": "unchanged expert-1 snapshot; measured production image",
        "source_tree_sha256": before,
        "image_sha256": IMAGE,
        "reviewer_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "started": datetime.now(timezone.utc).isoformat(),
        "port": PORT,
        "probes": {},
    }
    try:
        startup()
        registration = response("POST", "/api/users", {"user": {
            "username": "heldout_ts", "email": "heldout_ts@example.test", "password": "password123"
        }})
        assert registration["status"] == 201, public(registration)
        token = registration["body"]["user"]["token"]

        first = article("Revision diagnostic", token)
        slug = first["slug"]
        zero = response("PUT", f"/api/articles/{slug}",
                        {"article": {"revision": 0, "body": "Zero should be stale"}}, token=token)
        negative = response("PUT", f"/api/articles/{slug}",
                            {"article": {"revision": -1, "body": "Negative should be stale"}}, token=token)
        current = response("GET", f"/api/articles/{slug}", token=token)
        record["probes"]["integer_revision_mismatch"] = {
            "zero": public(zero), "negative": public(negative),
            "revision_after": current["body"]["article"]["revision"],
            "expected": "409 stale for any unequal integer; no mutation",
        }

        padded = response("POST", "/api/articles", {"article": {
            "title": "  Padded title  ", "description": "  Padded description  ",
            "body": "  Padded body  "}}, token=token)
        assert padded["status"] == 201, public(padded)
        edited = response("PUT", f"/api/articles/{padded['body']['article']['slug']}", {
            "article": {"body": "  Edited body  "}}, token=token)
        record["probes"]["whitespace_preservation"] = {
            "created": {field: padded["body"]["article"][field]
                        for field in ("title", "description", "body")},
            "edited_body": edited["body"]["article"]["body"],
            "expected": "nonblank input text preserved verbatim",
        }

        racing = article("No revision concurrency", token)
        race_slug = racing["slug"]
        blocked, pair = concurrent_calls(
            f"select id from articles where slug = '{race_slug}' for update",
            "update articles set",
            lambda number: response("PUT", f"/api/articles/{race_slug}",
                                    {"article": {"body": f"Writer {number}"}}, token=token),
        )
        final = response("GET", f"/api/articles/{race_slug}", token=token)
        record["probes"]["concurrent_no_revision_updates"] = {
            "blocked_updates_before_release": blocked,
            "statuses": [item["status"] for item in pair],
            "bodies": [public(item["body"]) for item in pair],
            "final_revision": final["body"]["article"]["revision"],
            "final_body": final["body"]["article"]["body"],
            "expected": "both omitted-revision updates apply, revision advances twice",
        }

        shared = article("Concurrent share rotation", token)
        share_slug = shared["slug"]
        original = response("POST", f"/api/articles/{share_slug}/share", token=token)
        assert original["status"] == 201, public(original)
        original_id = original["body"]["share"]["id"]
        blocked, pair = concurrent_calls(
            f"select id from shares where id = '{original_id}' for update",
            "update shares set",
            lambda number: response("POST", f"/api/articles/{share_slug}/share", token=token),
        )
        active_count = int(sql("select count(*) from shares where revoked_at is null "
                               f"and article_id = (select id from articles where slug = '{share_slug}')"))
        statuses = [item["status"] for item in pair]
        record["probes"]["concurrent_share_rotation"] = {
            "blocked_rotations_before_release": blocked,
            "statuses": statuses,
            "responses": [public(item["body"]) for item in pair],
            "active_share_count": active_count,
            "expected": "each rotation completes without leaking a database uniqueness conflict; one active link",
        }

        record["probes"]["malformed_websocket_frame"] = malformed_websocket_frame(original_id)
        record["finished"] = datetime.now(timezone.utc).isoformat()
        record["source_tree_unchanged"] = source_digest() == before
        OUTPUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        print(json.dumps({key: value for key, value in record.items() if key != "probes"}, indent=2))
        for name, probe in record["probes"].items():
            print(name, json.dumps(probe, sort_keys=True)[:1000])
    except Exception as error:
        record["error"] = f"{type(error).__name__}: {error}"
        record["finished"] = datetime.now(timezone.utc).isoformat()
        record["source_tree_unchanged"] = source_digest() == before
        OUTPUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        raise
    finally:
        cleanup()


if __name__ == "__main__":
    main()
