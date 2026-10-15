# Provenance: Project HERCULES | owner the owner | [id removed]
"""Summarise REAL-TRIB-1 rows and PROPOSE thresholds from the real clean margins.

Rule (fixed before the full run was summarised):
  margin thresholds (mirror, depth, slice) = clean 1st percentile / 3 (safety factor 3);
  MIN_REF_NCC = max(0.5, p1 - 3 (1 - p1)) with p1 the clean 1st percentile of the best NCC;
  offset tolerance stays 1 px (reported: the clean maximum |shift|).
The proposal is valid only if, re-evaluated under the proposed thresholds, every clean
record still passes and every planted fault is still caught by its own check.

    python tools/sib/tribunal/analyse_real_trib1.py RAW.json OUT.json
"""
import json
import math
import sys

import numpy as np

OWN = {"offset8": "window_offset", "swap_depth": "depth_order", "mirror": "mirror",
       "off_by_one": "slice_index", "wrong_voxel": "voxel_size"}
CURRENT = {"MIN_REF_NCC": 0.5, "MIRROR_MARGIN": 0.05, "DEPTH_MARGIN": 0.02, "SLICE_MARGIN": 0.02, "OFFSET_TOL_PX": 1}


def fails_under(r, t):
    """Re-evaluate the four data checks of one row under thresholds t (voxel check unchanged)."""
    f = set()
    unver = not (r["best_ncc"] is not None and r["best_ncc"] >= t["MIN_REF_NCC"])
    if unver or max(abs(r["shift"][0]), abs(r["shift"][1])) > t["OFFSET_TOL_PX"]:
        f.add("window_offset")
    if unver or r["transform"] != "identity" or not (r["mirror_margin"] >= t["MIRROR_MARGIN"]):
        f.add("mirror")
    if unver or str(r["winner"]).startswith("rev") or not (r["depth_margin"] >= t["DEPTH_MARGIN"]):
        f.add("depth_order")
    if unver or r["lag"] != 0 or not (r["slice_margin"] >= t["SLICE_MARGIN"]):
        f.add("slice_index")
    if r["voxel_reason"] != "ok":
        f.add("voxel_size")
    return f


def stats(v):
    v = np.asarray([x for x in v if x is not None and math.isfinite(x)], float)
    if not v.size:
        return None
    return {"n": int(v.size), "min": float(v.min()), "p1": float(np.percentile(v, 1)), "p5": float(np.percentile(v, 5)),
            "median": float(np.median(v)), "max": float(v.max())}


