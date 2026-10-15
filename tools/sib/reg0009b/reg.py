# Provenance: Project HERCULES | owner the owner | [id removed]
"""Per-segment registration of the PHerc0009B 2.401 um canvas to the 8.640 um canvas by CT NCC.

CT only (no ink map is read or written here). For each segment:
  I9 = mean of 8.64 um surface-volume slices [15-1, 15+2) at level 0 (canvas px = 8.64 um)
  J2 = mean of 2.401 um surface-volume slices [54-2, 54+3) at level 2 (9.604 um px)
  Starting map (label mapper, per axis): c2 = (c9 + 10) * N2 / N9 - 10, N = canvas extents
  (= 20 x mesh grid extents; checked against the zarr canvas_size).
  B9 = J2 resampled onto the 9 um canvas through the starting map (bilinear, L2 centre = 4i + 1.5).
  Band-pass both (Gaussian sigma 1 minus sigma 10 px), tiles 256 x 256 px, stride 256,
  tile kept if >= 98 % of pixels are non-zero CT in both. Per tile: NCC over integer shifts
  within +-R px (cv2 TM_CCOEFF_NORMED), parabolic sub-pixel peak.
Shift convention: d = (dx, dy) in 9 um canvas px such that the corrected map is
  c9 = (c2 + 10) * N9 / N2 - 10 + d     (content of the 2.4 um map moves by +d).
Outputs logs/sib/reg0009b/reg/<seg>.json (tile table, global shift, affine fit, gate numbers).
"""
import json, os, sys, time
import numpy as np, cv2, tifffile
sys.path.insert(0, os.path.dirname(__file__))
from svband import band

ROOT = 'PHerc0009B/segments/'
SV9 = 'surface-volumes/8.64um-1.2m-116keV-volume-20250521125136.zarr'
SV2 = 'surface-volumes/2.401um-0.35m-77keV-volume-20250820154339.zarr'
DATA = '/work/reg0009b/data'
OUT = '/home/user/dominion/logs/sib/reg0009b/reg'
TILE, R = 256, 12
Z9, Z2 = (14, 17), (52, 57)


def bandpass(a, valid):
    a = a.astype(np.float32)
    m = valid.astype(np.float32)
    def blur(x, s):
        num = cv2.GaussianBlur(x * m, (0, 0), s); den = cv2.GaussianBlur(m, (0, 0), s)
        return num / np.maximum(den, 1e-3)
    return (blur(a, 1.0) - blur(a, 10.0)) * m


def tile_ncc(A, B, x0, y0, r=R, t=TILE):
    """Best shift d s.t. A(x) ~ B(x - d) for A tile at (x0, y0). Returns (dx, dy, peak, ncc0)."""
    a = A[y0:y0 + t, x0:x0 + t]
    w = B[y0 - r:y0 + t + r, x0 - r:x0 + t + r]
    res = cv2.matchTemplate(w, a, cv2.TM_CCOEFF_NORMED)  # res[v, u]: a ~ w[v:v+t, u:u+t]
    v, u = np.unravel_index(np.argmax(res), res.shape)
    pk = float(res[v, u]); n0 = float(res[r, r])
    def sub(c, lo, hi):
        if 0 < c < len(lo) - 1:
            den = lo[c - 1] - 2 * lo[c] + lo[c + 1]
            return c + (0.5 * (lo[c - 1] - lo[c + 1]) / den if den < 0 else 0.0)
        return float(c)
    uu = sub(u, res[v, :], None); vv = sub(v, res[:, u], None)
    # a(x) = w(x + off) with off = (uu - r, vv - r); B(x + off) = A(x)  =>  A(x) = B(x - d), d = -off
    return -(uu - r), -(vv - r), pk, n0, bool(0 < u < 2 * r and 0 < v < 2 * r)


