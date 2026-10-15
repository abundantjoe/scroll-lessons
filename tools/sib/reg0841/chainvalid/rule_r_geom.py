# Provenance: Project HERCULES | owner the owner | [id removed]
"""Geometry side of rule R on 0841 (numbers only, no CT beyond the coarse mask, no ink).
Render normal (villa 41701aa vc_render_tifxyz): N = dP/dU x dP/dV with U = column, V = row (Geometry.cpp
grid_normal); --flip-normals (used, as chain2um) negates it: n_render = -(dP/dcol x dP/drow).
Umbilicus proxy (no official umbilicus for 0841 on S3): per 9 um L4 slice, the centroid of the scroll mask
(v9_L4 > 0), mapped to the rescan frame with the frozen field. r_out = horizontal (x, y) unit vector from the
proxy to the node. Reports per segment and per label crop: median of n_render . r_out, and the fraction of
nodes with positive sign. Writes logs/sib/reg0841/chainvalid/rule_r_geom.json."""
import json, sys
import numpy as np, tifffile
MESH = sys.argv[1] if len(sys.argv) > 1 else "/work/cv/mesh"
OUTF = sys.argv[2] if len(sys.argv) > 2 else "/home/user/dominion/logs/sib/reg0841/chainvalid/rule_r_geom.json"
sys.path.insert(0, "/home/user/dominion/tools/sib/reg0841na"); from field import load_final
MAP, FD = load_final()
REPO = "/home/user/dominion"
v4 = np.load("/work/reg/cache/v9_L4.npy", mmap_mode="r")
cen = {}
for k in range(int(12700 / 16), int(16750 / 16) + 1):
    m = np.asarray(v4[k]) > 0
    if m.sum() > 100:
        yy, xx = np.nonzero(m); cen[k] = (xx.mean() * 16 + 7.5, yy.mean() * 16 + 7.5, k * 16 + 7.5)
K = np.array(sorted(cen)); C9 = np.array([cen[k] for k in K]); C2 = MAP.f(C9)
LEV = "mesh_lev" in MESH
area = json.load(open(f"{REPO}/logs/sib/reg0841/chainvalid/" + ("area_lev.json" if LEV else "area.json")))
LABKEY = "core_E_px" if LEV else "core_sup_px"
out = {"umbilicus_proxy": "scroll-mask centroid per 9 um L4 slice, mapped with field_final",
       "proxy_xy_spread_rescanvox": [float(np.ptp(C2[:, 0])), float(np.ptp(C2[:, 1]))], "segments": {}}
for key in ("w00", "214732", "022814"):
    P = np.stack([tifffile.imread(f"{MESH}/{key}/{a}.tif") for a in "xyz"], -1).astype(np.float64)
    V = P[..., 0] != -1
    dU = np.zeros_like(P); dV = np.zeros_like(P)
    dU[:, 1:-1] = (P[:, 2:] - P[:, :-2]) / 2; dV[1:-1] = (P[2:] - P[:-2]) / 2
    ok = V.copy(); ok[:, 1:-1] &= V[:, 2:] & V[:, :-2]; ok[1:-1] &= V[2:] & V[:-2]; ok[[0, -1], :] = False; ok[:, [0, -1]] = False
    n = -np.cross(dU, dV); n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-12
    z = P[..., 2]
    cx = np.interp(z, C2[:, 2], C2[:, 0]); cy = np.interp(z, C2[:, 2], C2[:, 1])
    r = np.stack([P[..., 0] - cx, P[..., 1] - cy], -1); r /= np.linalg.norm(r, axis=-1, keepdims=True) + 1e-12
    d = n[..., 0] * r[..., 0] + n[..., 1] * r[..., 1]
    rec = dict(n_nodes=int(ok.sum()), median_n_dot_rout=float(np.median(d[ok])), frac_positive=float((d[ok] > 0).mean()),
               median_abs_nz=float(np.median(np.abs(n[..., 2][ok]))))
    crops = [c for c in area["segments"][key]["crops"] if c[LABKEY] > 0]
    rec["label_crops"] = []
    for c in crops:
        g0r, g1r = max(c["y"] + 128, 0) // 20, (c["y"] + 1920) // 20; g0c, g1c = max(c["x"] + 128, 0) // 20, (c["x"] + 1920) // 20
        sub = ok[g0r:g1r, g0c:g1c]; dd = d[g0r:g1r, g0c:g1c][sub]
        rec["label_crops"].append(dict(y=c["y"], x=c["x"], n_nodes=int(sub.sum()), median_n_dot_rout=float(np.median(dd)), frac_positive=float((dd > 0).mean())))
    out["segments"][key] = rec
    print(key, json.dumps(rec))
json.dump(out, open(OUTF, "w"), indent=1)
