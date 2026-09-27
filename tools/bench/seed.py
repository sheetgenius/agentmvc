"""Seed a RealWorld backend with identical data through its public API.

Usage: python3 seed.py BASE_URL OUT.json
Creates 50 users, 500 articles (3 of 20 tags each), 500 follows, 1,000 favorites and 1,000 comments,
all from a fixed random seed, and writes tokens and slugs for the load test to OUT.json.
"""
import json, random, sys, time, urllib.request

BASE, OUT = sys.argv[1].rstrip("/"), sys.argv[2]
USERS, ARTICLES_EACH, FOLLOWS_EACH, FAVORITES_EACH, COMMENTS_EACH = 50, 10, 10, 20, 2
TAGS = [f"tag{i:02d}" for i in range(20)]
rng = random.Random(20260927)


def call(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(BASE + path, data=data, method=method)
    request.add_header("Content-Type", "application/json")
    request.add_header("Accept", "application/json")
    if token:
        request.add_header("Authorization", f"Token {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        text = response.read()
        return json.loads(text) if text else None


started = time.time()
users = []
for i in range(USERS):
    user = call("POST", "/api/users", {"user": {"username": f"user{i:02d}", "email": f"user{i:02d}@bench.test",
                                                "password": "password123"}})["user"]
    users.append({"username": user["username"], "token": user["token"]})

slugs = []
for i, user in enumerate(users):
    for j in range(ARTICLES_EACH):
        article = call("POST", "/api/articles", {"article": {
            "title": f"Article {i:02d}-{j:02d} about benchmarks",
            "description": f"Description {i}-{j}",
            "body": ("Benchmark body text. " * 40).strip(),
            "tagList": rng.sample(TAGS, 3)}}, user["token"])["article"]
        slugs.append(article["slug"])

for i, user in enumerate(users):
    for other in rng.sample([u for u in users if u is not user], FOLLOWS_EACH):
        call("POST", f"/api/profiles/{other['username']}/follow", token=user["token"])
    for slug in rng.sample(slugs, FAVORITES_EACH):
        call("POST", f"/api/articles/{slug}/favorite", token=user["token"])

for slug in slugs:
    for _ in range(COMMENTS_EACH):
        commenter = rng.choice(users)
        call("POST", f"/api/articles/{slug}/comments", {"comment": {"body": "A benchmark comment."}}, commenter["token"])

json.dump({"users": users, "slugs": slugs, "tags": TAGS, "seed_seconds": round(time.time() - started, 1)},
          open(OUT, "w"))
print(f"seeded {len(users)} users, {len(slugs)} articles in {time.time() - started:.1f}s")
