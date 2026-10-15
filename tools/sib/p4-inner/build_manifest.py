"""Assemble a P4 outer-strip manifest (same format as logs/sib/p4-inner/mout/manifest.json) from builder outputs.
Provenance: Project HERCULES | owner the owner | [id removed]
usage: build_manifest.py <work_dir with downloads.jsonl and out/> <dest_dir> <declaration text>
"""
import json, os, shutil, sys
W, D, decl = sys.argv[1:4]
os.makedirs(f"{D}/tiles", exist_ok=True)
S3 = "s3://vesuvius-challenge-open-data/"
g = json.load(open(f"{W}/out/grid.json")); geo = json.load(open(f"{W}/out/tile_geom.json")); dr = json.load(open(f"{W}/out/direction.json"))
L = [json.loads(l) for l in open(f"{W}/downloads.jsonl")]
e = lambda d: {"path": S3 + d["key"], "bytes": d["bytes"], "sha256": d["sha256"]}
cen = [json.loads(l) for l in open(f"{W}/out/tile_census.jsonl")]
tiles, inel = [], []
for t in cen:
    if not t["eligible"]:
        inel.append({"r": t["r"], "c": t["c"], "valid_fraction": t["valid_fraction"]}); continue
    gm = geo["tiles"][f"r{t['r']}_c{t['c']}"]
    shutil.copy(f"{W}/out/{t['file']}", f"{D}/{t['file']}")
    tiles.append({k: t[k] for k in ("r", "c", "valid_fraction", "file", "png_sha256", "png_bytes", "valid_px", "mean", "std", "frac_ge_150",
                                    "n_mesh_vertices_in_tile", "n_points_saved", "canvas_rows", "canvas_cols", "grid_rows", "grid_cols")}
                 | {k: gm[k] for k in ("median_z_mm", "median_r_mm", "r_mm_p10_p90", "min_dist_labelled_mm", "labelled_adjacent")})
blank = [(t["r"], t["c"]) for t in tiles if t["mean"] == 0 and t["std"] == 0]
p = [d for d in L if "ink-detection" in d["key"]][0]
m = {"provenance": "Project HERCULES | owner the owner | [id removed]", "declaration": decl,
     "segment": g["segment"], "volume": "20260411134726", "model": "20260417190342-new_canon_autoresearch_recipe",
     "prediction": e(p) | {"canvas_shape": g["canvas_shape"], "dtype": "uint8", "used_as_published": True, "local_copy_deleted_after_tiling": True},
     "mesh_tifxyz": {d["key"].split("/")[-1]: e(d) for d in L if "/mesh/" in d["key"]},
     "volume_metadata": {d["key"].split("/")[-1]: e(d) for d in L if "/volumes/" in d["key"]},
     "voxel_size_mm": g["voxel_size_mm"], "grid_shape": g["grid_shape"], "canvas_per_grid": g["scale_canvas_per_grid"]["rows"],
     "median_edge_vox": g["edge_length_vox"]["median"], "px_per_mm": g["px_per_mm"], "T_canvas_px": g["T_canvas_px"], "tile_mm": 20.0,
     "tile_grid": [g["tile_grid"]["n_rows"], g["tile_grid"]["n_cols"]],
     "eligible_rule": "valid_fraction >= 0.5 (canvas mask = grid mask nearest-neighbour x20; beyond canvas = invalid)",
     "display": "raw uint8 prediction, 0 outside mesh-valid, builder.area_downscale (cv2.INTER_AREA) to 1068 x 1068, builder.png_bytes (IHDR/IDAT/IEND only); 53.40 display px/mm",
     "stats_definition": "mean, std, frac_ge_150 over raw canvas pixels inside mesh-valid, before downscale",
     "tile_points": {"file": "tile_points.npz", "keys": "r<r>_c<c>", "content": "float32 (n,3) x,y,z in 20260411134726 voxels; seeded subsample [20260926,r,c], <= 4096"},
     "geometry": {"umbilicus": geo["sources"]["umbilicus"], "labelled_meshes": list(geo["sources"]["labelled_meshes"]),
                  "labelled_adjacent_rule": "min distance < 1.2 mm to any valid vertex of the 8 labelled 2.4um meshes",
                  "n_labelled_adjacent": sum(t["labelled_adjacent"] for t in tiles), "min_dist_labelled_mm_min": min(t["min_dist_labelled_mm"] for t in tiles)},
     "direction": {"per_tile_rule_pooled_spearman_col_vs_median_r_tie_averaged": geo["pooled_spearman_col_vs_median_r_tie_averaged"],
                   "per_row_spearman": {r: v["spearman_col_vs_median_r"] for r, v in geo["per_row"].items()},
                   "same_angle_crossing_check": {"n_pairs": dr["n_pairs"], "frac_r_increases_with_col": dr["frac_r_increases_with_col"], "outward": dr["outward_direction"]}},
     "blank_tiles_all_zero_prediction": {"n": len(blank), "rc": blank, "note": "prediction exactly 0 over the whole mesh-valid area; blank, not evidence of no ink"},
     "n_tiles_total": len(cen), "n_eligible": len(tiles), "ineligible": inel, "tiles": tiles}
json.dump(m, open(f"{D}/manifest.json", "w"), indent=1)
for f in ("grid.json", "tile_points.npz", "tile_census.jsonl", "tile_geom.json", "direction.json"):
    shutil.copy(f"{W}/out/{f}", f"{D}/{f}")
shutil.copy(f"{W}/downloads.jsonl", f"{D}/downloads.jsonl")
print(json.dumps({"segment": g["segment"], "eligible": len(tiles), "blank": len(blank), "adjacent": m["geometry"]["n_labelled_adjacent"],
                  "outward_crossing": dr["outward_direction"], "frac": dr["frac_r_increases_with_col"], "pooled_rho": geo["pooled_spearman_col_vs_median_r_tie_averaged"]}))
