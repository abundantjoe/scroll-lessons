# Provenance: Project HERCULES | owner the owner | [id removed]
"""Levelling of the mapped 2.4 um meshes (src/hercules/geometry/level_mesh.level_mesh, step 20 vox, global
median angle) and the exact canvas correspondence organizer canvas <-> levelled canvas.
Grid <-> canvas: c = 20 g - 0.5 (g = (c + 0.5)/20) on both canvases (tifxyz scale 0.05).
Levelled node (i', j') sits at source grid (u, v) = U e_u + V e_v with U = U0 + du j', V = V0 + dv i'
(orthonormal e_u, e_v, det +1), so source (u, v) -> j' = (u e_u0 + v e_u1 - U0)/du, i' = (u e_v0 + v e_v1 - V0)/dv."""
import json, os, sys
import numpy as np, tifffile
sys.path.insert(0, "/home/user/dominion/src")
from hercules.geometry.level_mesh import level_mesh


def level_segment(key, src="/work/cv/mesh", dst="/work/cv/mesh_lev"):
    P = np.stack([tifffile.imread(f"{src}/{key}/{a}.tif") for a in "xyz"], -1).astype(np.float64)
    L = level_mesh(P, step_vox=20.0)
    od = f"{dst}/{key}"; os.makedirs(od, exist_ok=True)
    for i, a in enumerate("xyz"):
        tifffile.imwrite(f"{od}/{a}.tif", L.points[..., i].astype(np.float32))
    m = json.load(open(f"{src}/{key}/meta.json")); m["uuid"] = m["uuid"] + "-levelled"
    ok = L.points[..., 0] != -1
    m["bbox"] = [L.points[ok].min(0).tolist(), L.points[ok].max(0).tolist()]
    json.dump(m, open(f"{od}/meta.json", "w"), indent=1)
    T = dict(angle_deg=L.angle_deg, spread_deg=L.spread_deg, e_u=L.e_u.tolist(), e_v=L.e_v.tolist(), origin=list(L.origin),
             du=L.du, dv=L.dv, step_vox=L.step_vox, metric=list(L.metric), shape=list(L.points.shape[:2]))
    json.dump(T, open(f"{od}/level_transform.json", "w"), indent=1)
    return L, T


def org_px_to_lev_px(T, r, c):
    """Organizer canvas px (row, col) -> levelled canvas px (row', col')."""
    v = (np.asarray(r, float) + 0.5) / 20; u = (np.asarray(c, float) + 0.5) / 20
    eu, ev = T["e_u"], T["e_v"]; U0, V0 = T["origin"]
    jp = (u * eu[0] + v * eu[1] - U0) / T["du"]; ip = (u * ev[0] + v * ev[1] - V0) / T["dv"]
    return 20 * ip - 0.5, 20 * jp - 0.5


def lev_px_to_org_px(T, rp, cp):
    ip = (np.asarray(rp, float) + 0.5) / 20; jp = (np.asarray(cp, float) + 0.5) / 20
    U = T["origin"][0] + T["du"] * jp; V = T["origin"][1] + T["dv"] * ip
    u = U * T["e_u"][0] + V * T["e_v"][0]; v = U * T["e_u"][1] + V * T["e_v"][1]
    return 20 * v - 0.5, 20 * u - 0.5
