"""Independent check of T_cert (geometry only): (1) random certified mask pixels -> bilinear 3-D strip point ->
exact distance to the X surface (all triangles incident to X vertices within 500 + Lc_X) must be >= 500 vox;
(2) the k-NN lower bound must not exceed the exact distance on random near-X points."""
import sys, os, json, time
import numpy as np, tifffile
sys.path.insert(0, os.path.dirname(__file__))
from surfdist import Surface
from process import VOX_MM, PROV
a_mesh, a_grid, b_mesh, b_grid, cdir, out = sys.argv[1:7]
t0 = time.time(); s = 20; LIM = 1.2 / VOX_MM
ld = lambda m: np.stack([tifffile.imread(f'{m}/{c}.tif') for c in 'xyz'], -1)
Ga = ld(a_mesh); Va = (Ga >= 0).all(-1); Ta = int(json.load(open(a_grid))['T_canvas_px'])
cert = json.load(open(f'{cdir}/T_cert.json')); xj0, xj1 = cert['X']['grid_quad_cols']; xj1 += 1
GX = np.where(Va[:, xj0:xj1, None], Ga[:, xj0:xj1], np.nan).astype(np.float32); SX = Surface(GX)
rng = np.random.default_rng(1)
res = {'provenance': PROV, 'what': 'independent check of T_cert.json', 'checks': {}}
for name, mesh, grid in (('w010-027', a_mesh, a_grid), ('w028-037', b_mesh, b_grid)):
    G = Ga if name == 'w010-027' else ld(mesh)
    g = json.load(open(grid)); T = int(g.get('T_px') or g['T_canvas_px'])
    M = np.load(f'{cdir}/T_mask_{name}.npz')
    ks = M.files; pts = []
    for _ in range(300):
        k = ks[rng.integers(len(ks))]; m = M[k]; yy, xx = np.nonzero(m); j = rng.integers(len(yy))
        r, c = (int(x[1:]) for x in k.split('_')[-2:])
        py = r * T + 4 * yy[j] + rng.uniform(0, 4); px = c * T + 4 * xx[j] + rng.uniform(0, 4)   # any point of the pixel
        gy, gx = py / s, px / s; i, jj = int(gy), int(gx); fy, fx = gy - i, gx - jj
        C = [G[i, jj], G[i, jj + 1], G[i + 1, jj], G[i + 1, jj + 1]]
        # the (a,b,e),(a,e,c) triangulation point at (fy, fx)
        a, b, cc, e = (np.asarray(x, np.float64) for x in C)
        p = a + (b - a) * (fx - fy) + (e - a) * fy if fx >= fy else a + (cc - a) * (fy - fx) + (e - a) * fx
        pts.append(p)
    pts = np.array(pts); dmin = []
    for q in pts:
        v = SX.tree.query_ball_point(q, LIM + SX.Lc)
        dmin.append(SX._tri_dist_for_vertices(q, np.asarray(v)) if v else np.inf)
    dmin = np.array(dmin)
    res['checks'][name + '_certified_pixels'] = {'n': len(dmin), 'min_exact_vox': float(dmin.min()),
                                                 'n_below_500': int((dmin < LIM).sum()), 'pass': bool((dmin >= LIM).all())}
    print(name, res['checks'][name + '_certified_pixels'], round(time.time() - t0), 's', flush=True)
# (2) lower bound soundness on near-X strip-b points (exact affordable at small distance)
lcv_src = cert
Gb = ld(b_mesh); Vb = (Gb >= 0).all(-1); vi, vj = np.nonzero(Vb)
sel = rng.choice(len(vi), 400000, replace=False); P = Gb[vi[sel], vj[sel]].astype(np.float64)
dv, _ = SX.tree.query(P, workers=-1); near = P[dv < 150][:400]
import importlib.util
ex = SX.point_dist(near)
# recompute lc_v and the bound exactly as t_cert.py
qx = SX.quad_valid; g = SX.grid.astype(np.float64); LQ = np.zeros(qx.shape)
for (a0, a1), (b0, b1) in (((0, 0), (0, 1)), ((0, 0), (1, 0)), ((0, 1), (1, 1)), ((1, 0), (1, 1)), ((0, 0), (1, 1))):
    d = np.linalg.norm(g[a0:a0 + qx.shape[0], a1:a1 + qx.shape[1]] - g[b0:b0 + qx.shape[0], b1:b1 + qx.shape[1]], axis=-1)
    LQ = np.maximum(LQ, np.where(qx, d, 0))
LV = np.zeros(SX.valid.shape)
for di in (0, 1):
    for dj in (0, 1):
        LV[di:di + qx.shape[0], dj:dj + qx.shape[1]] = np.maximum(LV[di:di + qx.shape[0], dj:dj + qx.shape[1]], LQ)
lcv = LV[SX.ij[:, 0], SX.ij[:, 1]] / np.sqrt(3)
d, v = SX.tree.query(near, k=16, workers=-1); lb = np.minimum((d - lcv[v]).min(1), d[:, -1] - SX.Lc)
res['checks']['lower_bound_soundness'] = {'n': int(len(near)), 'max(lb - exact)_vox': float((lb - ex).max()),
                                          'median(exact - lb)_vox': float(np.median(ex - lb)), 'pass': bool((lb <= ex + 1e-9).all())}
print(res['checks']['lower_bound_soundness'])
res['all_pass'] = all(c['pass'] for c in res['checks'].values()); res['seconds'] = round(time.time() - t0, 1)
json.dump(res, open(out, 'w'), indent=1); print('all_pass', res['all_pass'])
