"""Verify from git history that every pre-registered test was declared (committed) before its result was recorded.

  check_preregistration.py [--json results/preregistration_order.json]

For each test: the commit that introduced its declaration heading and the commit that introduced its result heading in the lab notebook
(git log -S, oldest match), with committer times. Times typed into notebook headings are NOT used: they were written by hand and are
not reliable; commit times are.
"""
import json, subprocess, sys

NOTEBOOK_PATHS = ["RULES.md", "docs/RULES.md"]          # the notebook moved into docs/ at the release
TESTS = [
    ("GATE-T1 (w028 calibration)", "## GATE-T1 (6.2)", "### GATE-T1, text1, method v0.1 "),
    ("GATE-S1 (Scroll 1, verified text)", "## GATE-S1 — Scroll 1", "### GATE-S1 TRAIN crop results"),
    ("S1-v5 U-Net (one crop)", "### Declared BEFORE running: S1-v5", "### S1-v5 result"),
    ("transfer to segment 20231210121321", "### Declared BEFORE running: GATE-S1 transfer segment", "### GATE-S1 transfer segment 20231210121321 (2026-09-18"),
    ("judge mask J", "### Judge mask J (declared", "### Segment 1 under mask J"),
    ("stroke test", "## Stroke test (declared", "### Stroke test results"),
    ("local stroke test L", "## Local stroke test L (declared", "### Local stroke test L result"),
    ("v7 hand-built ridge", "## Method v7 (declared", "### v7 result"),
    ("v6b U-Net, 8 crops", "## Method v6b (declared", "### v6b result"),
    ("v6c no-veto control", "## Control v6c (declared", "### Control v6c result"),
    ("v8 U-Net, 15 crops", "## Method v8 (declared", "## v8 RESULT"),
    ("GP-R1 Grand-Prize-style baseline", "## Baseline GP-R (declared", "## GP-R1 RESULT"),
    ("E ensemble", "## Method E (declared", "## Ensemble E RESULT"),
    ("R1 reading run (unread papyrus)", "## Reading run R1 (declared", "## R1 RESULT"),
    ("R2 reading run (unread papyrus)", "## Reading run R2 (declared", "## R2 RESULT"),
    ("C1 confirmation on untouched crops", "## Confirmation test C1 (declared", "## C1 RESULT"),
    ("D3 smoothing-vs-ensembling (post-hoc)", "## Post-hoc decomposition D3 (declared", "## D3 RESULT"),
    ("N1 reading-run null (post-hoc)", "## Post-hoc null N1 for the reading runs (declared", "## N1 RESULT"),
]


def first_commit(s):
    out = subprocess.run(["git", "log", "--format=%h %cI", "-S", s, "--"] + NOTEBOOK_PATHS,
                         capture_output=True, text=True).stdout.strip().splitlines()
    return out[-1].split() if out else None


rows, bad = [], 0
for name, d, r in TESTS:
    a, b = first_commit(d), first_commit(r)
    order = "pending" if not b else ("OK" if a and a[1] < b[1] else "VIOLATION")
    bad += order == "VIOLATION"
    rows.append({"test": name, "declared_commit": a[0] if a else None, "declared_time": a[1] if a else None,
                 "result_commit": b[0] if b else None, "result_time": b[1] if b else None, "order": order})
    print(f"{name:42s} {a[0] if a else '-':8s} {a[1] if a else '':26s} {b[0] if b else '-':8s} {b[1] if b else '':26s} {order}")
if "--json" in sys.argv:
    json.dump(rows, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
sys.exit(1 if bad else 0)