def main():
    raw = json.load(open(sys.argv[1]))
    rows = raw["rows"]
    clean = [r for r in rows if r["case"] == "clean"]
    dist = {k: stats([r[k] for r in clean]) for k in ("best_ncc", "identity_zero_ncc", "mirror_margin", "depth_margin",
                                                     "slice_margin")}
    dist["abs_shift_max_px"] = max(max(abs(r["shift"][0]), abs(r["shift"][1])) for r in clean) if clean else None
    p1 = {k: dist[k]["p1"] for k in ("best_ncc", "mirror_margin", "depth_margin", "slice_margin")}
    prop = {"MIN_REF_NCC": round(max(0.5, p1["best_ncc"] - 3 * (1 - p1["best_ncc"])), 3),
            "MIRROR_MARGIN": round(p1["mirror_margin"] / 3, 3), "DEPTH_MARGIN": round(p1["depth_margin"] / 3, 3),
            "SLICE_MARGIN": round(p1["slice_margin"] / 3, 3), "OFFSET_TOL_PX": 1}
    # POST-HOC alternative (labelled; added after the pre-registered MIN_REF_NCC output was
    # found defective: p1 - 3 (1 - p1) = 0.9998 rounds to 1.000 and fails every clean record).
    # MIN_REF_NCC stays at the current 0.5: it must stay below the surface NCC that genuine
    # faults produce (off-by-one gives 0.74-0.85), else faults become "unverifiable" rather
    # than being attributed to their own check; margins keep the pre-registered p1 / 3.
    alt = dict(prop, MIN_REF_NCC=CURRENT["MIN_REF_NCC"])
    fault_ncc = {f: stats([r["best_ncc"] for r in rows if r["case"] == f]) for f in OWN if f != "wrong_voxel"}
    faults = {}
    for f, own in OWN.items():
        fr = [r for r in rows if r["case"] == f]
        faults[f] = {"n": len(fr), "caught_by_own_check": sum(own in r["failed"] for r in fr),
                     "caught_by_gate": sum(not r["passed"] for r in fr),
                     "other_checks_fired": sorted({c for r in fr for c in r["failed"] if c != own}),
                     "caught_under_proposed": sum(own in fails_under(r, prop) for r in fr),
                     "caught_under_posthoc_alternative": sum(own in fails_under(r, alt) for r in fr),
                     "only_own_check_under_alternative": sum(fails_under(r, alt) == {own} for r in fr)}
    clean_ok_prop = sum(not fails_under(r, prop) for r in clean)
    clean_ok_alt = sum(not fails_under(r, alt) for r in clean)
    rt = raw.get("retrace", [])
    pos = [r for r in rt if r["case"] == "retrace_pos"]
    neg = [r for r in rt if r["case"] == "retrace_neg"]
    out = {
        "provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
        "rule": "REAL-TRIB-1", "raw": sys.argv[1], "volume": raw["volume"], "voxel_um": raw["voxel_um"],
        "metadata_sha256": raw["metadata_sha256"], "renderer_sha256": raw["renderer_sha256"],
        "n_windows": len(clean), "windows": [r["window"] for r in clean],
        "n33_slices_1_32_equal_n31": all(r["n33_vs_n31_maxabs"] == 0 for r in clean),
        "clean": {"n": len(clean), "passed_current": sum(r["passed"] for r in clean), "passed_preregistered_rule": clean_ok_prop,
                  "passed_posthoc_alternative": clean_ok_alt,
                  "margins": dist},
        "faults": faults,
        "retrace": {"positives": len(pos), "caught": sum(r["caught"] for r in pos),
                    "caught_vertex_form_alone": sum(r["vertex_same"] for r in pos),
                    "caught_surface_form_alone": sum(r["surface_same"] for r in pos),
                    "negatives": len(neg), "false_alarms": sum(r["caught"] for r in neg),
                    "base_training_same_in_positive_windows": sorted({s for r in pos for s in r["base_training_same_as"]}),
                    "base_training_same_in_negative_windows": sorted({s for r in neg for s in r["base_training_same_as"]})},
        "thresholds_current": CURRENT,
        "thresholds_preregistered_rule_output": prop,
        "preregistered_rule_defect": "MIN_REF_NCC = p1 - 3 (1 - p1) rounds to 1.000 when the reference is exact; "
                                     "it fails every clean record and is NOT proposed",
        "thresholds_proposed": alt,
        "thresholds_proposed_basis": "POST-HOC: margins by the pre-registered p1 / 3 rule; MIN_REF_NCC kept at 0.5 "
                                     "(below the 0.74-0.85 surface NCC of genuine off-by-one faults)",
        "fault_best_ncc": fault_ncc,
        "proposal_rule": __doc__.split("Rule (fixed before the full run was summarised):")[1].split("python tools")[0].strip(),
        "status": "PROPOSED, not declared",
    }
    allc = all(v["caught_by_own_check"] == v["n"] and v["caught_under_posthoc_alternative"] == v["n"]
               for v in faults.values())
    out["verdict"] = ("PASS" if (allc and out["clean"]["passed_current"] == len(clean) and clean_ok_alt == len(clean)
                                 and len(pos) >= 1 and len(neg) >= 1
                                 and out["retrace"]["caught"] == len(pos) and out["retrace"]["false_alarms"] == 0
                                 and len(clean) >= 10) else "FAIL")
    json.dump(out, open(sys.argv[2], "w"), indent=1, sort_keys=True)
    print(json.dumps({"verdict": out["verdict"], "clean": out["clean"]["passed_current"], "faults":
                      {k: (v["caught_by_own_check"], v["n"]) for k, v in faults.items()}, "proposed": alt, "preregistered_output": prop, "clean_alt": clean_ok_alt,
                      "retrace": out["retrace"]}, default=float))


if __name__ == "__main__":
    main()
