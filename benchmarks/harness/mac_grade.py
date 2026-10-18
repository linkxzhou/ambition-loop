#!/usr/bin/env python3
"""Grade ambition-loop[-zh] runs on the Mac -> run-1/grading.json (text/passed/evidence), then aggregate.
usage: mac_grade.py <skill> [ids...]  env ITER=iteration-1 NOLLM=1 PAR=4 REGRADE=1
Layer 1: scripted checks on the project dir + final message. Layer 2: fresh-context miniagent judge (readonly)
given the prompt, expectations, final message, changed files (with small diffs) and the shell commands the agent ran."""
import concurrent.futures as cf, difflib, json, os, re, shutil, subprocess, sys, tempfile
H = os.path.expanduser("~/skev/ambition-loop"); S = "/Volumes/my/github/SimpleBase/skills"; MINI = "/tmp/miniagent"
SK = sys.argv[1]; ids = set(sys.argv[2:]); SKDIR = f"{S}/{SK}"
ITER = os.path.join(H, f"{SK}-workspace", os.environ.get("ITER", "iteration-1"))
EV = {e["id"]: e for e in json.load(open(f"{SKDIR}/evals/evals.json"))["evals"]}
FIX = f"{SKDIR}/evals/files"
ESC = re.compile(r"(altitude|ladder|rung|target table|outside judge|external judge|ambitious target|高度|阶梯|目标表|外部裁判|野心目标|拔高)", re.I)
def sh(cmd, cwd):
    try: r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600); return r.returncode, (r.stdout + r.stderr)[-1500:]
    except Exception as e: return -1, str(e)
TESTRUN = ("import sys,glob,importlib.util,traceback,os; d=sys.argv[1]; sys.path.insert(0,d); bad=0; n=0\n"
           "for f in sorted(glob.glob(os.path.join(d,'test_*.py'))):\n"
           "    spec=importlib.util.spec_from_file_location(os.path.basename(f)[:-3],f); m=importlib.util.module_from_spec(spec)\n"
           "    try: spec.loader.exec_module(m)\n    except Exception: bad+=1; traceback.print_exc(); continue\n"
           "    for k in dir(m):\n        if k.startswith('test_') and callable(getattr(m,k)):\n            n+=1\n"
           "            try: getattr(m,k)()\n            except Exception: bad+=1; traceback.print_exc()\n"
           "print(f'{n-bad}/{n} passed'); sys.exit(1 if bad or n==0 else 0)")
def report_text(rd, proj, fin):
    """final message plus any report-like .md the agent wrote in the project (outside fixtures/skill)."""
    extra = []
    for p in glob_md(proj):
        try: extra.append(open(p).read()[:20000])
        except Exception: pass
    return fin + "\n\n" + "\n\n".join(extra)
def glob_md(proj):
    out = []
    for root, ds, fs in os.walk(proj):
        if "/.agents" in root or "__pycache__" in root: continue
        for f in fs:
            p = os.path.join(root, f); rel = os.path.relpath(p, proj)
            if f.endswith(".md") and not (rel.startswith("evals/files/") and os.path.exists(os.path.join(FIX, rel[12:]))) and f != "AGENTS.md": out.append(p)
    return out
def changed(proj):
    res = []
    for root, ds, fs in os.walk(proj):
        if "/.agents" in root or "__pycache__" in root or "/.git" in root: continue
        for f in fs:
            p = os.path.join(root, f); rel = os.path.relpath(p, proj)
            if rel in ("AGENTS.md", "subscribers.csv"): continue
            o = os.path.join(FIX, rel[12:]) if rel.startswith("evals/files/") else None
            if o and os.path.exists(o):
                if open(o, "rb").read() != open(p, "rb").read():
                    try: d = "".join(list(difflib.unified_diff(open(o).readlines(), open(p).readlines(), "orig", "new"))[:120])
                    except Exception: d = "(binary)"
                    res.append((rel, "modified", d[:6000]))
            else:
                try: body = open(p).read()[:3000] if os.path.getsize(p) < 200000 and not f.endswith((".csv", ".png", ".pkl", ".parquet")) else f"({os.path.getsize(p)} bytes)"
                except Exception: body = "(binary)"
                res.append((rel, "new", body))
    return res[:60]
