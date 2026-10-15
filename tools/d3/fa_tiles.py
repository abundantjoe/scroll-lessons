# Provenance: Project HERCULES | owner the owner | [id removed]
"""D3 Stage 1a: fold-A tile list (numbers only). Reproduces the PRIMARY text tiles of D3-FEAS-RESULT with the
count-B exclusion (logs/d1/d3_feas_count_B.json method: pixel excluded iff inside its segment's J window or its mesh
point is < 128 vox (3-D) from any J mesh point; stride-4 subsample KD-tree upper bound, measured covering radius e
lower bound, exact full-res check where inconclusive). PRIMARY: 128 px tiles, origins stride 64, valid9 >= 90 %,
0 excluded px, (valid9 & ref9 >= 150) >= 2 % of valid. For every tile also the certified minimum 3-D distance to J
over its mesh-valid pixels (exact where < 144 + e + 2, else lower bound or 'beyond'), for the >= 144 vox crop rule
of DECL-D3-A1 item 2. Output: JSON tile list. No image or pixel array is displayed."""
import os, sys, json, time, hashlib
os.environ.setdefault("OMP_NUM_THREADS", "3")
import numpy as np, tifffile
from scipy.spatial import cKDTree

BANK = "/work/bank/0841"
T, MARGIN, W, TILE = 128.0, 144.0, 3, 128
OUT = sys.argv[1]
t0 = time.time()
bank = json.load(open(f"{BANK}/bank_0841.json"))
JW = bank["J_windows"]
SEGS = sorted(bank["segments"].keys())


def mesh(seg):
    ts = seg.split("-")[0]
    d = f"{BANK}/s3/PHerc0841/segments/{seg}/mesh/{ts}-on-20250821151531-9.366um.tifxyz"
    return np.stack([tifffile.imread(f"{d}/{c}.tif").astype(np.float64) for c in "xyz"], -1)


def canvas_points(xyz, rows, cols):
    G = xyz.shape[:2]
    gy = (rows + 0.5) / 20.0; i0 = np.floor(gy).astype(np.int64); fy = gy - i0
    gx = (cols + 0.5) / 20.0; j0 = np.floor(gx).astype(np.int64); fx = gx - j0
    okr = i0 + 1 < G[0]; okc = j0 + 1 < G[1]
    i0 = np.minimum(i0, G[0] - 2); j0 = np.minimum(j0, G[1] - 2)
    v = xyz[..., 0] != -1
    q = v[:-1, :-1] & v[1:, :-1] & v[:-1, 1:] & v[1:, 1:]
    valid = q[i0][:, j0] & okr[:, None] & okc[None, :]
    fy = fy[:, None, None]; fx = fx[None, :, None]
    A = xyz[i0][:, j0]; B = xyz[i0][:, j0 + 1]; C = xyz[i0 + 1][:, j0]; D = xyz[i0 + 1][:, j0 + 1]
    return (1 - fy) * ((1 - fx) * A + fx * B) + fy * ((1 - fx) * C + fx * D), valid


meshes = {s: mesh(s) for s in SEGS}
full_pts, sub_pts = [], []
for j in sorted(JW):
    w = JW[j]; s = w["segment"]; y0, x0, n = w["y0"], w["x0"], w["size"]
    P, V = canvas_points(meshes[s], np.arange(y0, y0 + n), np.arange(x0, x0 + n))
    full_pts.append(P[V]); sub_pts.append(P[1::4, 1::4][V[1::4, 1::4]])
    del P, V
full_pts = np.concatenate(full_pts); sub_pts = np.concatenate(sub_pts)
sub_tree = cKDTree(sub_pts)
e = 0.0
for k in range(0, len(full_pts), 2_000_000):
    d, _ = sub_tree.query(full_pts[k:k + 2_000_000], k=1, workers=W)
    e = max(e, float(d.max()))
e_used = e + 1e-6
full_tree = cKDTree(full_pts)
QB = MARGIN + e_used + 2.0


def sat(m):
    a = np.zeros((m.shape[0] + 1, m.shape[1] + 1), np.int64)
    a[1:, 1:] = m.astype(np.int64).cumsum(0).cumsum(1)
    return a


def boxsum(a, ys, xs):
    Y = ys[:, None]; X = xs[None, :]
    return a[Y + TILE, X + TILE] - a[Y, X + TILE] - a[Y + TILE, X] + a[Y, X]


