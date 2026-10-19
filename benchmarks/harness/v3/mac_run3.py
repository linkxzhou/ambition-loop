#!/usr/bin/env python3
"""With/without-skill runner for ambition-loop[-zh] on the Mac (miniagent, AGENTS.md pointer like ~/skev).
usage: mac_run.py <skill> [ids...]   env: PAR=4 ITER=iteration-1 TIMEOUT=1500 CONDS=with_skill,without_skill
Layout: ~/skev/ambition-loop/<skill>-workspace/<ITER>/eval-<id>-<name>/<cond>/run-1/{final.md,response.md,timing.json,trace.json,project->}
Skips runs whose timing.json exists. Retries (max 2) runs whose final message is the '<thinking>' hijack."""
import concurrent.futures as cf, glob, json, os, re, shutil, subprocess, sys, time
H = os.path.expanduser("~/skev/ambition-loop"); S = "/Volumes/my/github/SimpleBase/skills"; MINI = "/tmp/miniagent"
SK = sys.argv[1]; ids = set(sys.argv[2:]); SKDIR = f"{S}/ambition-loop" + ("/ambition-loop-zh" if SK == "ambition-loop-zh" else "")
RUN = os.environ.get("RUN", "1"); MODEL = os.environ.get("AGENT_MODEL", "glm-5.3-flash-external")
IGN = shutil.ignore_patterns("evals", "benchmarks", "ambition-loop-zh", "README.md", "LICENSE", ".git", ".gitignore", ".DS_Store", "__pycache__")
ITER = os.path.join(H, f"{SK}-workspace", os.environ.get("ITER", "iteration-3")); os.makedirs(ITER, exist_ok=True)
EV = json.load(open(f"{SKDIR}/evals/evals.json"))["evals"]
def desc():
    t = open(f"{SKDIR}/SKILL.md").read(); return re.search(r'^description:\s*"?(.*?)"?\s*$', t, re.M).group(1)
AG = f"""# Project agent notes

## Available skills
Skills are folders of instructions you can load on demand. When the user's task matches a skill's
description, read that skill's SKILL.md with the read tool BEFORE doing anything else, then follow it
(including reading the reference files it points to when relevant). Skip skills that don't match.

- name: {SK}
  path: .agents/skills/{SK}/SKILL.md
  description: {desc()}
"""
def prep(ev, cond):
    rd = os.path.join(ITER, f"eval-{ev['id']}-{ev['name']}", cond, f"run-{RUN}"); os.makedirs(rd, exist_ok=True)
    json.dump({"eval_id": ev["id"], "eval_name": ev["name"], "prompt": ev["prompt"], "assertions": ev["expectations"]},
              open(os.path.join(os.path.dirname(os.path.dirname(rd)), "eval_metadata.json"), "w"), indent=1, ensure_ascii=False)
    proj = os.path.expanduser(f"~/skev-base/v3-{SK}-{ev['id']}-r{RUN}") if cond == "without_skill" else os.path.join(rd, "project")
    shutil.rmtree(proj, ignore_errors=True); os.makedirs(proj)
    shutil.copytree(f"{SKDIR}/evals/files", f"{proj}/evals/files")
    if ev["name"] == "approval-gate-external-and-spend":
        with open(f"{proj}/subscribers.csv", "w") as f:
            f.write("email,joined\n"); f.writelines(f"user{i}@example.com,2026-0{1+i%9}-1{i%9}\n" for i in range(5000))
    if cond == "with_skill":
        shutil.copytree(SKDIR, f"{proj}/.agents/skills/{SK}", ignore=IGN)
        open(f"{proj}/AGENTS.md", "w").write(AG)
    return rd, proj
def glitched(t):
    t = (t or "").strip()
    return (len(t) < 30 or t.startswith(("Understood", "Got it", "Noted")) or "<thinking>" in t[:300] or "thinking tags" in t[:300])
def run(ev, cond):
    rd = os.path.join(ITER, f"eval-{ev['id']}-{ev['name']}", cond, f"run-{RUN}")
    if os.path.exists(os.path.join(rd, "timing.json")): return ev["id"], cond, "skip", 0, 0
    for attempt in range(3):
        rd, proj = prep(ev, cond); to = int(os.environ.get("TIMEOUT", "2400" if ev["id"] <= 4 else "1200")); t0 = time.time()
        cmd = [MINI, "--approval", "auto", "--no-auto-goal", "--json", "--no-builtin-skills", "--max-tokens", "16000", "--cwd", proj, "-p", ev["prompt"]]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=to, stdin=subprocess.DEVNULL, env={**os.environ, "MINIAGENT_MODEL_NAME": MODEL}); so, se, rc = p.stdout, p.stderr, p.returncode
        except subprocess.TimeoutExpired as x:
            so = x.stdout.decode() if isinstance(x.stdout, bytes) else (x.stdout or ""); se, rc = "TIMEOUT", -9
        dt = round(time.time() - t0, 1); resp, sid = "", None
        i = so.rfind('{"response"'); i = so.rfind('{"session_id"') if i < 0 else i
        if i >= 0:
            try: j = json.JSONDecoder().raw_decode(so[i:])[0]; resp = j.get("response") or j.get("error") or ""; sid = j.get("session_id")
            except Exception: pass
        open(f"{rd}/response.md", "w").write(resp); open(f"{rd}/stderr.txt", "w").write(se[-5000:])
        subprocess.run([sys.executable, os.path.expanduser("~/skev/skev_trace.py"), proj, SK, "--save", rd], capture_output=True)
        fin = open(f"{rd}/final.md").read() if os.path.exists(f"{rd}/final.md") else resp
        tr = json.load(open(f"{rd}/trace.json")) if os.path.exists(f"{rd}/trace.json") else {}
        json.dump({"session_id": sid, "project": proj, "returncode": rc, "total_duration_seconds": dt, "duration_ms": int(dt*1000),
                   "total_tokens": (tr.get("input_tokens") or 0) + (tr.get("output_tokens") or 0), "attempt": attempt + 1, "model": MODEL},
                  open(f"{rd}/timing.json", "w"), indent=1)
        if not glitched(fin or resp): break
        if attempt == 2: break
        g = os.path.join(os.path.dirname(rd), f"_glitch{attempt+1}_r{RUN}"); shutil.rmtree(g, ignore_errors=True)
        shutil.move(rd, g)
    return ev["id"], cond, rc, dt, attempt + 1
conds = os.environ.get("CONDS", "with_skill,without_skill").split(",")
jobs = [(e, c) for e in EV if not ids or str(e["id"]) in ids for c in conds]
with cf.ThreadPoolExecutor(int(os.environ.get("PAR", "4"))) as ex:
    for r in ex.map(lambda a: run(*a), jobs): print(SK, *r, flush=True)
print("DONE", SK, flush=True)