def mapped(J2, N2, N9, shape9, d=(0.0, 0.0)):
    H9, W9 = shape9
    x9 = np.arange(W9, dtype=np.float64) - d[0]; y9 = np.arange(H9, dtype=np.float64) - d[1]
    x2 = (x9 + 10) * N2[0] / N9[0] - 10; y2 = (y9 + 10) * N2[1] / N9[1] - 10
    mx = ((x2 - 1.5) / 4).astype(np.float32); my = ((y2 - 1.5) / 4).astype(np.float32)
    MX, MY = np.meshgrid(mx, my)
    return cv2.remap(J2, MX, MY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def depth_plane(seg):
    """Robust plane k(x9, y9) (2.4 um slice index best matching 9 um slice 15), fitted to the
    depthcheck.py tiles (L1 tile centres -> L0 canvas px), 3 trimming rounds at 3 slices."""
    o = json.load(open(f'{OUT}/{seg}.depth.json'))
    T = np.array([t for t in o['per_s9']['15']['tiles'] if t[3] >= 0.3], float)
    X = np.c_[np.ones(len(T)), 2 * (T[:, 0] + 64) + 0.5, 2 * (T[:, 1] + 64) + 0.5]
    keep = np.ones(len(T), bool)
    for _ in range(3):
        c, *_ = np.linalg.lstsq(X[keep], T[keep, 2], rcond=None)
        keep = np.abs(T[:, 2] - X @ c) <= 3.0
    return c, float(np.std(T[keep, 2] - X[keep] @ c)), int(keep.sum()), len(T)


def depth_field(seg, shape9):
    """Smooth depth field k(x9, y9): per-tile best slices (ncc >= 0.3, within 6 slices of the robust
    plane) linearly interpolated between tile centres (plane outside their hull), then Gaussian-smoothed
    (sigma = 1 tile = 256 L0 px). Returns (kfield float, plane coef, plane resid std, n_used, n_tiles)."""
    from scipy.interpolate import griddata
    c, pstd, pn, pT = depth_plane(seg)
    o = json.load(open(f'{OUT}/{seg}.depth.json'))
    T = np.array([t for t in o['per_s9']['15']['tiles'] if t[3] >= 0.3], float)
    X = np.c_[2 * (T[:, 0] + 64) + 0.5, 2 * (T[:, 1] + 64) + 0.5]
    pl = c[0] + c[1] * X[:, 0] + c[2] * X[:, 1]
    ok = np.abs(T[:, 2] - pl) <= 6.0
    H, W = shape9; s = 16
    gy, gx = np.mgrid[0:H:s, 0:W:s].astype(float)
    kp = c[0] + c[1] * gx + c[2] * gy
    ki = griddata(X[ok], T[ok, 2] - pl[ok], (gx, gy), method='linear')
    kf = kp + np.nan_to_num(ki, nan=0.0)
    kf = cv2.GaussianBlur(kf.astype(np.float32), (0, 0), 256 / s)
    kf = cv2.resize(kf, (W, H), interpolation=cv2.INTER_LINEAR)
    return kf, c, pstd, int(ok.sum()), len(T)


def run(seg, dc=False):
    """dc=True: depth-corrected pass. The 2.4 um slab (5 slices) is centred per 9 um pixel on the
    smooth depth field of depth_field() instead of the nominal slice 54; output <seg>.dc.json."""
    os.makedirs(OUT, exist_ok=True)
    of = f'{OUT}/{seg}.dc.json' if dc else f'{OUT}/{seg}.json'
    if os.path.exists(of): return json.load(open(of))
    t0 = time.time(); sid = seg.split('-')[0]
    g9 = tifffile.imread(f'{DATA}/{seg}/mesh/{sid}-on-20250521125136-8.64um.tifxyz/x.tif')
    g2 = tifffile.imread(f'{DATA}/{seg}/mesh/{sid}-on-20250820154339-2.401um.tifxyz/x.tif')
    N9 = (g9.shape[1] * 20.0, g9.shape[0] * 20.0); N2 = (g2.shape[1] * 20.0, g2.shape[0] * 20.0)
    s9, za9, st9 = band(f'{ROOT}{seg}/{SV9}', 0, *Z9)
    H9, W9 = s9.shape[1:]
    if dc:
        kf, dcoef, pstd, pn, pT = depth_field(seg, (H9, W9))
        kmap = np.rint(kf).astype(int)
        kmap = np.clip(kmap, 2, 106)
        Z2 = (int(kmap.min()) - 2, int(kmap.max()) + 3)
        s2, za2, st2 = band(f'{ROOT}{seg}/{SV2}', 2, *Z2)
    else:
        Z2 = (52, 57)
        s2, za2, st2 = band(f'{ROOT}{seg}/{SV2}', 2, *Z2)
    I9 = s9.mean(0).astype(np.float32); v9 = (s9 > 0).all(0)
    v2 = (s2 > 0).all(0).astype(np.float32)
    vB = mapped(v2, N2, N9, I9.shape) > 0.999
    if dc:
        # per-pixel slab: mean of the 5 slices centred on kmap, resampled onto the 9 um canvas
        B9 = np.zeros(I9.shape, np.float32)
        for k in range(int(kmap.min()), int(kmap.max()) + 1):
            sel = kmap == k
            if not sel.any(): continue
            Jk = s2[k - 2 - Z2[0]:k + 3 - Z2[0]].mean(0).astype(np.float32)
            B9[sel] = mapped(Jk, N2, N9, I9.shape)[sel]
        J2 = None
    else:
        J2 = s2.mean(0).astype(np.float32)
        B9 = mapped(J2, N2, N9, I9.shape)
    A = bandpass(I9, v9); Bb = bandpass(B9, vB)
    H, W = I9.shape
    tiles = []
    for y0 in range(R, H - TILE - R, TILE):
        for x0 in range(R, W - TILE - R, TILE):
            fa = v9[y0:y0 + TILE, x0:x0 + TILE].mean(); fb = vB[y0 - R:y0 + TILE + R, x0 - R:x0 + TILE + R].mean()
            if fa < 0.98 or fb < 0.98: continue
            dx, dy, pk, n0, interior = tile_ncc(A, Bb, x0, y0)
            tiles.append(dict(x0=x0, y0=y0, dx=round(dx, 3), dy=round(dy, 3), ncc_peak=round(pk, 4), ncc_at0=round(n0, 4), interior=interior))
    res = dict(depth_plane=dict(coef=[float(x) for x in dcoef], resid_std_slices=pstd, n_tiles_field=pn, n_tiles=pT,
                                kmap_p1_p50_p99=np.percentile(kmap[v9], [1, 50, 99]).tolist() if v9.any() else None) if dc else None,
               segment=seg, N9=N9, N2=N2, ratio=(N2[0] / N9[0], N2[1] / N9[1]), n_tiles=len(tiles), tiles=tiles,
               z9=Z9, z2=Z2, stream=dict(sv9=st9, sv2=st2), valid9_px=int(v9.sum()), validB_px=int(vB.sum()))
    good = [t for t in tiles if t['interior'] and t['ncc_peak'] >= 0.3]
    res['n_good'] = len(good)
    if len(good) >= 3:
        D = np.array([[t['dx'], t['dy']] for t in good]); X = np.array([[t['x0'] + TILE / 2, t['y0'] + TILE / 2] for t in good])
        dg = np.median(D, 0)
        # affine fit d = d0 + M (x - xc), iteratively trimmed at 3 px
        xc = X.mean(0); keep = np.ones(len(D), bool)
        for _ in range(3):
            G = np.c_[np.ones(keep.sum()), X[keep] - xc]
            coef, *_ = np.linalg.lstsq(G, D[keep], rcond=None)
            pred = np.c_[np.ones(len(D)), X - xc] @ coef
            keep = np.linalg.norm(D - pred, axis=1) <= 3.0
        pred = np.c_[np.ones(len(D)), X - xc] @ coef
        res['global_shift_median'] = dg.round(3).tolist()
        res['affine'] = dict(xc=xc.round(1).tolist(), d0=coef[0].round(3).tolist(), M=coef[1:].round(7).tolist(),
                             n_inliers=int(keep.sum()), resid_rms_px=float(np.sqrt((np.linalg.norm(D[keep] - pred[keep], axis=1) ** 2).mean())))
        r_glob = np.linalg.norm(D - dg, axis=1)
        res['resid_after_global'] = dict(median=float(np.median(r_glob)), p90=float(np.percentile(r_glob, 90)),
                                         frac_le2=float((r_glob <= 2).mean()))
        # gate: whole-segment NCC after global correction (sub-pixel remap), and at best residual shift
        Msh = np.float32([[1, 0, dg[0]], [0, 1, dg[1]]])  # B(x) -> B(x - d)
        vc = cv2.warpAffine(vB.astype(np.float32), Msh, (W, H), flags=cv2.INTER_LINEAR) > 0.999
        Bc = bandpass(cv2.warpAffine(B9, Msh, (W, H), flags=cv2.INTER_LINEAR), vc)
        m = v9 & vc
        er = cv2.erode(m.astype(np.uint8), np.ones((21, 21), np.uint8)).astype(bool)  # drop band-pass edge effects
        def ncc(a, b):
            a = a - a.mean(); b = b - b.mean(); return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum()))
        res['gate'] = dict(ncc_global_after=ncc(A[er], Bc[er]), n_px=int(er.sum()))
        # null: the same images offset by a further (40, 40) px (outside every search range)
        Bn = np.roll(Bc, (40, 40), axis=(0, 1)); vn = np.roll(er, (40, 40), axis=(0, 1)) & er
        res['gate']['ncc_null_offset40'] = ncc(A[vn], Bn[vn])
        B0 = bandpass(B9, vB); m0 = cv2.erode((v9 & vB).astype(np.uint8), np.ones((21, 21), np.uint8)).astype(bool)
        res['gate']['ncc_global_mapper_only'] = ncc(A[m0], B0[m0])
        # per-tile NCC at the corrected alignment and residual shift
        tt = []
        for t in good:
            dx, dy, pk, n0, interior = tile_ncc(A, Bc, t['x0'], t['y0'], r=4)
            tt.append((dx, dy, pk, n0))
        tt = np.array(tt)
        res['gate']['tile_resid_shift_median'] = float(np.median(np.hypot(tt[:, 0], tt[:, 1])))
        res['gate']['tile_ncc_at_corrected_median'] = float(np.median(tt[:, 3]))
        res['gate']['tile_ncc_peak_median'] = float(np.median(tt[:, 2]))
        res['gate']['frac_tiles_ncc080_shift_le2'] = float(((tt[:, 2] >= 0.8) & (np.hypot(tt[:, 0], tt[:, 1]) <= 2)).mean())
        res['gate']['pass'] = bool(res['gate']['ncc_global_after'] >= 0.80 and res['gate']['tile_resid_shift_median'] <= 2.0)
    res['seconds'] = round(time.time() - t0, 1)
    json.dump(res, open(of, 'w'), indent=1)
    return res


if __name__ == '__main__':
    dc = '--dc' in sys.argv
    segs = [a for a in sys.argv[1:] if a != '--dc'] or sorted(d for d in os.listdir(DATA) if os.path.isdir(f'{DATA}/{d}/mesh'))
    for s in segs:
        r = run(s, dc)
        print(s[:14], r['n_tiles'], r.get('n_good'), r.get('global_shift_median'), r.get('gate'), r['seconds'], flush=True)
