"""p4-pig-fe driver for one family (numbers only): control maps -> sigma0, theta -> injection (control, title) ->
title-strip maps -> scores. Outputs under logs/sib/p4-pig-fe/<family>/ are committed and pushed after each stage.

Provenance: Project HERCULES | owner the owner | [id removed]

Usage (from the repo root): python tools/sib/p4-pig-fe/run_family.py <control> <title> <scratch> <branch> [nloc]
  e.g. C E1 ... (family 1129) or C2 E2 ... (family 24). Frozen parameters: logs/sib/p4-pig-fe/params.json.
"""
import json
import os
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import fe  # noqa: E402
import strip  # noqa: E402

SEEDS = {"C": 101, "E1": 202, "C2": 303, "E2": 404}


def push(paths, msg, branch):
    subprocess.run(["git", "add", *paths])
    subprocess.run(["git", "commit", "-q", "-m", msg + "\n\n" + fe.PROV + "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"])
    for i in range(5):
        if subprocess.run(["git", "push", "-q", "origin", branch]).returncode == 0:
            return
        subprocess.run(["git", "pull", "-q", "--no-rebase", "origin", branch])
        time.sleep(2 ** (i + 1))


def main(ctrl, title, scr, branch, nloc=12):
    fam = fe.MAT[ctrl]["family"]
    od = os.path.join("logs", "sib", "p4-pig-fe", fam)
    os.makedirs(od, exist_ok=True)
    log = open(os.path.join(od, "run_log.jsonl"), "a")
    L = lambda **k: (log.write(json.dumps({"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **k}) + "\n"), log.flush())
    # 1. control maps and scores -> sigma0, theta
    cs = os.path.join(od, f"scores_{ctrl}.json")
    if not os.path.exists(cs):
        if not os.path.exists(os.path.join(scr, f"maps_{ctrl}.npz")):
            L(stage="maps", material=ctrl, meta=strip.maps(ctrl, scr))
        res = strip.score(ctrl, scr, cs)
        P = fe.load_params()
        el = [t for t in res["tiles"] if t.get("eligible") and "z" in t]
        zs = np.array([t["z"] for t in el] + [t["z_rot90"] for t in el])
        theta = float(np.percentile(zs, 99))
        # leave-one-out FP on the control tiles
        fp = 0
        for i, t in enumerate(el):
            rest = [u for j, u in enumerate(el) if j != i]
            th_i = float(np.percentile([u["z"] for u in rest] + [u["z_rot90"] for u in rest], 99))
            fp += int(t["z"] > th_i)
        res["theta"] = theta
        res["theta_rule"] = P["threshold"]["theta"]
        res["n_eligible_control_tiles"] = len(el)
        res["control_fp_leave_one_out"] = {"fp": fp, "n": len(el), "rate": fp / max(len(el), 1)}
        res["rot90_max_abs_diff_z"] = float(max(abs(t["z"] - t["z_rot90"]) for t in el))
        json.dump(res, open(cs, "w"), indent=1)
        L(stage="control_scored", sigma0=res["sigma0"], theta=theta, n=len(el), fp_loo=fp)
        push([od], f"p4-pig-fe {fam}: control {ctrl} scores, sigma0 and theta (control only)", branch)
    res = json.load(open(cs))
    sigma0, theta = res["sigma0"], res["theta"]
    # 2. injection-recovery: control, then title strip
    import inject
    for mat in (ctrl, title):
        ip = os.path.join(od, f"injection_{mat}.json")
        if not os.path.exists(ip) or len(json.load(open(ip))["locations"]) < nloc:
            inject.main(mat, scr, nloc, SEEDS[mat], ip, theta, sigma0)
            push([od], f"p4-pig-fe {fam}: injection-recovery on {mat}", branch)
    # 3. title-strip maps and scores (normalised by the control sigma0)
    ts = os.path.join(od, f"scores_{title}.json")
    if not os.path.exists(ts):
        if not os.path.exists(os.path.join(scr, f"maps_{title}.npz")):
            L(stage="maps", material=title, meta=strip.maps(title, scr))
        r2 = strip.score(title, scr, ts, sigma0=sigma0)
        r2["theta"] = theta
        json.dump(r2, open(ts, "w"), indent=1)
        push([od], f"p4-pig-fe {fam}: title-strip {title} tile scores", branch)
    L(stage="done")


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], a[3], a[4], int(a[5]) if len(a) > 5 else 12)
