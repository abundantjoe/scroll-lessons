# Numbers only: median z and crude radius per w010-027 tile from mesh points (no pixels).
# Input: tile_points.npz from origin/claude/gifted-bell-gavnl5-sib-p4-tiles-a:logs/sib/p4-tiles-a/tile_points.npz
import sys, numpy as np
z = np.load(sys.argv[1]); v = 0.0024  # mm per voxel (20260411134726)
allp = np.concatenate([z[k] for k in z.files])
zb = np.floor(allp[:, 2] * v / 5).astype(int)
cen = {b: allp[zb == b, :2].mean(0) for b in np.unique(zb)}  # crude axis proxy per 5 mm z-bin
R, C = 8, 20
Z = np.full((R, C), np.nan); Rr = np.full((R, C), np.nan)
for k in z.files:
    r, c = [int(s[1:]) for s in k.split('_')]; p = z[k]
    b = np.floor(p[:, 2] * v / 5).astype(int)
    cc = np.array([cen[i] for i in b])
    Z[r, c] = np.median(p[:, 2]) * v; Rr[r, c] = np.median(np.hypot(*(p[:, :2] - cc).T)) * v
print('median z (mm)'); [print('r%d ' % r + ' '.join('%5.0f' % x for x in Z[r])) for r in range(R)]
print('median r (mm, crude axis)'); [print('r%d ' % r + ' '.join('%5.1f' % x for x in Rr[r])) for r in range(R)]
