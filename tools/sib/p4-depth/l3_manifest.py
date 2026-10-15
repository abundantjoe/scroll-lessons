"""P4-L3 manifest.json from worker census files (p4-l2 l2/l2s manifest format). Numbers and hashes only.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: l3_manifest.py <l3_dir> <l2_manifest.json> <calib.json> <calib_params.json> <mesh_dir>
Writes <l3_dir>/manifest.json with "partial": true until all 160 eligible tiles are present.
"""
import hashlib
import json
import os
import sys

d, l2m_p, cal_p, par_p, mesh = sys.argv[1:6]
l2m = json.load(open(l2m_p))
cal = json.load(open(cal_p))
ref = {(t["r"], t["c"]): t for t in l2m["tiles"]}
cen = {}
for fn in sorted(os.listdir(d)):
    if fn.startswith("census_w") and fn.endswith(".jsonl"):
        for line in open(os.path.join(d, fn)):
            x = json.loads(line)
            k = (x["r"], x["c"])
            assert k not in cen or cen[k]["png_sha256"] == x["png_sha256"], ("conflicting tile", k)
            cen[k] = x
keys = sorted(cen)
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()  # noqa: E731
za, zb = cal["l3_slices_inclusive"]
checks = {"n_tiles_built": len(keys), "n_eligible_ref": len(ref), "all_ref_eligible_built": set(keys) == set(ref),
          "built_subset_of_ref_eligible": set(keys) <= set(ref),
          "valid_fraction_equal_l2": all(cen[k]["valid_fraction"] == ref[k]["valid_fraction"] for k in keys),
          "valid_px_equal_l2": all(cen[k]["stats"]["valid_px"] == ref[k]["stats"]["valid_px"] for k in keys),
          "png_sha256_recomputed_ok": all(sha(os.path.join(d, cen[k]["file"])) == cen[k]["png_sha256"] for k in keys),
          "png_only_IHDR_IDAT_IEND": all(set(cen[k]["png_chunks"]) <= {"IHDR", "IDAT", "IEND"} for k in keys),
          "file_names_equal_l2": all(cen[k]["file"] == ref[k]["file"] for k in keys)}
keep = ("file", "r", "c", "png_sha256", "png_bytes", "valid_fraction", "canvas_rows", "canvas_cols", "stats",
        "chunks_read", "chunks_missing", "raw_max_sha256")
man = {"provenance": "Project HERCULES | owner the owner | [id removed]",
       "declaration": "RULES.md DECL-P4-12-A3 (P4-L3, depth-calibrated thin-slab channel)",
       "partial": not checks["all_ref_eligible_built"],
       "segment": l2m["segment"], "surface_volume": l2m["surface_volume"],
       "input_sha256": {**{k: v for k, v in l2m["input_sha256"].items() if "mesh" in k},
                        "mesh_recomputed": {n: sha(os.path.join(mesh, n)) for n in ("meta.json", "x.tif", "y.tif", "z.tif")},
                        "l2_manifest.json": sha(l2m_p), "calib.json": sha(cal_p), "calib_params.json": sha(par_p)},
       "grid_source": l2m["grid_source"], "level_used": 0,
       "calibration": {"d_star_um": cal["d_star_um"], "z_star": cal["z_star"], "z_peak": cal["z_peak"],
                       "verdict": cal["verdict"], "d_star_side": cal["sides"]["d_star_side"],
                       "recto_verso_of_d_star": cal.get("recto_verso_of_d_star"),
                       "calibration_specificity": cal.get("calibration_specificity")},
       "slab": {"slices": [za, zb], "centre": cal["z_star"], "n": zb - za + 1,
                "um": [round((za - 54) * 2.4, 1), round((zb - 54) * 2.4, 1)],
                "rule": "|z - z*| * 2.4 um <= 10 um (DECL-P4-12-A3 item 2)"},
       "projection": "max over the L3 slab of level-0 uint8 voxels per canvas px; 404 chunk = 0",
       "display": "per tile: hercules.display.builder.linear_window_ct (linear 1-99 % np.percentile) over mesh-valid "
                  "canvas px with L3 max > 0; 0 outside mesh-valid and where max == 0 (as L2S, DECL-P4-5-A1 rule); "
                  "cv2.INTER_AREA 8343 -> 1068; uint8 PNG IHDR/IDAT/IEND",
       "checks": checks, "n_tiles": len(keys), "tiles": [{k: cen[t][k] for k in keep} for t in keys],
       "missing": [list(k) for k in sorted(set(ref) - set(keys))], "ineligible": l2m.get("ineligible", [])}
json.dump(man, open(os.path.join(d, "manifest.json"), "w"), indent=1)
print(json.dumps(checks), "partial" if man["partial"] else "COMPLETE")
