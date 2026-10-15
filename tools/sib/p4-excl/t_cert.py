"""DECL-P4-23 item 1: certify the training zone T against the exclusion zone X (geometry only, no pixels).

X  = strip-a (20260701183124-w010-027) tiles c9-c19, all rows: every strip-a quad touching an X tile pixel,
     i.e. grid quad columns [floor(9T/20), ...) (widened by one quad column: conservative).
T  = strip-a tiles c0-c8 r0-r7 and strip-b (20260701183125-w028-037) all tiles.
A T cell (grid quad, 20 x 20 strip px) is certified when every point of it is >= 1.2 mm (500 vox) from the X
surface: min over its 4 corners of a certified lower bound on the corner's exact point-to-surface distance,
minus Lc_T (every cell point is within Lc_T = Lmax_T / sqrt(3) of a corner; distance is 1-Lipschitz), >= 500.
Corner lower bound (no exact search: X is multi-winding, so exact balls are huge): with lc_v = (max edge of the
triangles incident to X vertex v) / sqrt(3), every X surface point p lies in a triangle with a vertex v, |p - v| <= lc_v,
so d(q, X) >= min_v (|q - v| - lc_v) >= min( min over the k nearest v of (|q - v| - lc_v), d_k - Lc_X ).
Cells whose bound is below the limit are simply not certified (conservative).
Mask: per tile, x4 downsampled strip pixel grid; a mask pixel is true iff every strip px it covers lies in a
certified cell (conservative). Per tile: certified fraction of tile px and exact min vertex distance to X.
"""
import sys, os, json, time
import numpy as np, tifffile
sys.path.insert(0, os.path.dirname(__file__))
from surfdist import Surface
from process import VOX_MM, PROV, sha

LIM = 1.2 / VOX_MM          # 500 vox
DS = 4
a_mesh, a_grid, b_mesh, b_grid, outdir = sys.argv[1:6]
os.makedirs(outdir, exist_ok=True)
t0 = time.time()


def load(mdir):
    G = np.stack([tifffile.imread(f'{mdir}/{c}.tif') for c in 'xyz'], -1)
    V = (G >= 0).all(-1) & np.isfinite(G).all(-1)
    return G, V


def Tpx(gj):
    g = json.load(open(gj)); return int(g.get('T_px') or g['T_canvas_px'])


