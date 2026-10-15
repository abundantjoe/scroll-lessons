# Provenance: Project HERCULES | owner the owner | [id removed]
"""Retro-check of the two CT-only bench renders (made from the THR = 168 mesh of 214732): every node that was kept
at 168 but is dropped at 172 and that lies inside a bench crop (grown by one node) gets the per-node fail-closed
surface clearance (point grown by 13.2 vox, jsurf.JSurf). Reports the minimum."""
import json, sys
import numpy as np, tifffile
sys.path.insert(0, "/home/user/dominion/tools/sib/reg0841na"); sys.path.insert(0, "/home/user/dominion/tools/sib/reg0841")
from field import load_final
from jsurf import JSurf
from jexcl import JExcl
MAP, FD = load_final(); J = JSurf(); JE = JExcl()
from jexcl import SEGID
F9, F2 = "20250821151531-9.366um", "20260319124803-2.403um"


def load(seg, frame):  # same as map_meshes.py
    ts = seg.split("-")[0]; d = f"/work/reg/mesh/{seg}/mesh/{ts}-on-{frame}.tifxyz"
    P = np.stack([tifffile.imread(f"{d}/{a}.tif").astype(np.float64) for a in "xyz"], -1)
    return P, ~np.all(P == -1, -1) & (P[..., 2] > 0), None


def bil(P, V, r, c):  # same as map_meshes.py
    H, W = V.shape
    r0 = np.clip(np.floor(r).astype(int), 0, H - 2); c0 = np.clip(np.floor(c).astype(int), 0, W - 2)
    fr = (r - r0)[:, None]; fc = (c - c0)[:, None]
    ok = V[r0, c0] & V[r0 + 1, c0] & V[r0, c0 + 1] & V[r0 + 1, c0 + 1] & (r >= 0) & (c >= 0) & (r <= H - 1) & (c <= W - 1)
    return P[r0, c0] * (1 - fr) * (1 - fc) + P[r0 + 1, c0] * fr * (1 - fc) + P[r0, c0 + 1] * (1 - fr) * fc + P[r0 + 1, c0 + 1] * fr * fc, ok
seg = SEGID["214732"]
P9, V9, _ = load(seg, F9); P2, V2, _ = load(seg, F2)
N9 = np.array(V9.shape) * 20; N2 = np.array(V2.shape) * 20
out = {"crops": []}
for (cy, cx, n) in ((2560, 7552, 512), (3456, 7040, 2048)):
    r0, r1 = max((cy - 20) // 20, 0), (cy + n + 20) // 20 + 1; c0, c1 = max((cx - 20) // 20, 0), (cx + n + 20) // 20 + 1
    rr, cc = np.meshgrid(np.arange(r0, r1), np.arange(c0, c1), indexing="ij"); rr = rr.ravel(); cc = cc.ravel()
    cr9 = (20 * rr - 0.5 + 10) * N9[0] / N2[0] - 10; ccol9 = (20 * cc - 0.5 + 10) * N9[1] / N2[1] - 10
    p9, ok = bil(P9, V9, (cr9 + 0.5) / 20, (ccol9 + 0.5) / 20)
    dJ = np.full(len(p9), np.inf); dJ[ok] = JE.tree.query(p9[ok])[0]
    q = MAP.f(p9[ok]); inz = np.zeros(len(p9), bool); inz[ok] = (q[:, 2] >= 31) & (q[:, 2] <= 15120 - 31)
    k168 = ok & (dJ >= 168) & inz
    band = k168 & (dJ < 172)
    cl = [J.box_clearance(p - 13.2, p + 13.2, cap=400.0) for p in p9[band]]
    allk = [J.box_clearance(p - 13.2, p + 13.2, cap=400.0) for p in p9[k168][:: max(1, k168.sum() // 400)]]
    out["crops"].append(dict(crop=[cy, cx, n], n_nodes_kept168=int(k168.sum()), n_nodes_168_to_172=int(band.sum()),
                             min_clearance_168_to_172=float(min(cl)) if cl else None,
                             min_clearance_sampled_all=float(min(allk)) if allk else None))
    print(out["crops"][-1], flush=True)
json.dump(out, open("/home/user/dominion/logs/sib/reg0841/chainvalid/bench_render_clearance.json", "w"), indent=1)
