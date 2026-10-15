# Provenance: Project HERCULES | owner the owner | [id removed]
"""REAL-TRIB-2 (iii): pre-registered criteria on the 2.399 um gate rows (PREREG.md).
Under each threshold set: (a) every clean record passes; (b) every fault is caught by its own
check; (c) every clean margin >= 3 x its threshold (mirror, depth, slice), clean |shift| = 0, clean
best NCC >= MIN_REF_NCC. Reports the smallest margin / threshold ratio. Nothing is rounded.

    python tools/sib/tribunal/analyse_gate_2p4um.py RAW.json RETRIB1_UNROUNDED.json OUT.json
"""
import json
import math
import sys

sys.path.insert(0, "tools/sib/tribunal")
from retrib1_unrounded import OWN, reasons  # noqa: E402  (same evaluator as part i)

SETS = {
    "current": {"MIN_REF_NCC": 0.5, "OFFSET_TOL_PX": 1, "MIRROR_MARGIN": 0.05, "DEPTH_MARGIN": 0.02, "SLICE_MARGIN": 0.02},
    "real_trib1_proposed": {"MIN_REF_NCC": 0.5, "OFFSET_TOL_PX": 1, "MIRROR_MARGIN": 0.181, "DEPTH_MARGIN": 0.284,
                            "SLICE_MARGIN": 0.042},
}
MARGIN_KEYS = {"MIRROR_MARGIN": "mirror_margin", "DEPTH_MARGIN": "depth_margin", "SLICE_MARGIN": "slice_margin"}


def main():
    raw = json.load(open(sys.argv[1]))
    u = json.load(open(sys.argv[2]))["preregistered_unrounded"]["thresholds"]
    sets = dict(SETS, real_trib1_unrounded_rule=u)  # reported too (part i), not a pre-registered criterion set
    rows = raw["rows"]
    clean = [r for r in rows if r["case"] == "clean"]
    out = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
           "rule": "REAL-TRIB-2 (iii), PREREG.md", "volume": raw["volume"], "voxel_um": raw["voxel_um"],
           "metadata_sha256": raw["metadata_sha256"], "renderer_sha256": raw["renderer_sha256"],
           "n_windows": len(clean), "windows": [r["window"] for r in clean],
           "n33_slices_1_32_equal_n31": all(r["n33_vs_n31_maxabs"] == 0 for r in clean),
           "clean_values": {k: [r[k] for r in clean] for k in ("best_ncc", "mirror_margin", "depth_margin",
                                                                 "slice_margin", "shift")},
           "by_threshold_set": {}}
    for name, t in sets.items():
        a = all(not reasons(r, t) for r in clean)
        faults = {}
        for f, own in OWN.items():
            rs = [reasons(r, t) for r in rows if r["case"] == f]
            faults[f] = {"n": len(rs), "caught_by_own_check": sum(own in x for x in rs),
                         "only_own_check": sum(set(x) == {own} for x in rs)}
        b = all(v["caught_by_own_check"] == v["n"] for v in faults.values())
        ratios = {k: min(r[v] for r in clean) / t[k] for k, v in MARGIN_KEYS.items()}
        c = (all(x >= 3.0 for x in ratios.values()) and all(r["shift"] == [0, 0] for r in clean)
             and all(r["best_ncc"] >= t["MIN_REF_NCC"] for r in clean))
        out["by_threshold_set"][name] = {
            "thresholds": t, "a_clean_all_pass": a, "b_faults_caught_by_own_check": b, "faults": faults,
            "c_margin_over_threshold_min_ratio": ratios, "c_min_ratio": min(ratios.values()),
            "c_all_margins_ge_3x": c, "min_clean_best_ncc": min(r["best_ncc"] for r in clean),
            "all_criteria": bool(a and b and c)}
    json.dump(out, open(sys.argv[3], "w"), indent=1, sort_keys=True)
    print(json.dumps({k: {x: v[x] for x in ("a_clean_all_pass", "b_faults_caught_by_own_check", "c_min_ratio",
                                              "c_all_margins_ge_3x", "min_clean_best_ncc")}
                      for k, v in out["by_threshold_set"].items()}, indent=1, default=float))


if __name__ == "__main__":
    main()
