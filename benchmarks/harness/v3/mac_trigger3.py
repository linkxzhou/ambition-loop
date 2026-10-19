#!/usr/bin/env python3
"""Trigger eval: AGENTS.md lists the user's 4 other skills + <skill>; triggered = <skill>/SKILL.md read within MAXSTEPS.
usage: mac_trigger.py <skill>   env PAR=4 MAXSTEPS=5. Resumable. Output: ~/skev/ambition-loop/trigger/<skill>/"""
import concurrent.futures as cf, glob, json, os, re, shutil, subprocess, sys, time
S = "/Volumes/my/github/SimpleBase/skills"; SK = sys.argv[1]; MINI = "/tmp/miniagent"
ALL = ["andrew-translate", "design-taste", "simplify-code", "code-refactor", SK]
P = {s: f"{S}/{s}" for s in ALL}; P["ambition-loop"] = f"{S}/ambition-loop"; P["ambition-loop-zh"] = f"{S}/ambition-loop/ambition-loop-zh"
MODEL = os.environ.get("AGENT_MODEL", "glm-5.3-flash-external")
Q = json.load(open(f"{P[SK]}/evals/trigger-evals.json")); OUT = os.path.expanduser(f"~/skev/ambition-loop/trigger-v102/{SK}"); os.makedirs(OUT, exist_ok=True)
def desc(s): return re.search(r'^description:\s*"?(.*?)"?\s*$', open(f"{P[s]}/SKILL.md").read(), re.M).group(1)
AG = ("# Project agent notes\n\n## Available skills\nSkills are folders of instructions you can load on demand. When the user's task matches a skill's\n"
      "description, read that skill's SKILL.md with the read tool BEFORE doing anything else, then follow it.\nSkip skills that don't match.\n\n"
      + "".join(f"- name: {s}\n  path: .agents/skills/{s}/SKILL.md\n  description: {desc(s)}\n\n" for s in ALL))
def one(i, q):
    rf = f"{OUT}/q{i:02d}.json"
    if os.path.exists(rf): return json.load(open(rf))
    d = os.path.expanduser(f"~/skev-trigger/v102-{SK}/q{i:02d}"); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    open(f"{d}/AGENTS.md", "w").write(AG)
    for s in ALL: shutil.copytree(P[s], f"{d}/.agents/skills/{s}", ignore=shutil.ignore_patterns("evals", "scripts", "files", "*-workspace", "benchmarks", "ambition-loop-zh", ".git", "README.md", "LICENSE"))
    t0 = time.time()
    try: rc = subprocess.run([MINI, "--approval", "readonly", "--no-auto-goal", "--json", "--no-builtin-skills", "--max-steps", os.environ.get("MAXSTEPS", "5"), "--cwd", d, "-p", q["query"]], capture_output=True, text=True, timeout=400, stdin=subprocess.DEVNULL, env={**os.environ, "MINIAGENT_MODEL_NAME": MODEL}).returncode
    except subprocess.TimeoutExpired: rc = -9
    best = None
    for m in glob.glob(os.path.expanduser("~/.miniagent/*/*/meta.json")):
        try: meta = json.load(open(m))
        except Exception: continue
        if meta.get("cwd") == d and (best is None or meta["created_at"] > best[1]["created_at"]): best = (os.path.dirname(m), meta)
    reads = []
    if best:
        for l in open(f"{best[0]}/msgs.jsonl"):
            for tc in json.loads(l).get("tool_calls") or []:
                a = json.dumps(tc.get("function", tc).get("arguments"), ensure_ascii=False)
                for s in ALL:
                    if f".agents/skills/{s}/SKILL.md" in a and s not in reads: reads.append(s)
    trig = SK in reads
    r = {"i": i, "query": q["query"], "should_trigger": q["should_trigger"], "triggered": trig, "reads": reads, "correct": trig == q["should_trigger"], "rc": rc, "secs": round(time.time() - t0, 1)}
    json.dump(r, open(rf, "w"), indent=1, ensure_ascii=False); return r
with cf.ThreadPoolExecutor(int(os.environ.get("PAR", "4"))) as ex: rs = list(ex.map(lambda a: one(*a), enumerate(Q)))
pos = [r for r in rs if r["should_trigger"]]; neg = [r for r in rs if not r["should_trigger"]]
summ = {"skill": SK, "n": len(rs), "accuracy": round(sum(r["correct"] for r in rs) / len(rs), 3), "recall": f"{sum(r['triggered'] for r in pos)}/{len(pos)}",
        "false_triggers": f"{sum(r['triggered'] for r in neg)}/{len(neg)}", "misses": [(r["query"][:80], r["should_trigger"], r["reads"]) for r in rs if not r["correct"]]}
json.dump({"summary": summ, "results": rs}, open(f"{OUT}/summary.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(summ, ensure_ascii=False, indent=1))
