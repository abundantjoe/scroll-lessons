import sys, json, numpy as np
sys.path.insert(0, 'tools/sib/fl-pherc0306b/fl2'); import fl
Z = fl.Zarr('https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0306B/representations/predictions/surfaces/20250521133212-surface-20260413222639-surface-m7-L0-th0.2.zarr/0')
rng = np.random.default_rng(1)
for seg in sys.argv[1:]:
    P, V = fl.load_xyz(f'/work/fl2/seg/{seg}')
    # local surface normal from grid neighbours, to shift along the normal (off-sheet control)
    du = np.zeros_like(P); dv = np.zeros_like(P)
    du[:, 1:-1] = P[:, 2:] - P[:, :-2]; dv[1:-1] = P[2:] - P[:-2]
    N = np.cross(du, dv); nn = np.linalg.norm(N, axis=-1)
    ok = V & (nn > 0); ok[:, :1] = ok[:, -1:] = ok[:1] = ok[-1:] = False
    ii = np.argwhere(ok); pick = ii[rng.choice(len(ii), 60, replace=False)]
    res = {}
    for off in (0, 4, 8, 12, 16):
        on = 0
        for r, c in pick:
            p = P[r, c] + off * N[r, c] / nn[r, c]
            on += Z.at(p[2], p[1], p[0]) >= 128
        res[off] = round(on / len(pick), 3)
    print(json.dumps({'segment': seg, 'n': len(pick), 'frac_pred_ge128_vs_normal_offset_vox': res}))
