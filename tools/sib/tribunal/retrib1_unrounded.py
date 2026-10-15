# Provenance: Project HERCULES | owner the owner | [id removed]
"""REAL-TRIB-2 (i): re-analyse the unchanged REAL-TRIB-1 rows with the pre-registered threshold rule
applied UNROUNDED (MIN_REF_NCC = p1 - 3 (1 - p1); margins = p1 / 3; offset tolerance 1 px), with
every check's conditions all evaluated (no short-circuit) and every failing reason listed.
Also reported for comparison: the current thresholds and the round-2 post-hoc alternative.

    python tools/sib/tribunal/retrib1_unrounded.py RAW.json OUT.json
"""
import json
import math
import sys

import numpy as np

OWN = {"offset8": "window_offset", "swap_depth": "depth_order", "mirror": "mirror",
       "off_by_one": "slice_index", "wrong_voxel": "voxel_size"}
CURRENT = {"MIN_REF_NCC": 0.5, "OFFSET_TOL_PX": 1, "MIRROR_MARGIN": 0.05, "DEPTH_MARGIN": 0.02, "SLICE_MARGIN": 0.02}


def reasons(r, t):
    """Every failing condition of every check for one row under thresholds t (no short-circuit)."""
    out = {}
    unver = not (r["best_ncc"] is not None and math.isfinite(r["best_ncc"]) and r["best_ncc"] >= t["MIN_REF_NCC"])

    def add(check, cond, why):
        if cond:
            out.setdefault(check, []).append(why)

    for c in ("window_offset", "mirror", "depth_order", "slice_index"):
        add(c, unver, "unverifiable")
    add("window_offset", max(abs(r["shift"][0]), abs(r["shift"][1])) > t["OFFSET_TOL_PX"], "offset")
    add("mirror", r["transform"] != "identity", f"transform:{r['transform']}")
    add("mirror", not (r["mirror_margin"] is not None and r["mirror_margin"] >= t["MIRROR_MARGIN"]), "ambiguous")
    add("depth_order", str(r["winner"]).startswith("rev"), "reversed")
    add("depth_order", not (r["depth_margin"] is not None and r["depth_margin"] >= t["DEPTH_MARGIN"]), "ambiguous")
    add("slice_index", r["lag"] != 0, f"lag:{r['lag']}")
    add("slice_index", not (r["slice_margin"] is not None and r["slice_margin"] >= t["SLICE_MARGIN"]), "ambiguous")
    add("voxel_size", r["voxel_reason"] != "ok", r["voxel_reason"])
    return out


def evaluate(rows, t):
    clean = [r for r in rows if r["case"] == "clean"]
    res = {"thresholds": t, "clean_n": len(clean), "clean_passed": sum(not reasons(r, t) for r in clean),
           "clean_failures": [{"window": r["window"], "reasons": reasons(r, t)} for r in clean if reasons(r, t)],
           "faults": {}}
    for f, own in OWN.items():
        fr = [r for r in rows if r["case"] == f]
        rs = [reasons(r, t) for r in fr]
        res["faults"][f] = {
            "n": len(fr), "caught_by_own_check": sum(own in x for x in rs),
            "only_own_check": sum(set(x) == {own} for x in rs),
            "own_check_reasons": sorted({why for x in rs for why in x.get(own, [])}),
            "other_checks_fired": sorted({c for x in rs for c in x if c != own}),
        }
    return res


def main():
    raw = json.load(open(sys.argv[1]))
    rows = raw["rows"]
    clean = [r for r in rows if r["case"] == "clean"]
    p1 = {k: float(np.percentile([r[k] for r in clean], 1)) for k in ("best_ncc", "mirror_margin", "depth_margin",
                                                                        "slice_margin")}
    unrounded = {"MIN_REF_NCC": p1["best_ncc"] - 3 * (1 - p1["best_ncc"]), "OFFSET_TOL_PX": 1,
                 "MIRROR_MARGIN": p1["mirror_margin"] / 3, "DEPTH_MARGIN": p1["depth_margin"] / 3,
                 "SLICE_MARGIN": p1["slice_margin"] / 3}
    posthoc = dict(unrounded, MIN_REF_NCC=0.5)
    out = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
           "rule": "REAL-TRIB-2 (i), PREREG.md", "raw": sys.argv[1], "p1_clean": p1,
           "preregistered_unrounded": evaluate(rows, unrounded),
           "current": evaluate(rows, CURRENT),
           "posthoc_min_ref_ncc_0p5": evaluate(rows, posthoc)}
    json.dump(out, open(sys.argv[2], "w"), indent=1, sort_keys=True)
    pu = out["preregistered_unrounded"]
    print(json.dumps({"unrounded_thresholds": unrounded, "clean_passed": pu["clean_passed"],
                      "faults": {f: (v["caught_by_own_check"], v["only_own_check"], v["other_checks_fired"])
                                 for f, v in pu["faults"].items()}}, indent=1))


if __name__ == "__main__":
    main()
