# Provenance: Project HERCULES | owner the owner | [id removed]
"""POST-HOC DIAGNOSTIC (not a bar, not part of any pre-registration): r at zero shift of the
attempt-1 AFFINE ALONE on the 16 attempt-2 blocks, to separate model gain from patch-population
differences. Writes posthoc_affine_on_new.json."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import reg_core as rc
from fit_model import to_l1
OUT = "/home/user/dominion/logs/sib/ktlb4p-prep/reg"; BL = "/work/k4p/blocks2"
mod = json.load(open(f"{OUT}/model_final.json")); A1, c1 = to_l1(np.array(mod["A"]), np.array(mod["c"]))
rows = []
for p in json.load(open(f"{OUT}/new_heldout_plan.json"))["patches"]:
    m = json.load(open(f"{BL}/{p['id']}.json"))
    B = np.load(f"{BL}/{p['id']}_v9.npy").astype(np.float32); f2 = rc.prefilter(np.load(f"{BL}/{p['id']}_v2.npy"))
    P = rc.block_points(m["origin9_zyx"], B.shape)
    R0, _ = rc.sample(f2, m["origin2_zyx_level1"], A1, c1, P, B.shape)
    d, info = rc.refine(B, f2, m["origin2_zyx_level1"], A1, c1, P)
    rows.append(dict(id=p["id"], r_affine=rc.ncc(B, R0), abs_d9_affine=float(np.linalg.norm(d))))
    print(rows[-1], flush=True)
r = np.array([x["r_affine"] for x in rows]); dd = np.array([x["abs_d9_affine"] for x in rows])
out = dict(note="post-hoc diagnostic only", rows=rows, median_r_affine=float(np.median(r)), rms_abs_d9_affine=float(np.sqrt((dd ** 2).mean())))
json.dump(out, open(f"{OUT}/posthoc_affine_on_new.json", "w"), indent=1)
print(out["median_r_affine"], out["rms_abs_d9_affine"])
