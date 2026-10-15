# Provenance: Project HERCULES | owner the owner | [id removed]
"""Independent fail-closed check (CORR-RETRACE-RULE) of the renderable area: kept nodes of each mapped mesh are
mapped back to 9 um (exact inverse of the frozen field), grouped in 10 x 10 node blocks (a block whose box fails is re-checked node by node), and the axis-aligned
box of each block's points, grown by 8 vox (the -n 63 slab half-depth, 31 rescan vox) and by 5.2 vox (pixel
interpolation), must have point-to-triangulated-surface clearance >= 144 vox from J (jsurf.JSurf)."""
import json, sys
import numpy as np, tifffile
MESH = sys.argv[1] if len(sys.argv) > 1 else "/work/cv/mesh"
OUTF = sys.argv[2] if len(sys.argv) > 2 else "/home/user/dominion/logs/sib/reg0841/chainvalid/clearance_check.json"
sys.path.insert(0, "/home/user/dominion/tools/sib/reg0841na")
from field import load_final
from jsurf import JSurf
MAP, FD = load_final(); J = JSurf()
G = 8.0 + 5.2
out = {"grow_vox": G, "segments": {}}
for key in ("w00", "214732", "022814"):
    Q = np.stack([tifffile.imread(f"{MESH}/{key}/{a}.tif") for a in "xyz"], -1).astype(np.float64)
    V = Q[..., 0] != -1
    mins = []; pernode = []
    for r in range(0, V.shape[0], 10):
        for c in range(0, V.shape[1], 10):
            m = V[r:r + 10, c:c + 10]
            if not m.any():
                continue
            p9 = MAP.finv(Q[r:r + 10, c:c + 10][m])[0]
            b = J.box_clearance(p9.min(0) - G, p9.max(0) + G, cap=400.0)
            if b < 144:  # loose block box: re-check every node of the block on its own (box = point grown by G)
                b = min(J.box_clearance(p - G, p + G, cap=400.0) for p in p9)
                pernode.append(b)
            mins.append(b)
    mins = np.array(mins)
    out["segments"][key] = dict(n_blocks=int(len(mins)), min_clearance=float(mins.min()), n_below_144=int((mins < 144).sum()), n_blocks_rechecked_per_node=len(pernode))
    print(key, out["segments"][key], flush=True)
out["all_ge_144"] = all(v["n_below_144"] == 0 for v in out["segments"].values())
json.dump(out, open(OUTF, "w"), indent=1)
print(out["all_ge_144"])
