"""Synthetic tests for uvmap.nearest_uv. Run: python3 test_uvmap.py [out.json]"""
import sys, json, numpy as np
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from surfdist import Surface
from uvmap import nearest_uv


def surf_point(g, uv):
    """piecewise-linear point at uv on the (a,b,e),(a,e,c) triangulation."""
    i = np.floor(uv[:, 0]).astype(int); j = np.floor(uv[:, 1]).astype(int)
    i = np.minimum(i, g.shape[0] - 2); j = np.minimum(j, g.shape[1] - 2)
    s = uv[:, 0] - i; t = uv[:, 1] - j
    a, b, c, e = g[i, j], g[i, j + 1], g[i + 1, j], g[i + 1, j + 1]
    up = (t >= s)[:, None]   # (a,b,e): t >= s ; (a,e,c): s > t
    p1 = a + (b - a) * (t - s)[:, None] + (e - a) * s[:, None]
    p2 = a + (c - a) * (s - t)[:, None] + (e - a) * t[:, None]
    return np.where(up, p1, p2)


R = []
def check(name, ok, info):
    R.append({'test': name, 'pass': bool(ok), 'info': info}); print('PASS' if ok else 'FAIL', name, info)


rng = np.random.default_rng(5)
# 1 plane: uv exactly known
n = 40; j, i = np.meshgrid(np.arange(n), np.arange(n))
g = np.stack([500 + 20.0 * j, 700 + 20.0 * i, np.full(i.shape, 1000.0)], -1)
S = Surface(g.astype(np.float32))
uvt = rng.uniform(1, 37, (500, 2)); h = rng.uniform(-15, 15, 500)
Q = np.column_stack([500 + 20 * uvt[:, 1], 700 + 20 * uvt[:, 0], 1000 + h])
D, UV, nu = nearest_uv(S, Q, 20.0)
check('plane distance', np.abs(D - np.abs(h)).max() < 1e-9, float(np.abs(D - np.abs(h)).max()))
check('plane uv', np.abs(UV - uvt).max() < 1e-9, float(np.abs(UV - uvt).max()))
# 2 random curved sheets with holes: D == verified library distance; surf_point(UV) at distance D from q
worst_d = worst_p = 0.0; nunc = 0
for t in range(5):
    n = 30; j, i = np.meshgrid(np.arange(n), np.arange(n))
    x = 1000 + j * 20.0 + rng.normal(0, 3, (n, n)); y = 1000 + i * 20.0 + rng.normal(0, 3, (n, n))
    z = 2000 + 60 * np.sin(j / 4.0 + t) + 50 * np.cos(i / 5.0) + rng.normal(0, 2, (n, n))
    g = np.stack([x, y, z], -1); g[rng.random((n, n)) < 0.04] = -1
    S = Surface(g.astype(np.float32))
    Q = np.column_stack([rng.uniform(1050, 1550, 400), rng.uniform(1050, 1550, 400), rng.uniform(1850, 2150, 400)])
    D, UV, u = nearest_uv(S, Q, 1e9); nunc += u
    ref = S.point_dist(Q)
    worst_d = max(worst_d, float(np.abs(D - ref).max()))
    P = surf_point(S.grid.astype(np.float64), UV)
    isov = np.isclose(UV, np.round(UV)).all(1)  # vertex hits: surface(uv) is the vertex itself; still exact
    worst_p = max(worst_p, float(np.abs(np.linalg.norm(P - Q, axis=1) - D).max()))
check('random sheets: distance == library exact distance', worst_d < 1e-6, worst_d)
check('random sheets: |q - surface(uv)| == distance', worst_p < 1e-6, worst_p)
check('random sheets: ball fallback exercised', nunc > 0, nunc)
# 3 tolerance: points beyond tol get inf / nan
D, UV, _ = nearest_uv(S, Q, 5.0)
check('tolerance masking', bool(np.all(np.isinf(D[np.isnan(UV[:, 0])])) and np.all(D[np.isfinite(D)] <= 5.0)), int(np.isfinite(D).sum()))
npass = sum(r['pass'] for r in R); print(f'{npass}/{len(R)} pass')
if len(sys.argv) > 1:
    json.dump({'tests': R, 'pass': npass, 'total': len(R)}, open(sys.argv[1], 'w'), indent=1)
sys.exit(0 if npass == len(R) else 1)
