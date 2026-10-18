#!/usr/bin/env python3
"""Check that ambition-loop and ambition-loop-zh stay structurally in sync."""
import json, re, sys
from pathlib import Path
R = Path(__file__).resolve().parent.parent.parent  # repo root = English skill
en, zh = R, R / "ambition-loop-zh"
SKILL_PARTS = ("SKILL.md", "references", "scripts", "evals")
def _files(base):
    out = []
    for p in base.rglob("*"):
        rel = p.relative_to(base).as_posix()
        if p.is_file() and "__pycache__" not in rel and rel.split("/")[0] in SKILL_PARTS:
            out.append(rel)
    return sorted(out)
problems = []
ef = _files(en)
zf = _files(zh)
if ef != zf: problems.append(f"file sets differ: {set(ef) ^ set(zf)}")
es, zs = (en / "SKILL.md").read_text(), (zh / "SKILL.md").read_text()
n_en = len(re.findall(r"(?m)^### Step \d+", es)); n_zh = len(re.findall(r"(?m)^### 第 \d+ 步", zs))
if n_en != n_zh: problems.append(f"step count en={n_en} zh={n_zh}")
for g in ["G1", "G2", "G3", "G4", "G5"]:
    if g not in es or g not in zs: problems.append(f"gate {g} missing")
for k, (a, b) in {"Action": ("**Action:**", "**动作：**"), "Output": ("**Output:**", "**产出：**"), "Done": ("**Done when:**", "**完成标准：**")}.items():
    if es.count(a) != zs.count(b): problems.append(f"{k} count en={es.count(a)} zh={zs.count(b)}")
ee = json.load(open(en / "evals/evals.json"))["evals"]; ze = json.load(open(zh / "evals/evals.json"))["evals"]
if [(e["id"], e["name"], len(e["expectations"])) for e in ee] != [(e["id"], e["name"], len(e["expectations"])) for e in ze]: problems.append("evals differ in ids/names/expectation counts")
for f in ["scripts/check_report.py"]:
    if (en / f).read_bytes() != (zh / f).read_bytes(): problems.append(f"{f} differs")
import filecmp
d = filecmp.dircmp(en / "evals/files", zh / "evals/files")
if d.diff_files or d.left_only or d.right_only: problems.append("fixtures differ")
print("\n".join(problems) if problems else f"in sync: {n_en} steps, {len(ee)} evals, {len(ef)} files")
sys.exit(1 if problems else 0)
