"""P4-E E2: manifest.json and grid.json from the census; checks against P4-B strip a (e25635c). Numbers only.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: e2_finalize.py <e2_dir> <strip_a_grid.json> <strip_a_manifest.json> [<l1_census.jsonl>]
"""
import hashlib, io, json, os, sys
import numpy as np
from PIL import Image

PROV = "Project HERCULES | owner the owner | [id removed]"
d, ga_p, ma_p = sys.argv[1:4]
ga, ma = json.load(open(ga_p)), json.load(open(ma_p))
cen = {}
for l in open(os.path.join(d, "census.jsonl")):
    r = json.loads(l); cen[(r["r"], r["c"])] = r
sa = {(t["r"], t["c"]): t for t in ma["tiles"]}
el = sorted(k for k, v in cen.items() if v["eligible"])
checks = {"n_census": len(cen), "n_eligible": len(el),
          "eligible_set_equals_strip_a": set(el) == set(sa),
          "valid_fraction_equal_strip_a": all(cen[k]["valid_fraction"] == sa[k]["valid_fraction"] for k in el),
          "valid_px_equal_strip_a": all(cen[k]["stats"]["valid_px"] == sa[k]["valid_px"] for k in el)}
bad = []
for k in el:
    p = os.path.join(d, cen[k]["file"])
    b = open(p, "rb").read()
    if hashlib.sha256(b).hexdigest() != cen[k]["png_sha256"]:
        bad.append(k)
checks["png_sha256_recomputed_ok"] = not bad
tiles = [{"file": cen[k]["file"], "r": k[0], "c": k[1], "png_sha256": cen[k]["png_sha256"],
          "png_bytes": cen[k]["png_bytes"], "valid_fraction": cen[k]["valid_fraction"],
          "canvas_rows": cen[k]["canvas_rows"], "canvas_cols": cen[k]["canvas_cols"],
          "stats": cen[k]["stats"], "chunks_read": cen[k]["chunks_read"],
          "chunks_missing": cen[k]["chunks_missing"]} for k in el]
za = {}
for l in open(os.path.join(d, "downloads.jsonl")):
    x = json.loads(l); za[x["key"].split(".zarr/")[-1] if ".zarr/" in x["key"] else x["key"]] = x["sha256"]
man = {"provenance": PROV, "declaration": "RULES.md DECL-P4-5 material E2",
       "segment": "20260701183124-w010-027",
       "surface_volume": "s3://vesuvius-challenge-open-data/PHercParis4/segments/20260701183124-w010-027/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr",
       "input_sha256": za, "level_used": 2, "slab": {"slices": [32, 76], "centre": 54, "n": 45, "um": [-52.8, 52.8]},
       "display": "linear 1-99 % over mesh-valid canvas px (builder.linear_window_ct), 0 outside, cv2.INTER_AREA 8343 -> 1068, uint8 PNG IHDR/IDAT/IEND",
       "checks": checks, "n_tiles": len(tiles), "tiles": tiles,
       "ineligible": [{"r": k[0], "c": k[1], "valid_fraction": v["valid_fraction"]} for k, v in sorted(cen.items()) if not v["eligible"]]}
g = {"provenance": PROV, "strip_a_grid_json_sha256": hashlib.sha256(open(ga_p, "rb").read()).hexdigest(),
     "strip_a_manifest_json_sha256": hashlib.sha256(open(ma_p, "rb").read()).hexdigest(), "strip_a_commit": "e25635c",
     **{k: ga[k] for k in ("segment", "voxel_size_mm", "grid_shape", "canvas_shape", "px_per_mm", "T_canvas_px", "tile_grid", "canvas_mask_rule")},
     "sv_mapping": {
         "level0_shape_zyx": [109, 69760, 170000], "zattrs_canvas_size_wh": [170000, 69760],
         "canvas_to_level0": "canvas px (i, j) = level-0 (row i, col j); in-plane shape equal to canvas_shape",
         "level2": "shape (109, 17440, 42500), scale (2.4, 9.6, 9.6) um, downsampling_method mean; canvas px (i, j) -> level-2 (i // 4, j // 4)",
         "depth": "109 slices at 2.4 um at every level; centre slice 54 = mesh surface (DECL-P4-5); slab 32..76"}}
if len(sys.argv) > 4:
    l1 = [json.loads(l) for l in open(sys.argv[4])][-1]
    k = (l1["r"], l1["c"])
    a = np.asarray(Image.open(os.path.join(d, cen[k]["file"])), np.float64)
    b = np.asarray(Image.open(sys.argv[4].replace("census_L1.jsonl", "") + l1["file"]), np.float64)
    m = (a > 0) | (b > 0)
    man["level1_crosscheck"] = {"tile": list(k), "l1_png_sha256": l1["png_sha256"], "l1_stats": l1["stats"],
        "mean_abs_diff_u8": float(np.abs(a - b)[m].mean()), "p99_abs_diff_u8": float(np.percentile(np.abs(a - b)[m], 99)),
        "pearson_r": float(np.corrcoef(a[m], b[m])[0, 1]), "note": "numbers only; images not viewed"}
json.dump(man, open(os.path.join(d, "manifest.json"), "w"), indent=1)
json.dump(g, open(os.path.join(d, "grid.json"), "w"), indent=1)
print(json.dumps(checks), json.dumps(man.get("level1_crosscheck", {}))[:400])
