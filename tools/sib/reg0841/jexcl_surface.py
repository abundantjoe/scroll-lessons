# Provenance: Project HERCULES | owner the owner | [id removed]
"""Re-check of the J clearance under CORR-RETRACE-RULE (fail-closed; point-to-surface distance).
Surface: the 9 um organizer J-window meshes triangulated (each grid quad with 4 valid nodes split into
two triangles; windows grown by 1 node, as in jexcl.py). For every planned patch box (48x256x256 block
grown by PAD = 6 vox), the box-to-surface distance is bounded from below by densely sampling every
triangle near the box (barycentric step 1/24 of each edge, spacing <= ~1 vox for 20-vox edges) and
subtracting the sampling gap bound (max edge length / 24). Reported clearance = min(surface lower bound,
densified-vertex distance of jexcl.py). Admissible iff clearance >= 144 vox (limit); margin also reported."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from jexcl import JExcl, load9, SEGID, WIN, LIMIT, MARGIN
from scipy.spatial import cKDTree

REPO = "/home/user/dominion"
PAD = 6; N = 24
bank = json.load(open(f"{REPO}/logs/bank0841/summary.json"))["J"]
tris = []
for j, w in bank.items():
    P = load9(SEGID[w["segment"]]); V = ~np.all(P == -1, -1) & (P[..., 2] > 0)
    r0 = int(np.floor((w["y0"] - 20 + 0.5) / 20)); r1 = int(np.ceil((w["y0"] + WIN + 20 + 0.5) / 20))
    c0 = int(np.floor((w["x0"] - 20 + 0.5) / 20)); c1 = int(np.ceil((w["x0"] + WIN + 20 + 0.5) / 20))
    r0, c0 = max(r0, 0), max(c0, 0); r1, c1 = min(r1, V.shape[0] - 1), min(c1, V.shape[1] - 1)
    for r in range(r0, r1):
        for c in range(c0, c1):
            a, b, cc, d = (r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)
            for t in ((a, b, cc), (b, d, cc)):
                if all(V[k] for k in t):
                    tris.append([P[k] for k in t])
T = np.array(tris)  # (n, 3 vertices, xyz)
cent = T.mean(1); rad = np.linalg.norm(T - cent[:, None], axis=2).max(1)
emax = float(np.max([np.linalg.norm(T[:, i] - T[:, (i + 1) % 3], axis=1).max() for i in range(3)]))
gap = emax / N
# barycentric sample grid
u, v = np.meshgrid(np.arange(N + 1), np.arange(N + 1)); m = u + v <= N
bary = np.c_[u[m], v[m], N - u[m] - v[m]] / N
tree = cKDTree(cent)
J = JExcl()
plan = json.load(open(f"{REPO}/logs/sib/reg0841/patch_plan.json"))
rows = []
for p in plan["patches"]:
    x, y, z = p["centre_xyz"]
    lo = np.array([x - 128 - PAD, y - 128 - PAD, z - 24 - PAD]); hi = np.array([x + 128 + PAD, y + 128 + PAD, z + 24 + PAD])
    cb = (lo + hi) / 2; hb = (hi - lo) / 2
    R = np.linalg.norm(hb) + 400 + rad.max()
    idx = tree.query_ball_point(cb, R)
    dsurf = float("inf")
    if idx:
        # prune: triangle lower bound = centroid box distance - radius
        cd = np.linalg.norm(np.maximum(np.abs(cent[idx] - cb) - hb, 0), axis=1) - rad[idx]
        order = np.argsort(cd); idx = np.array(idx)[order]; cd = cd[order]
        for k0 in range(0, len(idx), 2000):
            if cd[k0] - gap >= dsurf:
                break
            tt = T[idx[k0:k0 + 2000]]
            pts = np.einsum("sk,tkd->tsd", bary, tt).reshape(-1, 3)
            dd = np.linalg.norm(np.maximum(np.abs(pts - cb) - hb, 0), axis=1).min() - gap
            dsurf = min(dsurf, float(dd))
    dvert = J.box_dist(lo, hi)
    clear = min(dsurf, dvert)
    rows.append(dict(id=p["id"], role=p["role"], surface_lower_bound=dsurf if np.isfinite(dsurf) else "gt_%d" % int(R - np.linalg.norm(hb) - rad.max()),
                     densified_vertex=dvert if np.isfinite(dvert) else "gt_206", clearance=clear if np.isfinite(clear) else None,
                     admissible=bool(clear >= LIMIT)))
fin = [r["clearance"] for r in rows if r["clearance"] is not None]
out = dict(rule="CORR-RETRACE-RULE fail-closed: min(point-to-triangulated-surface lower bound, densified-vertex)",
           n_triangles=int(len(T)), max_edge_vox=emax, sampling_gap_bound_vox=gap, pad_vox=PAD, limit_vox=LIMIT,
           min_clearance=min(fin), all_admissible=all(r["admissible"] for r in rows),
           n_with_surface_within_search=len(fin), rows=rows)
json.dump(out, open(f"{REPO}/logs/sib/reg0841/jexcl_surface_check.json", "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
for r in rows:
    if r["clearance"] is not None: print(r)
