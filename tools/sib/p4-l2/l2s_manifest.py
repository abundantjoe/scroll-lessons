"""P4-L L2S manifest.json from worker census files (pairs0814b e2 manifest format). Numbers and hashes only.

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: l2s_manifest.py <l2s_dir> <l2_dir>
"""
import hashlib
import json
import os
import sys

d, l2d = sys.argv[1:3]
l2m = json.load(open(os.path.join(l2d, "manifest.json")))
ref = {(t["r"], t["c"]): t for t in l2m["tiles"]}
cen = {}
for fn in sorted(os.listdir(d)):
    if fn.startswith("census_w") and fn.endswith(".jsonl"):
        for l in open(os.path.join(d, fn)):
            x = json.loads(l)
            cen[(x["r"], x["c"])] = x
keys = sorted(cen)
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()  # noqa: E731
checks = {"n_tiles_built": len(keys), "n_eligible_ref": len(ref), "all_ref_eligible_built": set(keys) == set(ref),
          "built_subset_of_ref_eligible": set(keys) <= set(ref),
          "valid_fraction_equal_l2": all(cen[k]["valid_fraction"] == ref[k]["valid_fraction"] for k in keys),
          "l2_png_rebuilt_equal_all": all(cen[k]["l2_png_rebuilt_equal"] for k in keys),
          "png_sha256_recomputed_ok": all(sha(os.path.join(d, cen[k]["file"])) == cen[k]["png_sha256"] for k in keys),
          "png_only_IHDR_IDAT_IEND": all(set(cen[k]["png_chunks"]) <= {"IHDR", "IDAT", "IEND"} for k in keys)}
keep = ("file", "r", "c", "png_sha256", "png_bytes", "valid_fraction", "canvas_rows", "canvas_cols", "stats",
        "chunks_read", "chunks_missing", "raw_npz", "raw_npz_sha256", "raw_npz_bytes", "raw_max_sha256",
        "l2_png_rebuilt_equal")
man = {"provenance": "Project HERCULES | owner the owner | [id removed]",
       "declaration": "RULES.md DECL-P4-12-A2 (L2S); channel DECL-P4-12 item 1 / DECL-P4-6 item 2",
       "partial": not checks["all_ref_eligible_built"],
       "segment": l2m["segment"], "surface_volume": l2m["surface_volume"],
       "input_sha256": {**l2m["input_sha256"], "l2_manifest.json": sha(os.path.join(l2d, "manifest.json"))},
       "grid_source": l2m["grid_source"], "level_used": 0, "slab": l2m["slab"], "projection": l2m["projection"],
       "display": "per tile: hercules.display.builder.linear_window_ct (linear 1-99 % np.percentile) over mesh-valid "
                  "canvas px with slab max > 0; 0 outside mesh-valid and where max == 0 (DECL-P4-5-A1 rule); "
                  "cv2.INTER_AREA 8343 -> 1068; uint8 PNG IHDR/IDAT/IEND",
       "raw_store": "unstretched slab max (uint8 8343 x 8343, key 'max') and mesh-valid mask (key 'valid') per tile, "
                    "np.savez_compressed; kept in the builder container at /work/l2/raw (too large for git, ~41 MB "
                    "each); sha256 of the npz bytes and of the raw max array bytes recorded per tile",
       "checks": checks, "n_tiles": len(keys), "tiles": [{k: cen[t][k] for k in keep} for t in keys],
       "missing": [list(k) for k in sorted(set(ref) - set(keys))], "ineligible": l2m.get("ineligible", [])}
json.dump(man, open(os.path.join(d, "manifest.json"), "w"), indent=1)
print(json.dumps(checks), "partial" if man["partial"] else "COMPLETE")
