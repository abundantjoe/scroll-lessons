"""p4-highz: per-tile coverage of the E2 (strip a) grid by the 137 keV 2.4 um scan, which with the 78 keV scans
brackets the Au/Hg/Pb K-edges (scans.json). Geometry only; no K-edge map (needs its own declaration).

Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python kedge_cov.py <scratch> <repo>
"""
import json
import os
import sys
import time

import numpy as np
import tifffile

sys.path.insert(0, os.path.dirname(__file__))
import common as C  # noqa: E402

scr, repo = sys.argv[1], sys.argv[2]
sc = json.load(open(os.path.join(repo, "logs/sib/p4-highz/scans.json")))
V137 = "20260323153942-2.400um-0.2m-137keV-masked"
REF = "20260411134726-2.400um-0.2m-78keV-masked"
A = lambda M: np.vstack([np.array(M), [0, 0, 0, 1]])
to_ref_137 = np.linalg.inv(A(sc["volumes"][REF]["registration"]["matrix_moving_to_fixed_xyz"])) @ A(
    sc["volumes"][V137]["registration"]["matrix_moving_to_fixed_xyz"])
inv = np.linalg.inv(to_ref_137)
Z, Y, X = sc["volumes"][V137]["shape_zyx_level0"]
g = C.git_json(C.MATERIALS["E2"]["grid"], C.MATERIALS["E2"]["ref"])
T = g["T_canvas_px"]
key = C.mesh_key(C.MATERIALS["E2"]["seg"], "20260411134726-2.4um")
arr = []
for a in "xyz":
    b = C.get(f"{C.BUCKET}/{key}/{a}.tif")
    p = os.path.join(scr, f"kc_{a}.tif")
    open(p, "wb").write(b)
    arr.append(tifffile.imread(p).astype(np.float64))
    os.remove(p)
ok = (arr[0] != -1) & (arr[1] != -1) & (arr[2] != -1)
gi, gj = np.nonzero(ok)
P = np.stack([a[ok] for a in arr], 1)
Q = (inv[:3, :3] @ P.T).T + inv[:3, 3]
inside = (Q[:, 0] >= 0) & (Q[:, 0] < X) & (Q[:, 1] >= 0) & (Q[:, 1] < Y) & (Q[:, 2] >= 0) & (Q[:, 2] < Z)
r, c = gi * 20 // T, gj * 20 // T
nr, nc = g["tile_grid"]["n_rows"], g["tile_grid"]["n_cols"]
tot = np.zeros((nr, nc)); ins = np.zeros((nr, nc))
np.add.at(tot, (r, c), 1); np.add.at(ins, (r, c), inside)
frac = np.where(tot > 0, ins / np.maximum(tot, 1), np.nan)
tiles = {f"r{i}_c{j}": float(frac[i, j]) for i in range(nr) for j in range(nc) if tot[i, j] > 0 and frac[i, j] > 0}
out = {"provenance": C.PROV, "serves": "DECL-P4-6-A1 item 2 (inventory; geometry only)", "scan_137keV": V137,
       "grid": "E2 strip a, T 8343, mesh vertex (gi, gj) -> tile (gi*20 // T, gj*20 // T)",
       "valid_vertices": int(ok.sum()), "frac_inside_137keV_extent": float(inside.mean()),
       "tiles_with_any_coverage": tiles,
       "title_zone_c10_c17_coverage": {k: v for k, v in tiles.items() if 10 <= int(k.split("_c")[1]) <= 17},
       "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
json.dump(out, open(os.path.join(repo, "logs/sib/p4-highz/kedge_coverage_e2.json"), "w"), indent=1)
print(json.dumps({k: out[k] for k in ("frac_inside_137keV_extent", "tiles_with_any_coverage", "title_zone_c10_c17_coverage")}))
