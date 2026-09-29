"""Post-run diagnostic against a disposable production app on port 4120."""
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).with_name("held-out.json")
BASE = "http://127.0.0.1:4120/api"
APP = "agentmvc-phoenix-expert-reference-heldout"
DB = "agentmvc-one-shot-db-4120"
IMAGE = "agentmvc-phoenix-expert-reference:1"


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def request(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Token " + token
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        response = urllib.request.urlopen(req, timeout=20)
    except urllib.error.HTTPError as error:
        response = error
    raw = response.read().decode(errors="replace")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = raw
    return {"status": response.status, "body": payload}


def walk(plan):
    yield plan
    for child in plan.get("Plans", []):
        yield from walk(child)


def explain(sql):
    raw = command("docker", "exec", DB, "psql", "-X", "-A", "-t", "-q",
                  "-v", "ON_ERROR_STOP=1", "-U", "agentmvc", "-d", "agentmvc",
                  "-c", "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql)
    result = json.loads(raw)[0]
    nodes = list(walk(result["Plan"]))
    return {"planning_ms": result["Planning Time"], "execution_ms": result["Execution Time"],
            "nodes": [{"type": n["Node Type"], "relation": n.get("Relation Name"),
                       "actual_rows": n.get("Actual Rows"),
                       "rows_removed_by_filter": n.get("Rows Removed by Filter"),
                       "index": n.get("Index Name")}
                      for n in nodes], "raw": result}


def main():
    fixture = json.loads((ROOT / "one-shot-v2-phoenix-expert/fixture-manifest.json").read_text())
    snapshot = json.loads((OUT.parent / "source-hashes.json").read_text())
    image = command("docker", "image", "inspect", "--format", "{{.Id}}", IMAGE)
    try:
        subprocess.run([str(ROOT / "tools/one_shot_host/db.sh"), "start", "4120"],
                       check=True, capture_output=True)
        subprocess.run(["docker", "run", "-d", "--name", APP,
                        "--label", "agentmvc.one-shot=true", "--network", "host",
                        "-e", "DATABASE_URL=postgres://agentmvc:agentmvc@host.docker.internal:54120/agentmvc",
                        "-e", "SECRET_KEY_BASE=" + "0123456789abcdef" * 4,
                        "-e", "PORT=4120", IMAGE], check=True, capture_output=True)
        for _ in range(60):
            try:
                if urllib.request.urlopen("http://127.0.0.1:4120/health", timeout=2).status == 200:
                    break
            except urllib.error.URLError:
                time.sleep(.2)
        else:
            raise RuntimeError("Disposable production app did not start")
        users = []
        for name in ("probe_owner", "probe_stranger"):
            created = request("POST", "/users", {"user": {"username": name,
                "email": name + "@example.invalid", "password": "password123"}})
            assert created["status"] == 201, created
            users.append(created["body"]["user"]["token"])
        owner, stranger = users
        created = request("POST", "/articles", {"article": {"title": "Probe article",
            "description": "probe", "body": "probe", "tagList": ["probe_rare"]}}, owner)
        assert created["status"] == 201, created
        slug = created["body"]["article"]["slug"]
        malformed = {"article": "not an object"}
        valid = {"article": {"body": "new body"}}
        results = {
            "stranger_valid_update": request("PUT", "/articles/" + slug, valid, stranger),
            "stranger_malformed_update": request("PUT", "/articles/" + slug, malformed, stranger),
            "missing_valid_update": request("PUT", "/articles/missing-probe", valid, owner),
            "missing_malformed_update": request("PUT", "/articles/missing-probe", malformed, owner),
            "max_title_length": 255,
            "max_title_create": request("POST", "/articles", {"article": {
                "title": "a" * 255, "description": "probe", "body": "probe"}}, owner),
        }
        huge = "9" * 100
        results["huge_id_digits"] = len(huge)
        results["huge_export_id"] = request("GET", "/user/exports/" + huge, token=owner)
        results["huge_comment_id"] = request("DELETE", "/articles/" + slug + "/comments/" + huge,
                                              token=owner)
        uid = command("docker", "exec", DB, "psql", "-X", "-A", "-t", "-q", "-U",
                      "agentmvc", "-d", "agentmvc", "-c",
                      "SELECT id FROM users WHERE username='probe_owner'")
        seed = """INSERT INTO articles (author_id, slug, title, description, body, tag_list,
                  status, revision, published_at, inserted_at, updated_at)
                  SELECT %s, 'probe-seed-' || g, 'Seed ' || g, 'probe', 'probe',
                    CASE WHEN g %% 100 = 0 THEN ARRAY['probe_rare'] ELSE ARRAY['probe_common'] END,
                    'published', 1, now(), now(), now() FROM generate_series(1, 10000) g""" % uid
        command("docker", "exec", DB, "psql", "-X", "-q", "-v", "ON_ERROR_STOP=1",
                "-U", "agentmvc", "-d", "agentmvc", "-c", seed)
        command("docker", "exec", DB, "psql", "-X", "-q", "-U", "agentmvc", "-d",
                "agentmvc", "-c", "ANALYZE articles")
        predicate = "status = 'published' AND tag_list @> ARRAY['probe_rare']::varchar[]"
        results["tag_count_explain"] = explain("SELECT count(id) FROM articles WHERE " + predicate)
        results["tag_page_explain"] = explain("SELECT id FROM articles WHERE " + predicate +
            " ORDER BY inserted_at DESC, id DESC LIMIT 20 OFFSET 0")
        results["tag_http"] = {"status": request("GET", "/articles?tag=probe_rare")["status"]}
        output = {"condition": "unscored post-run diagnostic", "fixture_sha256": fixture["sha256"],
                  "origin_source_snapshot_sha256": snapshot["origin_source_snapshot_sha256"],
                  "reference_patch_sha256": snapshot["patch_sha256"], "image_sha256": image,
                  "seeded_articles": 10000, "results": results}
        OUT.write_text(json.dumps(output, indent=2) + "\n")
        print(json.dumps({"fixture_sha256": fixture["sha256"], "image_sha256": image,
                          "statuses": {key: value["status"] for key, value in results.items()
                                       if isinstance(value, dict) and "status" in value}}, indent=2))
    finally:
        subprocess.run(["docker", "rm", "-f", APP], capture_output=True)
        subprocess.run([str(ROOT / "tools/one_shot_host/db.sh"), "stop", "4120"], capture_output=True)


if __name__ == "__main__":
    main()
