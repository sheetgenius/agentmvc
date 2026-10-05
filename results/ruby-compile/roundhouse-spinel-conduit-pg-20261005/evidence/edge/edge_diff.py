#!/usr/bin/env python3
"""Edge-case differential for the v7 workaround reverts (not a frozen gate).

usage: edge_diff.py run IMAGE PORT OUT.json      # fresh PostgreSQL 17 + IMAGE, scripted requests
       edge_diff.py diff A.json B.json           # compare two runs (status + normalized JSON body)

Covers the code paths the v7 reverts touch: PUT /api/user bodies (UsersController#update), login blank
fields (blank?), article create tagList defaults (fetch), the login throttle (21st failure -> 429) and
LiveRooms is left to the gate's live protocol. Containers are named conduit-v7-edge-<port>-*.
"""
import json, subprocess, sys, time, urllib.request, urllib.error

SECRET = "0123456789abcdef" * 8


def sh(*args, check=True):
    p = subprocess.run(args, capture_output=True, text=True)
    if check and p.returncode:
        raise SystemExit(f"{args[:4]} failed: {p.stderr[-800:]}")
    return p.stdout.strip()


def req(port, method, path, body=None, token=None, raw=None, ip=None):
    data = raw.encode() if raw is not None else (json.dumps(body).encode() if body is not None else None)
    r = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data, method=method)
    r.add_header("Accept", "application/json")
    if data is not None:
        r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", "Token " + token)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            status, text = resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        status, text = e.code, e.read().decode()
    try:
        payload = json.loads(text) if text else None
    except ValueError:
        payload = {"_raw": text[:200]}
    return status, payload


def norm(x):
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            if k == "token":
                out[k] = "<token>" if isinstance(v, str) and v else v
            elif k in ("createdAt", "updatedAt", "publishedAt"):
                out[k] = "<ts>" if v else v
            elif k == "slug" and isinstance(v, str):
                out[k] = "<slug>"
            else:
                out[k] = norm(v)
        return out
    if isinstance(x, list):
        return [norm(v) for v in x]
    return x


def script(port):
    results = []
    def rec(name, method, path, body=None, token=None, raw=None):
        status, payload = req(port, method, path, body, token, raw)
        results.append({"name": name, "status": status, "body": norm(payload)})
        return status, payload

    rec("register_b", "POST", "/api/users", {"user": {"username": "bob", "email": "bob@example.com", "password": "password123"}})
    updates = [
        ("bio_string", {"user": {"bio": "hello"}}), ("bio_null", {"user": {"bio": None}}),
        ("bio_empty", {"user": {"bio": ""}}), ("image_number", {"user": {"image": 123}}),
        ("bio_true", {"user": {"bio": True}}), ("bio_false", {"user": {"bio": False}}),
        ("bio_float", {"user": {"bio": 1.5}}), ("bio_hash", {"user": {"bio": {"a": 1}}}),
        ("bio_array", {"user": {"bio": ["x"]}}), ("empty_user", {"user": {}}),
        ("unwrapped_bio", {"bio": "unwrapped"}), ("unknown_key", {"user": {"admin": True, "bio": "k"}}),
        ("username_null", {"user": {"username": None}}), ("username_empty", {"user": {"username": ""}}),
        ("email_spaces", {"user": {"email": "   "}}), ("username_taken", {"user": {"username": "BOB"}}),
        ("email_taken", {"user": {"email": "Bob@Example.com"}}),
        ("password_short", {"user": {"password": "short"}}), ("password_empty", {"user": {"password": ""}}),
        ("password_null", {"user": {"password": None}}), ("password_number", {"user": {"password": 123456789}}),
        ("multi", {"user": {"username": "multi2", "bio": "b", "image": "http://i/x.png"}}),
        ("password_change", {"user": {"password": "newpassword1"}}),
        ("user_not_object", {"user": "x"}),
    ]
    # Each case on its own fresh user, so one case's outcome cannot leak into the next.
    for i, (name, body) in enumerate(updates):
        email = f"u{i}@example.com"
        _, reg = req(port, "POST", "/api/users", {"user": {"username": f"u{i}", "email": email, "password": "password123"}})
        tok = reg["user"]["token"]
        rec("update_" + name, "PUT", "/api/user", body, tok)
        rec("after_" + name, "GET", "/api/user", None, tok)
        for pw in ("password123", "newpassword1", "123456789"):
            rec(f"login_{name}_{pw}", "POST", "/api/users/login", {"user": {"email": email, "password": pw}})
    _, reg = req(port, "POST", "/api/users", {"user": {"username": "alice", "email": "alice@example.com", "password": "password123"}})
    tok = reg["user"]["token"]
    rec("update_malformed", "PUT", "/api/user", None, tok, raw='{"user": {"bio": ')
    blanks = [("email_empty", {"email": "", "password": "x"}), ("email_spaces", {"email": "  ", "password": "x"}),
              ("email_null", {"email": None, "password": "x"}), ("email_false", {"email": False, "password": "x"}),
              ("email_true", {"email": True, "password": "x"}), ("email_zero", {"email": 0, "password": "x"}),
              ("email_array", {"email": [], "password": "x"}), ("email_hash", {"email": {}, "password": "x"}),
              ("email_tab_newline", {"email": "\t\n", "password": "x"}), ("email_missing", {"password": "x"}),
              ("password_empty", {"email": "alice@example.com", "password": ""}),
              ("password_array1", {"email": "alice@example.com", "password": ["x"]}),
              ("both_blank", {"email": "", "password": ""})]
    for name, body in blanks:
        rec("login_" + name, "POST", "/api/users/login", {"user": body})
    article = {"title": "T", "description": "D", "body": "B"}
    creates = [("no_tags", {}), ("tags_dup", {"tagList": ["a", "a", "b"]}), ("tags_empty", {"tagList": []}),
               ("tags_null", {"tagList": None}), ("tags_string", {"tagList": "x"}), ("tags_int", {"tagList": [1]}),
               ("draft_no_tags", {"status": "draft"}), ("status_bad", {"status": "x"})]
    for i, (name, extra) in enumerate(creates):
        body = dict(article, title=f"T{i}", **extra)
        rec("create_" + name, "POST", "/api/articles", {"article": body}, tok)
    for i in range(23):
        rec(f"throttle_{i + 1:02d}", "POST", "/api/users/login", {"user": {"email": "throttle@example.com", "password": "wrong"}})
    return results


