# Provenance: Project HERCULES | owner the owner | [id removed]
"""CHAIN VALID prep, step 1: map the three organizer 9.366 um meshes to the 2.403 um frame with the frozen
non-affine map (logs/sib/reg0841na/field_final.json, REG-0841-NA), on the organizer's own 2.4 um UV grid,
so pixels line up with the organizer ink map and labels (canvas px c <-> grid g = (c + 0.5)/20;
c9 = (c2 + 10) N9/N2 - 10, B0841-BANK).
Exclusion (T shell + render slab, DECL-D3-A2 / CORR-RETRACE-RULE): a node is kept only if its 9 um point is
>= 168 vox from the J points of jexcl.py (0.25-node samples; <= 3.6 vox sampling gap + 1 vox bilinear-vs-
triangulated slack => point-to-surface >= 150); a rendered pixel interpolates 4 nodes <= 5.2 9um vox apart,
and the -n 63 slab adds <= 31 rescan vox (8 9um vox) along the normal: all rendered samples stay
>= 155 + 13 - 13 = 155 when the node threshold is 168 (155 + 5.2 + 8, rounded; raised to 172 after the fail-closed surface check clearance_check.json found 143.8 vox under 168), i.e. every rendered sample is >= 150 vox point-to-surface from J (>= 144 required).
Nodes whose rescan z would put the slab outside the volume (z < 31 or > 15120 - 31) are also dropped.
Writes /work/cv/mesh/<seg>/ (tifxyz) and logs/sib/reg0841/chainvalid/map_meshes.json (numbers only)."""
import json, os, sys
import numpy as np, tifffile
sys.path.insert(0, "/home/user/dominion/tools/sib/reg0841na"); sys.path.insert(0, "/home/user/dominion/tools/sib/reg0841")
from field import load_final
from jexcl import JExcl, SEGID
MAP, FD = load_final()
J = JExcl()
THR = 172.0
OUT = "/work/cv/mesh"; REPO = "/home/user/dominion"
F9, F2 = "20250821151531-9.366um", "20260319124803-2.403um"


def load(seg, frame):
    ts = seg.split("-")[0]; d = f"/work/reg/mesh/{seg}/mesh/{ts}-on-{frame}.tifxyz"
    P = np.stack([tifffile.imread(f"{d}/{a}.tif").astype(np.float64) for a in "xyz"], -1)
    return P, ~np.all(P == -1, -1) & (P[..., 2] > 0), json.load(open(f"{d}/meta.json"))


def bil(P, V, r, c):
    H, W = V.shape
    r0 = np.clip(np.floor(r).astype(int), 0, H - 2); c0 = np.clip(np.floor(c).astype(int), 0, W - 2)
    fr = (r - r0)[:, None]; fc = (c - c0)[:, None]
    ok = V[r0, c0] & V[r0 + 1, c0] & V[r0, c0 + 1] & V[r0 + 1, c0 + 1] & (r >= 0) & (c >= 0) & (r <= H - 1) & (c <= W - 1)
    return P[r0, c0] * (1 - fr) * (1 - fc) + P[r0 + 1, c0] * fr * (1 - fc) + P[r0, c0 + 1] * (1 - fr) * fc + P[r0 + 1, c0 + 1] * fr * fc, ok


res = {"field": {"kind": FD["kind"], "loo_rms9": FD["loo_rms9"]}, "threshold_node_vox": THR, "segments": {}}
for key, seg in SEGID.items():
    P9, V9, _ = load(seg, F9); P2, V2, meta2 = load(seg, F2)
    N9 = np.array(V9.shape) * 20; N2 = np.array(V2.shape) * 20
    rr, cc = np.meshgrid(np.arange(V2.shape[0]), np.arange(V2.shape[1]), indexing="ij"); rr = rr.ravel(); cc = cc.ravel()
    cr2 = 20 * rr - 0.5; cc2 = 20 * cc - 0.5
    cr9 = (cr2 + 10) * N9[0] / N2[0] - 10; ccol9 = (cc2 + 10) * N9[1] / N2[1] - 10
    p9, ok = bil(P9, V9, (cr9 + 0.5) / 20, (ccol9 + 0.5) / 20)
    q = np.full_like(p9, -1.0)
    q[ok] = MAP.f(p9[ok])
    dJ = np.full(len(p9), np.inf); dJ[ok] = J.tree.query(p9[ok], distance_upper_bound=THR + 50)[0]
    inz = (q[:, 2] >= 31) & (q[:, 2] <= 15120 - 31)
    keep = ok & (dJ >= THR) & inz
    org = P2[rr, cc]; orgv = V2[rr, cc]
    both = keep & orgv
    d2 = np.linalg.norm(q[both] - org[both], axis=1)
    d9 = np.linalg.norm(np.linalg.solve(MAP.A, (q[both] - org[both]).T).T, axis=1)
    X = np.where(keep[:, None], q, -1.0).reshape(V2.shape + (3,)).astype(np.float32)
    od = f"{OUT}/{key}"; os.makedirs(od, exist_ok=True)
    for i, a in enumerate("xyz"):
        tifffile.imwrite(f"{od}/{a}.tif", X[..., i])
    qk = q[keep]
    m = dict(meta2); m["uuid"] = f"reg0841na-mapped-{key}"; m["bbox"] = [qk.min(0).tolist(), qk.max(0).tolist()]
    m["hercules"] = "organizer 9.366 um mesh mapped with reg0841na field_final.json on the organizer 2.4 um UV grid; nodes < 172 vox from J removed"
    m.pop("area_vx2", None)
    json.dump(m, open(f"{od}/meta.json", "w"), indent=1)
    area_px = keep.sum() * 400  # 20x20 canvas px per node (approx.)
    res["segments"][key] = dict(segment=seg, grid2=list(V2.shape), n_nodes_valid9=int(ok.sum()), n_nodes_kept=int(keep.sum()),
                                n_dropped_J=int((ok & (dJ < THR)).sum()), n_dropped_z=int((ok & ~inz & (dJ >= THR)).sum()),
                                area_kept_cm2_approx=float(area_px * (2.403e-4) ** 2),
                                resid_vs_organizer_2p4_mesh=dict(n=int(both.sum()), rescanvox_median=float(np.median(d2)),
                                    rescanvox_p95=float(np.percentile(d2, 95)), rescanvox_max=float(d2.max()),
                                    vox9_median=float(np.median(d9)), vox9_p95=float(np.percentile(d9, 95)), vox9_max=float(d9.max())),
                                min_J_dist_kept=float(dJ[keep].min()), z2_range=[float(qk[:, 2].min()), float(qk[:, 2].max())])
    print(key, json.dumps(res["segments"][key]), flush=True)
json.dump(res, open(f"{REPO}/logs/sib/reg0841/chainvalid/map_meshes.json", "w"), indent=1)