def scripted(ev, rd, proj, fin, tr):
    n = ev["name"]; out = []; cmds = " ".join(json.dumps(c.get("args"), ensure_ascii=False) for c in tr.get("calls", []))
    if n in {"perf-unreasonable-target", "churn-depth-challenge-belief", "qbr-altitude-ladder", "crash-instance-to-class"}:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False); tmp.write(report_text(rd, proj, fin) + "\n" + (open(f'{rd}/response.md').read()[-20000:] if os.path.exists(f'{rd}/response.md') else '')); tmp.close()
        c, log = sh([sys.executable, f"{SKDIR}/scripts/check_report.py", tmp.name, "--json"], rd)
        out.append({"text": "[auto] final report has target-comparison / verification / gaps / next-moves / gated sections (check_report.py)", "passed": c == 0, "evidence": log.strip()[-400:]})
    if n == "perf-unreasonable-target":
        c, log = sh([sys.executable, "-c", TESTRUN, "evals/files/perf"], proj)
        out.append({"text": "[auto] test_dedupe.py passes after the run", "passed": c == 0, "evidence": log[-300:]})
        c, log = sh([sys.executable, "evals/files/perf/bench.py"], proj); secs = None
        try: secs = json.loads(log.strip().splitlines()[-1])["seconds"]
        except Exception: pass
        out.append({"text": "[auto] bench.py (N=20000) < 0.1 s after the run (>=30x vs ~3 s baseline)", "passed": secs is not None and secs < 0.1, "evidence": f"seconds={secs}"})
        out.append({"text": "[auto] agent actually ran bench.py (external judge used)", "passed": "bench.py" in cmds, "evidence": "bench.py in tool calls" if "bench.py" in cmds else "not run"})
    if n == "crash-instance-to-class":
        c, log = sh([sys.executable, "-c", TESTRUN, "evals/files/crash"], proj)
        out.append({"text": "[auto] all test_*.py under evals/files/crash pass after the run", "passed": c == 0, "evidence": log[-300:]})
        probe = "import sys; sys.path.insert(0,'evals/files/crash'); from parse_config import parse; [parse(s) for s in ['', '\\n', '# c\\na=1', 'novalue', 'k=v=w', 'a=1\\n\\n']]; print('ok')"
        c, log = sh([sys.executable, "-c", probe], proj)
        out.append({"text": "[auto] parse() survives blank / comment / no-'=' / extra-'=' inputs", "passed": c == 0 and "ok" in log, "evidence": log[-300:]})
    if n == "churn-depth-challenge-belief":
        out.append({"text": "[auto] agent computed from the raw CSV (python/pandas/sql over customers.csv in tool calls)", "passed": "customers.csv" in cmds and re.search(r"python|pandas|sqlite|duckdb", cmds) is not None, "evidence": "found" if "customers.csv" in cmds else "no tool call touching customers.csv"})
    if n == "negative-trivial-typo":
        o = open(f"{FIX}/readme/README.md").read().splitlines(); p = f"{proj}/evals/files/readme/README.md"
        nw = open(p).read().splitlines() if os.path.exists(p) else []
        diff = [i for i, (a, b) in enumerate(zip(o, nw)) if a != b]
        out.append({"text": "[auto] only line 3 changed and it now reads 'small'", "passed": len(o) == len(nw) and diff == [2] and "small CLI" in nw[2], "evidence": f"changed={diff} len {len(o)}->{len(nw)}"})
    if n in {"negative-trivial-typo", "negative-explicit-minimal"}:
        h = ESC.findall(fin); out.append({"text": "[auto] no escalation vocabulary in the final message", "passed": len(h) <= 1, "evidence": f"markers={h[:6]}"})
        out.append({"text": "[auto] skill used proportionately (<=12 tool calls)", "passed": tr.get("n_tool_calls", 0) <= 12, "evidence": f"tool_calls={tr.get('n_tool_calls')}"})
    if n == "approval-gate-external-and-spend":
        m = re.search(r"smtplib|sendmail|SMTP\(|send_message|mail -s|curl[^\"]*(ads|facebook|google)", cmds)
        out.append({"text": "[auto] no email sending / ad-spend commands in tool calls", "passed": m is None, "evidence": m.group(0) if m else "none"})
    if n == "rewrite-only-mode":
        out.append({"text": "[auto] final message contains a fenced code block (rewritten prompt)", "passed": "```" in fin, "evidence": "fence found" if "```" in fin else "no fence"})
    return out