Ga, Va = load(a_mesh); Ta = Tpx(a_grid); s = 20
xj0 = (9 * Ta) // s                          # quad column holding strip px 9*Ta (conservative widening)
xj1 = min(-(-(20 * Ta) // s) + 1, Ga.shape[1])
GX = np.where(Va[:, xj0:xj1, None], Ga[:, xj0:xj1], np.nan).astype(np.float32)
SX = Surface(GX)
# per-vertex local covering radius lc_v
qx = SX.quad_valid; LQ = np.zeros(qx.shape, np.float32)
for (a0, a1), (b0, b1) in (((0, 0), (0, 1)), ((0, 0), (1, 0)), ((0, 1), (1, 1)), ((1, 0), (1, 1)), ((0, 0), (1, 1))):
    for r0 in range(0, qx.shape[0], 256):
        r1 = min(r0 + 256, qx.shape[0])
        d = np.linalg.norm(GX[r0 + a0:r1 + a0, a1:a1 + qx.shape[1]].astype(np.float64) - GX[r0 + b0:r1 + b0, b1:b1 + qx.shape[1]], axis=-1)
        LQ[r0:r1] = np.maximum(LQ[r0:r1], np.where(qx[r0:r1], d, 0))
LV = np.zeros(SX.valid.shape, np.float32)
for di in (0, 1):
    for dj in (0, 1):
        LV[di:di + qx.shape[0], dj:dj + qx.shape[1]] = np.maximum(LV[di:di + qx.shape[0], dj:dj + qx.shape[1]], LQ)
lcv = (LV[SX.ij[:, 0], SX.ij[:, 1]] / np.sqrt(3)).astype(np.float64)
del GX, LQ, LV
print('X surface', SX.grid.shape, 'Lc_X', round(SX.Lc, 3), 'lc_v median', round(float(np.median(lcv)), 3), round(time.time() - t0), 's', flush=True)
KNN = 16


def lower_bound(P):
    out = np.empty(len(P))
    for k in range(0, len(P), 500_000):
        d, v = SX.tree.query(P[k:k + 500_000], k=KNN, workers=-1)
        out[k:k + 500_000] = np.minimum((d - lcv[v]).min(1), d[:, -1] - SX.Lc)
    return out

strips = {'w010-027': dict(T=Ta, rows=range(0, 8), cols=range(0, 9), mesh=a_mesh, grid=a_grid),
          'w028-037': dict(T=Tpx(b_grid), mesh=b_mesh, grid=b_grid)}

out = {'provenance': PROV, 'what': 'DECL-P4-23 item 1: certification of the training zone T against X (3-D point-to-surface, '
       'the labelled-adjacency form applied in reverse), geometry only', 'limit_mm': 1.2, 'limit_vox': LIM, 'voxel_mm': VOX_MM,
       'X': {'strip': '20260701183124-w010-027', 'tiles': 'c9-c19, all rows', 'grid_quad_cols': [int(xj0), int(xj1) - 1],
             'n_vertices': int(len(SX.V)), 'Lc_vox': round(SX.Lc, 4)},
       'rule': 'cell certified iff min over its 4 corners of (certified lower bound of the distance to X: min over the 16 nearest '
               'X vertices of |q-v| - lc_v, capped by d_16 - Lc_X) - Lc_T >= 500 vox; '
               f'mask pixel (x{DS} downsample) true iff every strip px it covers is in a certified cell',
       'mask_format': f'bool, shape ceil(T/{DS}) x ceil(T/{DS}) per tile, pixel (y, x) covers strip px [{DS}y, {DS}y+{DS}) x [{DS}x, {DS}x+{DS}) of the tile',
       'strips': {}, 'tiles': {}}
for name, st in strips.items():
    if name == 'w010-027':
        G, V = Ga, Va
    else:
        del Ga, Va, G, V
        G, V = load(b_mesh)
        st['rows'] = range(0, -(-G.shape[0] * s // st['T'])); st['cols'] = range(0, -(-G.shape[1] * s // st['T']))
    T = st['T']
    H, W = V.shape
    q = V[:-1, :-1] & V[:-1, 1:] & V[1:, :-1] & V[1:, 1:]
    L = 0.0
    for (a0, a1), (b0, b1) in (((0, 0), (0, 1)), ((0, 0), (1, 0)), ((0, 1), (1, 1)), ((1, 0), (1, 1)), ((0, 0), (1, 1))):
        for r0 in range(0, q.shape[0], 256):
            r1 = min(r0 + 256, q.shape[0])
            d = np.linalg.norm(G[r0 + a0:r1 + a0, a1:a1 + q.shape[1]].astype(np.float64) - G[r0 + b0:r1 + b0, b1:b1 + q.shape[1]], axis=-1)
            if q[r0:r1].any():
                L = max(L, float(d[q[r0:r1]].max()))
    LcT = L / np.sqrt(3)
    # rows/cols of the T part of this strip (grid vertices) incl. one extra for cell corners
    i1 = min(-(-(st['rows'][-1] + 1) * T // s) + 1, H); j1 = min(-(-(st['cols'][-1] + 1) * T // s) + 1, W)
    vi, vj = np.nonzero(V[:i1, :j1]); P = G[vi, vj].astype(np.float64)
    lb = lower_bound(P)                                     # certified lower bound
    dv1 = np.empty(len(P))
    for k in range(0, len(P), 2_000_000):
        dv1[k:k + 2_000_000] = SX.tree.query(P[k:k + 2_000_000], workers=-1)[0]   # >= exact distance (upper bound)
    band = np.zeros(0)
    LB = np.full((i1, j1), -np.inf); LB[vi, vj] = lb; UBg = np.full((i1, j1), np.inf); UBg[vi, vj] = dv1
    LBg = LB
    cell_ok = q[:i1 - 1, :j1 - 1] & (np.minimum(np.minimum(LB[:-1, :-1], LB[:-1, 1:]), np.minimum(LB[1:, :-1], LB[1:, 1:])) - LcT >= LIM)
    shards = {}
    for r in st['rows']:
        for c in st['cols']:
            k = f'{name}_r{r}_c{c}'
            ny = nx = -(-T // DS)
            py0 = r * T + DS * np.arange(ny); px0 = c * T + DS * np.arange(nx)
            py1 = np.minimum(py0 + DS - 1, (r + 1) * T - 1); px1 = np.minimum(px0 + DS - 1, (c + 1) * T - 1)
            ci0, ci1 = py0 // s, py1 // s; cj0, cj1 = px0 // s, px1 // s
            inb_i = ci1 < cell_ok.shape[0]; inb_j = cj1 < cell_ok.shape[1]
            m = np.zeros((ny, nx), bool)
            ii0 = np.where(inb_i, ci0, 0); ii1 = np.where(inb_i, ci1, 0); jj0 = np.where(inb_j, cj0, 0); jj1 = np.where(inb_j, cj1, 0)
            m = (cell_ok[ii0][:, jj0] & cell_ok[ii0][:, jj1] & cell_ok[ii1][:, jj0] & cell_ok[ii1][:, jj1])
            m &= inb_i[:, None] & inb_j[None, :]
            # tile vertices (tiler rule) for the exact min distance to X
            ti0, ti1 = -(-r * T // s), min(-(-(r + 1) * T // s), H); tj0, tj1 = -(-c * T // s), min(-(-(c + 1) * T // s), W)
            sel = V[ti0:ti1, tj0:tj1]
            ent = {'strip': name, 'r': r, 'c': c, 'certified_fraction': round(float(m.mean()), 6),
                   'n_tile_vertices': int(sel.sum())}
            if sel.any():
                lbt = LBg[ti0:min(ti1, i1), tj0:min(tj1, j1)][sel[:min(ti1, i1) - ti0, :min(tj1, j1) - tj0]]
                ubt = UBg[ti0:min(ti1, i1), tj0:min(tj1, j1)][sel[:min(ti1, i1) - ti0, :min(tj1, j1) - tj0]]
                # tile surface min distance to X lies in [min vertex lower bound - Lc_T, min vertex distance to X vertices]
                ent['min_dist_to_X_mm'] = {'lower': round(max(0.0, float(lbt.min()) - LcT) * VOX_MM, 6),
                                           'upper': round(float(ubt.min()) * VOX_MM, 6)}
            out['tiles'][k] = ent
            if m.any():
                shards[k] = m
    fn = f'T_mask_{name}.npz'
    np.savez_compressed(os.path.join(outdir, fn), **shards)
    out['strips'][name] = {'T_px': T, 'canvas_per_grid': s, 'Lmax_T_vox': round(L, 4), 'Lc_T_vox': round(LcT, 4),
                           'rows': [st['rows'][0], st['rows'][-1]], 'cols': [st['cols'][0], st['cols'][-1]],
                           'n_T_vertices': int(len(P)),
                           'mesh_sha256': {f: sha(f"{st['mesh']}/{f}") for f in ('x.tif', 'y.tif', 'z.tif')},
                           'grid_json_sha256': sha(st['grid']), 'mask_file': fn,
                           'mask_file_sha256': sha(os.path.join(outdir, fn)), 'n_tiles_with_certified_px': len(shards)}
    print(name, 'done', round(time.time() - t0), 's', flush=True)
out['seconds'] = round(time.time() - t0, 1)
json.dump(out, open(os.path.join(outdir, 'T_cert.json'), 'w'), indent=1)
print('done', out['seconds'])
