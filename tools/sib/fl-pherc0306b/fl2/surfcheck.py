import sys, json, numpy as np, tifffile
sys.path.insert(0, 'tools/sib/fl-pherc0306b/fl2'); import fl
Z = fl.Zarr('https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0306B/representations/predictions/surfaces/20250521133212-surface-20260413222639-surface-m7-L0-th0.2.zarr/0')
rng = np.random.default_rng(0)
for seg in sys.argv[1:]:
    d = f'/work/fl2/seg/{seg}'
    P, V = fl.load_xyz(d)
    pts = P[V]
    c = pts - pts.mean(0); s = np.linalg.svd(c[::7], compute_uv=False)
    plane_rms = float(s[2] / np.sqrt(len(c[::7])))
    # sample 150 vertices clustered by chunk to limit fetches: pick 15 anchor vertices, 10 neighbours each
    idx = rng.choice(len(pts), 15, replace=False); on = 0; near = 0; n = 0
    for i in idx:
        x, y, z = pts[i]
        for dx in range(-2, 3):
            for dy in range(-1, 1):
                v0 = Z.at(z, y + dy * 3, x + dx * 3); n += 1; on += v0 >= 128
                nb = max(Z.at(z + a, y + dy * 3 + b, x + dx * 3 + e) for a in (-3, 0, 3) for b in (-3, 0, 3) for e in (-3, 0, 3))
                near += nb >= 128
    print(json.dumps({'segment': seg, 'n_vertices': int(len(pts)), 'bbox_extent_vox': np.ptp(pts, 0).round(0).tolist(),
                      'plane_fit_rms_vox': round(plane_rms, 2), 'n_samples': n,
                      'frac_on_pred_ge128': round(on / n, 3), 'frac_within_3vox_pred_ge128': round(near / n, 3)}))
