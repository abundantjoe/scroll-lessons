# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-7 item 3 preparation: choose the 2 x 2 cm core window and the VC3D
seeds from the item-1 count JSONs (numbers only), and emit the exact trace
commands. Nothing is traced by this script.

Window rule (fixed here, before any trace):
  * z band: inside the 1.129 um footprint (67.4-135.3 mm) so that p4-inner's
    1.129 um count covers the same material; 20 mm tall; the band whose
    levels have the highest fraction of rays with |calibration - 10| <= 1
    (the counter is best validated there), ties -> lower count spread.
  * seeds: at each level in the band, the outermost inner peak (the
    w009 candidate) on the ray with the median inner count whose
    calibration count equals 10; 3 seeds (band bottom, middle, top).
  * a trace is RUN only if DECL-P4-7 items 1-2 show papyrus inward of w010 in
    both this count and p4-inner's 1.129 um count (task gate).

usage: plan_window.py <levels_dir> <out.json>
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

KEY = "primary_pf0.25"
FOOT = (67.4, 135.3)
VOL_PRED = ("https://vesuvius-challenge-open-data.s3.amazonaws.com/PHercParis4/representations/predictions/surfaces/"
            "20260411134726-surface-20260413141734-surface-recto-2um-ps256-L0-th0.45.zarr")


def main(levels_dir: Path, out: Path):
    L = [json.load(open(f)) for f in sorted(levels_dir.glob("z*.json"))]
    L = [d for d in L if "runs" in d]
    stat = []
    for d in L:
        rr = [o for o in d["runs"][KEY] if o]
        cal = np.array([o["n_cal"] for o in rr])
        n = np.array([o["n_inner"] for o in rr])
        stat.append(dict(z=d["z_mm"], cal_ok=float(np.mean(np.abs(cal - 10) <= 1)), iqr=float(np.subtract(*np.percentile(n, [75, 25])))))
    best = None
    for z0 in np.arange(FOOT[0], FOOT[1] - 20 + 1e-6, 1.0):
        s = [t for t in stat if z0 <= t["z"] <= z0 + 20]
        if len(s) < 3:
            continue
        sc = (np.mean([t["cal_ok"] for t in s]), -np.mean([t["iqr"] for t in s]))
        if best is None or sc > best[0]:
            best = (sc, float(z0), s)
    if best is None:
        raise SystemExit("no z band with >= 3 levels inside the 1.129 um footprint")
    (cal_ok, neg_iqr), z0, s = best
    zs = [t["z"] for t in s]
    pick = [zs[0], zs[len(zs) // 2], zs[-1]]
    seeds = []
    for d in L:
        if d["z_mm"] not in pick:
            continue
        rr = d["runs"][KEY]
        n = np.array([o["n_inner"] if o else -1 for o in rr])
        ok = [i for i, o in enumerate(rr) if o and o["n_cal"] == 10 and o["inner_peaks_mm"]]
        if not ok:
            continue
        med = np.median(n[ok])
        i = min(ok, key=lambda j: (abs(n[j] - med), j))
        th = d["angles"][i]
        r_mm = rr[i]["inner_peaks_mm"][-1]
        cx, cy = d["umb_xy"]
        rv = r_mm / 2.4e-3
        seeds.append({"z_mm": d["z_mm"], "ray": i, "theta": th, "r_mm": r_mm, "candidate": "w009 (outermost inner peak)",
                      "xyz_vox": [round(cx + rv * math.cos(th), 1), round(cy + rv * math.sin(th), 1), d["z_vox"]],
                      "ray_inner_count": int(n[i])})
    plan = {"provenance": "Project HERCULES | owner the owner | [id removed]",
            "rule": __doc__.split("Window rule")[1].split("usage")[0].strip(),
            "band_mm": [z0, z0 + 20], "band_levels": s, "band_cal_ok_mean": cal_ok, "band_iqr_mean": -neg_iqr,
            "seeds": seeds, "prediction_zarr": VOL_PRED,
            "commands": [f"vc_grow_seg_from_seed --volume {VOL_PRED} --target-dir traces/p4core_s{k} "
                         f"--params presets/P4CORE_L20.json --seed {sd['xyz_vox'][0]} {sd['xyz_vox'][1]} {sd['xyz_vox'][2]}"
                         for k, sd in enumerate(seeds)]}
    json.dump(plan, open(out, "w"), indent=1)
    print(json.dumps({k: plan[k] for k in ("band_mm", "band_cal_ok_mean", "seeds")}, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
