"""Run small held-out evolution checks against the finished Servant image."""
import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

import one_shot

ROOT = one_shot.ROOT
RESULT = ROOT / "results/one-shot-v2-servant/pilot-1/diagnostics.json"
IMAGE = "agentmvc-v2-pilot-servant:final"
PORT = 18115


def command(*args, check=True):
    proc = subprocess.run(args, capture_output=True, text=True, timeout=120)
    if check and proc.returncode:
        raise RuntimeError(f"{args[0]} {args[1]} failed: {proc.stderr[-500:]}")
    return proc.stdout.strip()


def call(method, path, body=None, token=None):
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Token " + token
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        response = urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as error:
        response = error
    data = response.read()
    try:
        payload = json.loads(data) if data else None
    except json.JSONDecodeError:
        payload = None
    return response.status, payload


def main():
    if RESULT.exists():
        raise SystemExit(f"Result exists: {RESULT}")
    image_id = command("docker", "image", "inspect", "--format", "{{.Id}}", IMAGE)
    summary = json.loads((RESULT.parent / "runtime/summary.json").read_text())
    if image_id != summary["image_sha256"]:
        raise SystemExit("Diagnostic image differs from measured image")
    suffix = uuid.uuid4().hex[:10]
    net = f"agentmvc-v2-diagnostic-{suffix}"
    db = net + "-db"
    app = net + "-app"
    nonce = uuid.uuid4().hex[:12]
    output = {"condition": "held-out diagnostic, not frozen acceptance", "image_sha256": image_id,
              "started": datetime.now(timezone.utc).isoformat(), "checks": {}}
    try:
        command("docker", "network", "create", net)
        command("docker", "run", "-d", "--name", db, "--network", net, "--network-alias", "db",
                "-e", "POSTGRES_PASSWORD=conduit", "-e", "POSTGRES_DB=conduit", "postgres:17-alpine")
        for _ in range(100):
            if subprocess.run(["docker", "exec", db, "pg_isready", "-h", "127.0.0.1", "-U", "postgres", "-d", "conduit"],
                              capture_output=True, timeout=5).returncode == 0:
                break
            time.sleep(.1)
        else:
            raise RuntimeError("Diagnostic database did not become ready")
        command("docker", "run", "-d", "--name", app, "--network", net,
                "-p", f"127.0.0.1:{PORT}:8080",
                "-e", "DATABASE_URL=postgres://postgres:conduit@db:5432/conduit",
                "-e", "SECRET_KEY_BASE=" + "0123456789abcdef" * 8,
                "-e", "PORT=8080", IMAGE)
        for _ in range(100):
            try:
                if call("GET", "/health")[0] == 200:
                    break
            except Exception:
                time.sleep(.1)
        else:
            raise RuntimeError("Diagnostic app did not become ready")

        status, short = call("POST", "/api/users", {"user": {
            "username": "short_" + nonce, "email": f"short_{nonce}@example.test", "password": "short7c"}})
        output["checks"]["short_password_registration"] = {"status": status,
            "accepted": status == 201, "compared_with_update_minimum": 8}
        if status == 201:
            status, _ = call("POST", "/api/users/login", {"user": {
                "email": f"short_{nonce}@example.test", "password": "short7c"}})
            output["checks"]["short_password_login"] = {"status": status, "succeeded": status == 200}

        status, created = call("POST", "/api/users", {"user": {
            "username": "held_" + nonce, "email": f"held_{nonce}@example.test", "password": "password123"}})
        if status != 201:
            raise RuntimeError(f"Normal registration failed: {status}")
        token = created["user"]["token"]
        status, updated = call("PUT", "/api/user", {"user": {"email": f"held_new_{nonce}@example.test"}}, token)
        output["checks"]["email_update"] = {"status": status,
            "new_email_returned": updated.get("user", {}).get("email") == f"held_new_{nonce}@example.test" if isinstance(updated, dict) else False}
        status, _ = call("POST", "/api/users/login", {"user": {
            "email": f"held_new_{nonce}@example.test", "password": "password123"}})
        output["checks"]["updated_email_login"] = {"status": status, "succeeded": status == 200}
        status, article = call("POST", "/api/articles", {"article": {
            "title": "Read / ? # correctly", "description": "Held-out URL test", "body": "Body"}}, token)
        if status != 201:
            raise RuntimeError(f"Punctuated title article creation failed: {status}")
        slug = article["article"]["slug"]
        status, fetched = call("GET", "/api/articles/" + urllib.parse.quote(slug, safe=""))
        output["checks"]["punctuated_title_roundtrip"] = {"status": status,
            "title_matches": fetched.get("article", {}).get("title") == "Read / ? # correctly" if isinstance(fetched, dict) else False,
            "url_safe_slug": all(c not in slug for c in "/?#")}
    finally:
        command("docker", "rm", "-f", app, check=False)
        command("docker", "rm", "-f", db, check=False)
        command("docker", "network", "rm", net, check=False)
        output["finished"] = datetime.now(timezone.utc).isoformat()
        RESULT.parent.mkdir(parents=True, exist_ok=True)
        RESULT.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