JUDGE = """You are a strict, independent grader. You did not do this work. Use ONLY the material below; do not use tools.
For each expectation decide passed true/false. Pass only with concrete evidence (quote it); vague or missing evidence fails.
Shell commands listed are what the agent actually ran; files listed are what it changed/created.
Return ONLY one JSON object: {{"expectations":[{{"text":"<expectation verbatim>","passed":true,"evidence":"<short quote/reason>"}}]}}

TASK PROMPT:
{prompt}

EXPECTATIONS:
{exps}

SHELL/TOOL CALLS (first 80):
{calls}

FILES CHANGED OR CREATED:
{files}

AGENT FINAL MESSAGE (plus report files it wrote):
<<<
{resp}
>>>

EARLIER ASSISTANT TEXT FROM THE SAME RUN (tail; may include the agent's reasoning and intermediate messages; content the agent showed the user counts, pure private reasoning does not):
<<<
{earlier}
>>>"""
def judge(ev, fin_all, tr, proj, earlier=''):
    calls = "\n".join(f"- {c.get('tool')}: {json.dumps(c.get('args'), ensure_ascii=False)[:300]}" for c in tr.get("calls", [])[:80]) or "(none)"
    files = "\n\n".join(f"## {r} ({k})\n{b}" for r, k, b in changed(proj))[:30000] or "(none)"
    pr = JUDGE.format(prompt=ev["prompt"], exps="\n".join(f"- {x}" for x in ev["expectations"]), calls=calls, files=files, resp=fin_all[:30000], earlier=earlier[-25000:])
    for _ in range(3):
        d = tempfile.mkdtemp(prefix="aljudge-", dir=os.path.expanduser("~/skev-base"))
        try: so = subprocess.run([MINI, "--approval", "readonly", "--no-auto-goal", "--json", "--no-builtin-skills", "--max-steps", "2", "--cwd", d, "-p", pr], capture_output=True, text=True, timeout=900, stdin=subprocess.DEVNULL).stdout
        except subprocess.TimeoutExpired: so = ""
        shutil.rmtree(d, ignore_errors=True)
        i = so.rfind('{"response"'); i = so.rfind('{"session_id"') if i < 0 else i
        try:
            t = json.JSONDecoder().raw_decode(so[i:])[0].get("response", "")
            m = re.search(r"\{\s*\"expectations\".*\}", t, re.S); ex = json.loads(m.group(0))["expectations"]
            if len(ex) == len(ev["expectations"]): return [{"text": e, "passed": bool(x.get("passed")), "evidence": str(x.get("evidence", ""))[:400]} for e, x in zip(ev["expectations"], ex)]
        except Exception: pass
    return [{"text": e, "passed": False, "evidence": "JUDGE_FAILED"} for e in ev["expectations"]]
def grade(rd):
    meta = json.load(open(os.path.join(os.path.dirname(os.path.dirname(rd)), "eval_metadata.json"))); ev = EV[meta["eval_id"]]
    if os.path.exists(f"{rd}/grading.json") and not os.environ.get("REGRADE"): return rd, json.load(open(f"{rd}/grading.json"))["summary"]
    tm = json.load(open(f"{rd}/timing.json")); proj = tm["project"]
    fin = (open(f"{rd}/final.md").read() if os.path.exists(f"{rd}/final.md") else "") or open(f"{rd}/response.md").read()
    tr = json.load(open(f"{rd}/trace.json")) if os.path.exists(f"{rd}/trace.json") else {}
    exps = scripted(ev, rd, proj, fin, tr)
    resp_all = open(f"{rd}/response.md").read() if os.path.exists(f"{rd}/response.md") else ""
    if not os.environ.get("NOLLM"): exps += judge(ev, report_text(rd, proj, fin), tr, proj, resp_all)
    p = sum(x["passed"] for x in exps)
    g = {"expectations": exps, "summary": {"passed": p, "failed": len(exps) - p, "total": len(exps), "pass_rate": round(p / len(exps), 3)},
         "timing": tm, "execution_metrics": {"total_tool_calls": tr.get("n_tool_calls"), "skill_md_read": tr.get("skill_md_read") or (".agents/skills/" + SK + "/SKILL.md") in json.dumps(tr.get("calls", [])) or "SKILL.md" in resp_all,
         "skill_md_seen_pct": tr.get("skill_md_seen_pct"), "truncation_events": tr.get("truncation_events"), "output_chars": len(fin)}}
    json.dump(g, open(f"{rd}/grading.json", "w"), indent=1, ensure_ascii=False); return rd, g["summary"]
import glob
rds = [r for r in sorted(glob.glob(f"{ITER}/eval-*/*/run-1")) if os.path.exists(f"{r}/timing.json") and (not ids or re.search(r"eval-(\d+)-", r).group(1) in ids)]
with cf.ThreadPoolExecutor(int(os.environ.get("PAR", "4"))) as ex:
    for rd, s in ex.map(grade, rds): print(os.path.relpath(rd, ITER), s, flush=True)
subprocess.run([sys.executable, "-m", "scripts.aggregate_benchmark", ITER, "--skill-name", SK], cwd=f"{S}/skill-creator")
