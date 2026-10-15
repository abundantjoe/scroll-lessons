"""p4-highz step 2/4 outputs: screen.json (DECL-P4-6 item 3) and f1/manifest.json, from stage_a/stage_b records.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python screen.py <scratch> <repo> [candidates]   ('candidates' only prints tiles needing the full-coverage f_in)
"""
import hashlib
import json
import os
import sys
import time

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(__file__))
import common as C  # noqa: E402

scr, repo = sys.argv[1], sys.argv[2]
ARGS = [a for a in sys.argv[3:] if a != "candidates"]
CT, TG = (ARGS[0], ARGS[1]) if len(ARGS) >= 2 else ("C", "E1")
SUF = "" if TG == "E1" else "_2p4"
out = os.path.join(repo, "logs/sib/p4-highz")
th = json.load(open(os.path.join(out, f"thresholds{SUF}.json")))
T_hi = th["T_hi"]
recs, fsamp = {}, {}
for name in (CT, TG):
    recs[name] = [json.loads(l) for l in open(os.path.join(scr, f"stage_b_{name}.jsonl"))]
    z = np.load(os.path.join(scr, f"stage_a_{name}.npz"))
    for (r, c), h, n in zip(z["rc"], z["H"], z["npx"]):
        ns, nl, nh = (int(h[k][T_hi + 1:].sum()) for k in range(3))
        md = C.MATERIALS[name]
        ngap = (md["gap_lo"][1] - md["gap_lo"][0]) + (md["gap_hi"][1] - md["gap_hi"][0])
        fsamp[(name, int(r), int(c))] = {"n_sheet": ns, "n_gap_lo": nl, "n_gap_hi": nh,
                                         "f_in_sample": ns / max(1, ns + nl + nh),
                                         "density_ratio_sheet_over_gaps": (ns / 13) / max(1e-9, (nl + nh) / ngap),
                                         "sample_valid_px": int(n)}
nhc = np.array([t["n_hi"] for t in recs[CT]], float)
p99 = float(np.percentile(nhc, 99))
cand = [(t["r"], t["c"]) for t in recs[TG] if t["n_hi"] > p99]
cand_c = [(t["r"], t["c"]) for t in recs[CT] if t["n_hi"] > p99]
if "candidates" in sys.argv:
    print(json.dumps({"control_tile_p99_n_hi": p99, TG: cand, CT: cand_c}))
    sys.exit()
full = {}
for name in (CT, TG):
    p = os.path.join(scr, f"stage_b_gap_{name}.jsonl")
    if os.path.exists(p):
        for l in open(p):
            d = json.loads(l)
            full[(name, d["r"], d["c"])] = d


def row(name, t):
    k = (name, t["r"], t["c"])
    fs = fsamp[k]
    fu = full.get(k)
    f_in = fu["f_in_full"] if fu else fs["f_in_sample"]
    a, a9 = t["acf"] or {}, t["acf_rot90"] or {}
    s = t["stroke"]
    return {"tile": f"r{t['r']}_c{t['c']}", "r": t["r"], "c": t["c"], "n_hi": t["n_hi"],
            "n_hi_per_1e6_voxels": t["n_hi_per_1e6_voxels"], "valid_px_present": t["valid_px_present"],
            "frac_valid_in_absent_chunk": t["frac_valid_in_absent_chunk"],
            "f_in": f_in, "f_in_source": "full coverage" if fu else "6 % chunk sample", "f_in_sample": fs,
            "f_in_full": fu, "n_hi_gt_control_p99": t["n_hi"] > p99,
            "DENSE_HOTSPOT": bool(t["n_hi"] > p99 and f_in >= 0.8),
            "acf_radial_peak_2_4mm": a.get("radial_peak_2_4mm"), "acf_radial_peak_mm": a.get("radial_peak_radius_mm"),
            "acf_radial_mean_2_4mm": a.get("radial_mean_2_4mm"),
            "acf_dir_rows_peak": a.get("dir_rows_peak"), "acf_dir_cols_peak": a.get("dir_cols_peak"),
            "rot90_acf_radial_peak_2_4mm": a9.get("radial_peak_2_4mm"),
            "rot90_acf_dir_rows_peak": a9.get("dir_rows_peak"), "rot90_acf_dir_cols_peak": a9.get("dir_cols_peak"),
            "rot90_n_hi": t["n_hi"], "rot90_f_in": f_in,
            "stroke": s, "mip_mean": t["mip_mean"], "frac_mip_gt_T_hi": t["frac_mip_gt_T_hi"],
            "frac_mip_255": t["frac_mip_255"]}


