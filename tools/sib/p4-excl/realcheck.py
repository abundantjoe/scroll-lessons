"""Sanity on a real mesh (coords only): cell-interior points -> 0; normal offsets h -> <= h, == h when no other layer nearer."""
import sys, os, json, time, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from surfdist import Surface
S = Surface(np.load(sys.argv[1])['grid']); rng = np.random.default_rng(7); t = time.time()
i, j = np.nonzero(S.quad_valid); k = rng.choice(len(i), 200, replace=False); i, j = i[k], j[k]
g = S.grid.astype(np.float64); A, B, C, E = g[i, j], g[i, j+1], g[i+1, j], g[i+1, j+1]
u = rng.random((200, 1)); w = rng.random((200, 1)) * u   # barycentric: stays inside (a,b,e)
P = A + u*(B-A) + w*(E-B)                      # inside triangle (a,b,e)
n = np.cross(B-A, E-A); n /= np.linalg.norm(n, axis=1, keepdims=True)
res = {'on_surface_max': float(S.point_dist(P).max())}
for h in (0.5, 3.0, 50.0, 400.0):
    d = S.point_dist(P + h*n)
    res[f'offset_{h}'] = {'max': float(d.max()), 'n_equal_1e-3': int((np.abs(d-h) < 1e-3).sum()), 'n_less': int((d < h-1e-3).sum()), 'n_greater': int((d > h+1e-3).sum())}
res['set_min_offset3'] = S.min_dist(P + 3*n)[0]; res['s'] = round(time.time()-t, 1)
print(json.dumps(res))
