"""Aggregate a run_paired.py session: medians/ranges per config and same-round speedups. Usage: aggregate.py DIR TAG"""
import json, statistics as st, sys

B, TAG = sys.argv[1], sys.argv[2]
labels = ["rails-ref-1proc", "rails-ref-auto", f"cruby-{TAG}-1proc", f"compiled-{TAG}", f"compiled-{TAG}-k1"]
names = {"list_anonymous": "Anonymous article list", "list_signed_in": "Signed-in list", "list_by_tag": "List by tag",
         "feed": "Feed", "article": "Single article", "comments": "Comments", "tags": "Tags",
         "favorite_toggle": "Favorite toggle", "create_article": "Create article"}
data, meta = {}, {}
for l in labels:
    for r in range(1, 5):
        d = json.load(open(f"{B}/{l}/round{r}/results.json"))
        s = d["scenarios"]
        data[(l, r)] = {k: v["rps"] for k, v in s.items()}
        meta[(l, r)] = {"failed": sum(v["failed_checks"] for v in s.values()),
                        "foreign": [v.get("foreign_container_cpu_percent_max", 0) for v in s.values()],
                        "peak_mb": max(v.get("peak_memory_mb", 0) for v in s.values()),
                        "idle_mb": d.get("idle_memory_mb"),
                        "sql_list": s["list_anonymous"].get("sql_statements_per_request"),
                        "sql_article": s["article"].get("sql_statements_per_request"),
                        "p95_list": s["list_anonymous"].get("p95_ms")}
scen = list(names)
fmt = lambda v: f"{st.median(v):,.0f} [{min(v):,.0f}–{max(v):,.0f}]"
out = ["| Scenario | " + " | ".join(labels) + " |", "| --- |" + " ---: |" * len(labels)]
for s in scen:
    out.append(f"| {names[s]} | " + " | ".join(fmt([data[(l, r)][s] for r in range(1, 5)]) for l in labels) + " |")
out.append("")
out.append("| Scenario | compiled / rails-auto | compiled-k1 / rails-auto | compiled / rails-1proc |")
out.append("| --- | ---: | ---: | ---: |")
ratios = {}
for s in scen:
    def rr(a, b):
        v = [data[(a, r)][s] / data[(b, r)][s] for r in range(1, 5)]
        return v, f"{st.median(v):.1f}× [{min(v):.1f}–{max(v):.1f}]"
    a, fa = rr(f"compiled-{TAG}", "rails-ref-auto")
    k, fk = rr(f"compiled-{TAG}-k1", "rails-ref-auto")
    o, fo = rr(f"compiled-{TAG}", "rails-ref-1proc")
    ratios[s] = {"vs_auto": a, "k1_vs_auto": k, "vs_1proc": o}
    out.append(f"| {names[s]} | {fa} | {fk} | {fo} |")
fails = sum(m["failed"] for m in meta.values())
foreign = [f for m in meta.values() for f in m["foreign"]]
out.append("")
out.append(f"runs={len(data)} failed_checks={fails} foreign_cpu_percent min/median/max = "
           f"{min(foreign):.0f}/{st.median(foreign):.0f}/{max(foreign):.0f}")
for l in labels:
    ms = [meta[(l, r)] for r in range(1, 5)]
    out.append(f"{l}: idle MB {st.median([m['idle_mb'] for m in ms]):.1f}, peak MB {st.median([m['peak_mb'] for m in ms]):.1f}, "
               f"SQL/list {ms[0]['sql_list']}, SQL/article {ms[0]['sql_article']}, p95 list ms {st.median([m['p95_list'] for m in ms]):.1f}")
print("\n".join(out))
json.dump({"rps": {f"{l}|{r}": v for (l, r), v in data.items()}, "meta": {f"{l}|{r}": v for (l, r), v in meta.items()},
           "ratios": ratios}, open(f"{B}/aggregate.json", "w"), indent=1)
