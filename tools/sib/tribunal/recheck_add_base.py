# Provenance: Project HERCULES | owner the owner | [id removed]
"""Add one base-training trace (e.g. w028) to clearance part B without recomputing the existing pairs:
the same pair computation as recheck_clearances.part_b, restricted to the new trace, merged in; the
previous part B is kept under part_b_superseded. Mesh geometry only.

    python tools/sib/tribunal/recheck_add_base.py MESH_ROOT meshes_fetched.json recheck_clearances.json w028
"""
import copy
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from hercules.geometry.contamination import same_papyrus
from hercules.geometry.tifxyz import densify, read_tifxyz, valid_mask
from hercules.tribunal.preread import surface_distances

sys.path.insert(0, "tools/sib/tribunal")
from recheck_clearances import BANK_0139, BLANKS, W, canvas_pts  # noqa: E402

root, fetched, outp, tag = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text()), Path(sys.argv[3]), sys.argv[4]
ids = {k.split("/")[1]: v["mesh"] for k, v in fetched["segments"].items() if k.startswith("PHerc0139/") and "mesh" in v}
find = lambda t: sorted(s for s in ids if f"-{t}_" in s)  # noqa: E731
res = json.loads(outp.read_text())
old = copy.deepcopy(res["part_b"])
new_ids = find(tag)
apd_mesh, vox_cm2 = 16.0, (9.362e-4) ** 2
Bd = {s: densify(read_tifxyz(ids[s]).points.astype(np.float64), 5) for s in new_ids}
items = [("bank", find(t)[0], densify(read_tifxyz(ids[find(t)[0]]).points.astype(np.float64), 5)) for t in BANK_0139]
for name, (t, y0, x0) in BLANKS.items():
    p = read_tifxyz(ids[find(t)[0]]).points.astype(np.float64)
    g, v = canvas_pts(p, y0, y0 + 2136, x0, x0 + 2136)
    g[~v] = -1.0
    items.append(("blanks", name, g[::4, ::4]))
for key, name, A in items:
    per = res["part_b"][key][name]["vs_base"]
    for bid, B in Bd.items():
        lit = same_papyrus(A, B, workers=W)
        d = surface_distances(A, B, max_dist=3.0, workers=W)
        c = [int(np.sum(d < 1)), int(np.sum((d >= 1) & (d < 2))), int(np.sum((d >= 2) & (d < 3)))]
        sf = (c[0] + c[1]) >= 1000 and c[0] >= 2.0 * c[2]
        dv = cKDTree(B[valid_mask(B)]).query(A[valid_mask(A)], k=1, workers=W)[0]
        per[bid] = {"vertex_counts": list(lit.counts), "vertex_same": bool(lit.same), "surface_counts": c,
                    "surface_same": bool(sf), "same_corrected": bool(lit.same or sf),
                    "area_lt1_cm2": float(c[0] * apd_mesh * vox_cm2), "area_lt2_cm2": float((c[0] + c[1]) * apd_mesh * vox_cm2),
                    "min_surface_dist_vox": float(np.min(d)) if np.isfinite(d).any() else None,
                    "min_vertex_dist_vox": float(dv.min())}
        print(key, name[-22:], bid[-24:], per[bid]["surface_counts"], per[bid]["same_corrected"], round(per[bid]["min_vertex_dist_vox"], 2))
    e = res["part_b"][key][name]
    e["same_as"] = sorted(b for b, v in per.items() if v["same_corrected"])
    e["min_vertex_dist_to_any_base_vox"] = min(v["min_vertex_dist_vox"] for v in per.values())
    e["area_lt2_any_base_cm2_sum"] = sum(v["area_lt2_cm2"] for v in per.values())
res["part_b"]["base_training_traces"] = sorted(set(res["part_b"]["base_training_traces"]) | set(new_ids))
res.setdefault("part_b_superseded", []).append({"reason": f"base-training list lacked {tag}", "part_b": old})
outp.write_text(json.dumps(res, indent=1, sort_keys=True, default=float) + "\n", encoding="utf-8")