S = {name: [row(name, t) for t in sorted(recs[name], key=lambda d: (d["r"], d["c"]))] for name in (CT, TG)}


def q(a):
    a = np.array([x for x in a if x is not None], float)
    if not a.size:
        return None
    return {k: float(v) for k, v in zip(("min", "p10", "median", "p90", "p99", "max"), np.percentile(a, [0, 10, 50, 90, 99, 100]))}


summ = {}
for name in (CT, TG):
    L = S[name]
    summ[name] = {"tiles": len(L), "n_hi": q([x["n_hi"] for x in L]),
                  "n_hi_per_1e6_voxels": q([x["n_hi_per_1e6_voxels"] for x in L]),
                  "f_in_sample": q([x["f_in_sample"]["f_in_sample"] for x in L]),
                  "density_ratio_sheet_over_gaps": q([x["f_in_sample"]["density_ratio_sheet_over_gaps"] for x in L]),
                  "acf_radial_peak_2_4mm": q([x["acf_radial_peak_2_4mm"] for x in L]),
                  "acf_dir_rows_peak": q([x["acf_dir_rows_peak"] for x in L]),
                  "acf_dir_cols_peak": q([x["acf_dir_cols_peak"] for x in L]),
                  "stroke_width_um_median": q([x["stroke"].get("width_um_median") for x in L]),
                  "components_letter_scale": q([x["stroke"].get("components_letter_scale_0p5_5mm") for x in L]),
                  "comp_extent_mm_max": q([x["stroke"].get("comp_extent_mm_max") for x in L]),
                  "mean_hi_depth_um": q([x["stroke"].get("mean_hi_depth_um") for x in L]),
                  "frac_mip_255": q([x["frac_mip_255"] for x in L]),
                  "n_gt_control_p99": sum(x["n_hi_gt_control_p99"] for x in L),
                  "DENSE_HOTSPOT": [x["tile"] for x in L if x["DENSE_HOTSPOT"]]}
ks = {}
for key in ("n_hi_per_1e6_voxels", "acf_radial_peak_2_4mm"):
    a = [x[key] for x in S[CT] if x[key] is not None]
    b = [x[key] for x in S[TG] if x[key] is not None]
    r = stats.ks_2samp(a, b)
    ks[key] = {"D": float(r.statistic), "p": float(r.pvalue), f"n_{CT}": len(a), f"n_{TG}": len(b)}
rot_ok = all(abs((x["rot90_acf_radial_peak_2_4mm"] or 0) - (x["acf_radial_peak_2_4mm"] or 0)) < 1e-6 and
             abs((x["rot90_acf_dir_rows_peak"] or 0) - (x["acf_dir_cols_peak"] or 0)) < 1e-6 for L in S.values() for x in L)
