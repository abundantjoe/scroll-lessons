"""P4-L manifest.json from the worker census files (pairs0814b e2 manifest format). Numbers and hashes only.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: l2_manifest.py <l2_dir> <e2_ref_manifest.json> <e2_grid.json> <mesh_dir> [<census dirs of sub-siblings> ...]
Writes <l2_dir>/manifest.json with "partial": true until all 160 eligible tiles are present.
"""
import hashlib
import json
import os
import sys

PROV = "Project HERCULES | owner the owner | [id removed]"
d, ref_p, grid_p, mesh = sys.argv[1:5]
extra = sys.argv[5:]
ref = json.load(open(ref_p))
ref_t = {(t["r"], t["c"]): t for t in ref["tiles"]}
th_p = os.path.join(d, "thresholds.json")
th = json.load(open(th_p))
cen = {}
for dd in [d] + extra:
    for fn in sorted(os.listdir(dd)):
        if fn.startswith("census_w") and fn.endswith(".jsonl"):
            for l in open(os.path.join(dd, fn)):
                x = json.loads(l)
                k = (x["r"], x["c"])
                assert k not in cen or cen[k]["png_sha256"] == x["png_sha256"], ("conflicting tile", k)
                cen[k] = x
bad = [k for k, x in cen.items() if hashlib.sha256(open(os.path.join(d, x["file"]), "rb").read()).hexdigest()
       != x["png_sha256"]]
keys = sorted(cen)
checks = {"n_tiles_built": len(keys), "n_eligible_ref": len(ref_t),
          "built_subset_of_ref_eligible": set(keys) <= set(ref_t),
          "all_ref_eligible_built": set(keys) == set(ref_t),
          "valid_fraction_equal_e2": all(cen[k]["valid_fraction"] == ref_t[k]["valid_fraction"] for k in keys),
          "valid_px_equal_e2": all(cen[k]["stats"]["valid_px"] == ref_t[k]["stats"]["valid_px"] for k in keys),
          "png_sha256_recomputed_ok": not bad,
          "png_only_IHDR_IDAT_IEND": all(set(cen[k]["png_chunks"]) <= {"IHDR", "IDAT", "IEND"} for k in keys)}
tiles = [{"file": cen[k]["file"], "r": k[0], "c": k[1], "png_sha256": cen[k]["png_sha256"],
          "png_bytes": cen[k]["png_bytes"], "valid_fraction": cen[k]["valid_fraction"],
          "canvas_rows": cen[k]["canvas_rows"], "canvas_cols": cen[k]["canvas_cols"], "stats": cen[k]["stats"],
          "chunks_read": cen[k]["chunks_read"], "chunks_missing": cen[k]["chunks_missing"]} for k in keys]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()  # noqa: E731
man = {"provenance": PROV, "declaration": "RULES.md DECL-P4-12 (P4-L); channel DECL-P4-6 item 2",
       "partial": not checks["all_ref_eligible_built"],
       "segment": "20260701183124-w010-027",
       "surface_volume": "s3://vesuvius-challenge-open-data/PHercParis4/segments/20260701183124-w010-027/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr",
       "input_sha256": {**{k: v for k, v in ref["input_sha256"].items() if "mesh/" in k},
                        "mesh_recomputed": {n: sha(os.path.join(mesh, n)) for n in ("meta.json", "x.tif", "y.tif", "z.tif")},
                        "params.json": sha(os.path.join(d, "params.json")), "thresholds.json": sha(th_p),
                        "e2_ref_manifest.json": sha(ref_p), "e2_grid.json": sha(grid_p)},
       "grid_source": "pairs0814b e2 cc81a677 (strip-a grid, T 8343, origin (0, 0)); eligibility = its 160 tiles",
       "level_used": 0, "slab": {"slices": [48, 60], "centre": 54, "n": 13, "um": [-14.4, 14.4]},
       "projection": "max over the slab of level-0 uint8 voxels per canvas px",
       "thresholds": {"T_mid": th["T_mid"], "T_hi": th["T_hi"], "source": th["material"]},
       "display": "clip(255*(max - T_mid)/(T_hi - T_mid), 0, 255), rint, uint8; 0 outside mesh-valid; cv2.INTER_AREA 8343 -> 1068; uint8 PNG IHDR/IDAT/IEND",
       "checks": checks, "n_tiles": len(tiles), "tiles": tiles,
       "missing": [list(k) for k in sorted(set(ref_t) - set(keys))],
       "ineligible": ref.get("ineligible", [])}
json.dump(man, open(os.path.join(d, "manifest.json"), "w"), indent=1)
print(json.dumps(checks), "partial" if man["partial"] else "COMPLETE")
