#!/usr/bin/env python3
import glob, json, os, re, collections
H = os.path.expanduser("~/skev/ambition-loop")
out = {}
for sk in ["ambition-loop", "ambition-loop-zh"]:
    rows = collections.defaultdict(dict)
    for g in sorted(glob.glob(f"{H}/{sk}-workspace/iteration-3/eval-*/*/run-[0-9]*/grading.json")):
        p = g.split("/"); ev, cond, run = p[-4], p[-3], p[-2]
        d = json.load(open(g)); s = d["summary"]
        fails = [e["text"][:90] for e in d["expectations"] if not e["passed"]]
        rows[ev].setdefault(cond, []).append({"run": run, "passed": s["passed"], "total": s["total"], "rate": s["pass_rate"],
            "skill_read": d["execution_metrics"].get("skill_md_read"), "tools": d["execution_metrics"].get("total_tool_calls"),
            "secs": d["timing"].get("total_duration_seconds"), "attempt": d["timing"].get("attempt"), "fails": fails})
    out[sk] = rows
    print("==", sk)
    for ev in sorted(rows, key=lambda x: int(x.split("-")[1])):
        for cond in ["with_skill", "without_skill"]:
            for r in rows[ev].get(cond, []):
                print(f"{ev[:40]:40} {cond:13} {r['run']} {r['passed']}/{r['total']} read={r['skill_read']} tools={r['tools']} secs={r['secs']} att={r['attempt']}")
                for f in r["fails"]: print("      FAIL", f)
    for cond in ["with_skill", "without_skill"]:
        per = []; P = T = 0
        for ev in rows:
            rs = rows[ev].get(cond, [])
            if rs: per.append(sum(r["rate"] for r in rs) / len(rs)); P += sum(r["passed"] for r in rs); T += sum(r["total"] for r in rs)
        print(f"TOTAL {cond}: mean-of-cases {100*sum(per)/len(per):.1f}% over {len(per)} cases; assertions {P}/{T}")
json.dump(out, open(f"{H}/iteration3-summary.json", "w"), indent=1, ensure_ascii=False)
for sk in ["ambition-loop", "ambition-loop-zh"]:
    f = f"{H}/trigger-v102/{sk}/summary.json"
    if os.path.exists(f): print("TRIGGER", json.dumps(json.load(open(f))["summary"], ensure_ascii=False))