screen = {"provenance": C.PROV, "serves": "RULES.md DECL-P4-6 item 3 (numeric screen; numbers only, no tile viewed)",
          "thresholds": {"T_mid": th["T_mid"], "T_hi": T_hi}, "control_tile_p99_n_hi": p99,
          "dense_hotspot_rule": "n_hi > control tile p99 AND f_in >= 0.8",
          "f_in_rule": "n_sheet / (n_sheet + n_gap_lo + n_gap_hi), voxels > T_hi; 13 sheet vs 54 gap slices, so a depth-uniform "
                       "population gives 13/67 = 0.194",
          f"DENSE_HOTSPOT_{TG}": summ[TG]["DENSE_HOTSPOT"], f"DENSE_HOTSPOT_{CT}": summ[CT]["DENSE_HOTSPOT"],
          "full_coverage_f_in_done_for": sorted(f"{k[0]}:r{k[1]}_c{k[2]}" for k in full),
          "summary": summ, f"ks_control_vs_{TG}_per_tile": ks,
          "rot90_null": {"radial_stats_identical_and_directional_swapped_all_tiles": rot_ok,
                         "note": "n_hi, f_in and the radial autocorrelation are rotation-invariant by construction; the rot-90 "
                                 "copy only swaps the directional peaks, so it cannot separate text from non-text on these "
                                 "statistics. The discriminating null is the known-text control."},
          f"tiles_{TG}": S[TG], f"tiles_{CT}": S[CT], "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
if TG == "E2":
    ex = json.loads(__import__("subprocess").check_output(
        ["git", "show", "origin/claude/gifted-bell-gavnl5-sib-p4-excl:logs/sib/p4-excl/excl_a.json"], cwd=repo))["tiles"]
    kc = json.load(open(os.path.join(out, "kedge_coverage_e2.json")))["tiles_with_any_coverage"]
    for x in S[TG]:
        x["labelled_adjacent_union_excl_a"] = ex.get(x["tile"], {}).get("labelled_adjacent_union")
        x["frac_mesh_in_137keV_scan"] = kc.get(x["tile"], 0.0)
        x["title_zone_c10_c17"] = 10 <= x["c"] <= 17
    tz = [x for x in S[TG] if x["title_zone_c10_c17"]]
    screen["title_zone_c10_c17"] = {
        "tiles": len(tz), "DENSE_HOTSPOT": [x["tile"] for x in tz if x["DENSE_HOTSPOT"]],
        "n_gt_control_p99": [x["tile"] for x in tz if x["n_hi_gt_control_p99"]],
        "n_hi_per_1e6_voxels": q([x["n_hi_per_1e6_voxels"] for x in tz]),
        "f_in_sample": q([x["f_in_sample"]["f_in_sample"] for x in tz]),
        "components_letter_scale_total": int(sum(x["stroke"].get("components_letter_scale_0p5_5mm", 0) for x in tz)),
        "comp_extent_mm_max": q([x["stroke"].get("comp_extent_mm_max") for x in tz]),
        "acf_radial_peak_2_4mm": q([x["acf_radial_peak_2_4mm"] for x in tz]),
        "labelled_adjacent_tiles": [x["tile"] for x in tz if x["labelled_adjacent_union_excl_a"]],
        "note": "labelled-adjacency is reported, not excluding (DECL-P4-12 item 3)"}
    screen["tiles_" + TG] = S[TG]
json.dump(screen, open(os.path.join(out, f"screen{SUF}.json"), "w"), indent=1)
if TG != "E1":
    print(json.dumps({"p99": p99, "hot": summ[TG]["DENSE_HOTSPOT"], "hot_ctrl": summ[CT]["DENSE_HOTSPOT"],
                      "n_gt_p99": summ[TG]["n_gt_control_p99"], "rot_ok": rot_ok, "title_zone": screen.get("title_zone_c10_c17")}))
    sys.exit()

# f1 manifest (p4-tiles-b e1 format)
meta = []
seg = C.MATERIALS["E1"]["seg"]
for k in (".zattrs", ".zgroup", "0/.zarray"):
    b = C.get(f"{C.sv_prefix(seg)}/{k}")
    meta.append({"key": f"PHercParis4/segments/{seg}/{C.SV_NAME}/{k}", "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
mesh_inputs = json.load(open(os.path.join(scr, "valid_E1.npy.json")))
g = C.git_json(C.MATERIALS["E1"]["grid"])
tiles = []
for t in sorted(recs["E1"], key=lambda d: (d["r"], d["c"])):
    assert abs(t["valid_fraction"] - t["valid_fraction_src"]) < 1e-9, (t["r"], t["c"])
    tiles.append({"r": t["r"], "c": t["c"], "file": t["file"], "png_sha256": t["png_sha256"], "png_bytes": t["png_bytes"],
                  "valid_fraction": t["valid_fraction"], "frac_outside": t["frac_outside"],
                  "canvas_rows": t["canvas_rows"], "canvas_cols": t["canvas_cols"],
                  "stats": {"frac_mesh_points_outside_1129_volume": t["frac_outside"], "n_hi": t["n_hi"],
                            "mip_mean_valid": t["mip_mean"], "mip_std_valid": t["mip_std"],
                            "frac_valid_mip_zero": t["frac_mip_zero"], "frac_valid_mip_gt_T_hi": t["frac_mip_gt_T_hi"],
                            "frac_valid_mip_255": t["frac_mip_255"], "frac_valid_in_absent_chunk": t["frac_valid_in_absent_chunk"],
                            "chunks_absent": t["chunks_absent"], "chunks": t["chunks"],
                            "disp_frac_255": t["disp_frac_255"], "disp_frac_0_valid": t["disp_frac_0_valid"]}})
man = {"provenance": C.PROV, "serves": "RULES.md DECL-P4-6 P4-F on E1; sibling task p4-highz", "segment": seg,
       "material": f"official surface volume PHercParis4/segments/{seg}/{C.SV_NAME} (raw CT, no model)",
       "level_used": 0, "level_inplane_um": 2.258,
       "slab": {"n_slices": 116, "centre_index": 58, "centre_rule": "n//2 (p4-tiles-b convention)", "slices": [52, 64],
                "count": 13, "half_width_um": 6 * 2.258, "depth_step_um": 2.258, "projection": "maximum"},
       "thresholds": {"T_mid": th["T_mid"], "T_hi": T_hi, "file": "logs/sib/p4-highz/thresholds.json"},
       "px_per_mm": g["px_per_mm"], "T_px": g["T_px"], "tile_grid_rows_cols": g["tile_grid_rows_cols"],
       "grid_source": "p4-tiles-b e1/grid.json (reused exactly; valid fractions recomputed and equal to the source manifest)",
       "display": {"values": "clip(255 (max - T_mid) / (T_hi - T_mid), 0, 255) at level 0 (float32), 0 outside mesh-valid",
                   "downscale": "cv2.resize INTER_AREA (float32) from T x T to 1068 x 1068, then rounded to uint8",
                   "px_per_mm": 53.4, "encoder": "builder.png_bytes; chunks IHDR/IDAT/IEND only (asserted)"},
       "eligibility": g["eligibility"], "tiles_total": g["tiles_total"], "tiles_eligible": len(tiles),
       "inputs": meta + mesh_inputs,
       "chunk_reads": "HTTP range reads of slices 52..64 of every level-0 chunk of each tile; 404 = absent, fill 0; "
                      "no per-chunk hash recorded (range reads)",
       "viewing": "no image, tile or CT pixel was opened, displayed or described by the builder",
       "naming_note": "files named <segment>_r<r>_c<c>.png; flat uuid naming and key are the orchestrator's step",
       "tiles": tiles, "utc": screen["utc"]}
json.dump(man, open(os.path.join(out, "f1", "manifest.json"), "w"), indent=1)
print(json.dumps({"p99": p99, "hot_E1": summ["E1"]["DENSE_HOTSPOT"], "hot_C": summ["C"]["DENSE_HOTSPOT"],
                  "n_gt_p99_E1": summ["E1"]["n_gt_control_p99"], "tiles": len(tiles), "rot_ok": rot_ok}))