tiles, per_seg = [], {}
for s in SEGS:
    H, Wd = meshes[s].shape[0] * 20, meshes[s].shape[1] * 20
    inJ = np.zeros((H, Wd), bool)
    for j, w in JW.items():
        if w["segment"] == s:
            inJ[w["y0"]:w["y0"] + w["size"], w["x0"]:w["x0"] + w["size"]] = True
    MV = np.zeros((H, Wd), bool)
    dist = np.full((H, Wd), np.inf)       # certified: exact if < QB, else a lower bound (inf if beyond query bound)
    for r0 in range(0, H, 512):
        rows = np.arange(r0, min(H, r0 + 512))
        P, V = canvas_points(meshes[s], rows, np.arange(Wd))
        MV[rows] = V
        q = (V & ~inJ[rows]).reshape(-1)
        idx = np.flatnonzero(q)
        Pf = P.reshape(-1, 3)
        dsub = np.full(q.size, np.inf)
        if len(idx):
            dd, _ = sub_tree.query(Pf[idx], k=1, workers=W, distance_upper_bound=QB + e_used)
            dsub[idx] = dd
        lb = dsub - e_used
        need = q & (dsub >= T) & (dsub - e_used < QB)    # dsub < T: surely excluded; else exact if could be < QB
        nidx = np.flatnonzero(need)
        if len(nidx):
            dx, _ = full_tree.query(Pf[nidx], k=1, workers=W, distance_upper_bound=QB)
            lb[nidx] = dx
        lb[~q] = -np.inf                                   # inside J window / no mesh point: flag
        dist[rows] = lb.reshape(len(rows), Wd)
        del P, V, Pf, dsub, lb
    excluded = inJ | (MV & (dist < T))
    valid = np.load(f"{BANK}/canvas9/{s}/valid9.npy").astype(bool)
    ref = np.load(f"{BANK}/canvas9/{s}/ref9.npy")
    txt = valid & (ref >= 150)
    del ref
    Sv, Sx, St = sat(valid), sat(excluded), sat(txt)
    ys = np.arange(0, H - TILE + 1, 64); xs = np.arange(0, Wd - TILE + 1, 64)
    nv, nx, nt = boxsum(Sv, ys, xs), boxsum(Sx, ys, xs), boxsum(St, ys, xs)
    elig = (10 * nv >= 9 * TILE * TILE) & (nx == 0)
    text = elig & (100 * nt >= 2 * nv)
    dm = np.where(MV, dist, np.inf)
    n144 = 0
    for a, b in zip(*np.nonzero(text)):
        y, x = int(ys[a]), int(xs[b])
        md = float(dm[y:y + TILE, x:x + TILE].min())
        ok144 = bool(md >= MARGIN)
        n144 += ok144
        tiles.append(dict(segment=s, y0=y, x0=x, valid_px=int(nv[a, b]), text_px=int(nt[a, b]),
                          meshvalid_px=int(MV[y:y + TILE, x:x + TILE].sum()),
                          min_3d_dist_vox=(md if np.isfinite(md) else None), ge144=ok144))
    per_seg[s] = dict(eligible=int(elig.sum()), text=int(text.sum()), text_ge144=int(n144),
                      excluded_px=int(excluded.sum()), nonexcluded_valid_px=int((valid & ~excluded).sum()))
    print(s[:14], per_seg[s], f"t={time.time()-t0:.0f}s", flush=True)
    del dist, MV, excluded, valid, txt, inJ, dm
res = dict(provenance="Provenance: Project HERCULES | owner the owner | [id removed]",
           rule="DECL-D3-A1 item 2 / D3-FEAS-RESULT PRIMARY", e_cover_radius_vox=e, n_J_full=int(len(full_pts)),
           exact_query_bound_vox=QB, per_segment=per_seg, n_text=len(tiles),
           n_text_ge144=int(sum(t["ge144"] for t in tiles)),
           min_dist_hist_vox={f"[{a},{b})": int(sum(1 for t in tiles if t["min_3d_dist_vox"] is not None
                                                       and a <= t["min_3d_dist_vox"] < b))
                              for a, b in ((128, 132), (132, 136), (136, 140), (140, 144), (144, 150))},
           tiles=tiles, seconds=round(time.time() - t0, 1),
           script_sha256=hashlib.sha256(open(__file__, "rb").read()).hexdigest())
json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "tiles"}, indent=1))