def run(image, port, out):
    port = int(port)
    label = f"conduit-v7-edge-{port}"
    net, db, app = label + "-net", label + "-db", label + "-app"
    record = {"image": image, "image_id": sh("docker", "image", "inspect", "--format", "{{.Id}}", image)}
    try:
        sh("docker", "network", "create", net)
        sh("docker", "run", "-d", "--name", db, "--network", net, "--network-alias", "db", "--cpus=2", "--memory=1g",
           "-e", "POSTGRES_PASSWORD=postgres", "-e", "POSTGRES_DB=conduit", "postgres:17-alpine")
        for _ in range(120):
            if subprocess.run(["docker", "exec", db, "pg_isready", "-h", "127.0.0.1", "-U", "postgres", "-d", "conduit"],
                              capture_output=True).returncode == 0:
                break
            time.sleep(.5)
        sh("docker", "run", "-d", "--name", app, "--network", net, "--cpus=2", "--memory=1g", "-p", f"127.0.0.1:{port}:8080",
           "-e", "DATABASE_URL=postgres://postgres:postgres@db:5432/conduit", "-e", "SECRET_KEY_BASE=" + SECRET,
           "-e", "PORT=8080", image)
        for _ in range(360):
            try:
                if req(port, "GET", "/api/tags")[0] == 200:
                    break
            except Exception:
                pass
            time.sleep(.5)
        record["results"] = script(port)
        record["app_log_tail"] = sh("docker", "logs", "--tail", "40", app, check=False)
    finally:
        subprocess.run(["docker", "rm", "-f", "-v", app, db], capture_output=True)
        subprocess.run(["docker", "network", "rm", net], capture_output=True)
    json.dump(record, open(out, "w"), indent=1)
    print(f"{out}: {len(record.get('results', []))} requests")


def diff(a, b):
    A, B = json.load(open(a)), json.load(open(b))
    ra, rb = {r["name"]: r for r in A["results"]}, {r["name"]: r for r in B["results"]}
    n = 0
    for name in ra:
        x, y = ra[name], rb.get(name)
        if y is None or x["status"] != y["status"] or x["body"] != y["body"]:
            n += 1
            print(f"DIFF {name}: {x['status']} {json.dumps(x['body'])[:160]}\n     vs {y and y['status']} {json.dumps(y and y['body'])[:160]}")
    print(f"{n} of {len(ra)} differ ({A['image']} vs {B['image']})")


if __name__ == "__main__":
    {"run": run, "diff": diff}[sys.argv[1]](*sys.argv[2:])
