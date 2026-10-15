"""DECL-P4-23 item 2 (DECL-P4-21-A1): organizer ink labels on certified T pixels, as npz shards (code only; never
displayed, rendered or described). Interface: own-lead LABEL_INTERFACE.md (x4 per-tile grid, same as the T mask).

Per T tile with certified px:
  vertices of the tile (+1 border) -> exact closest point on each labelled segment within 20 vox (uvmap.nearest_uv)
  -> segment UV at the vertices; each x4 pixel centre (tile px 4y+1.5, 4x+1.5) -> strip grid coordinate (px / 20)
  -> segment UV and distance bilinearly interpolated from the quad's 4 corners (all 4 mapped to that segment)
  -> label px round(uv * 20). Nearest covering (supervision = 255) segment decides. n_sub = 1.
Only pixels with T mask = true are written; every other pixel is 0 in both arrays (sup = 0 means no label coverage).
Validation: a random sample of x4 pixels is also mapped exactly (bilinear 3-D strip point -> nearest_uv) and the label-px
deviation of the interpolated UV is reported (numbers only).
"""
import sys, os, json, time, hashlib
import numpy as np, tifffile, zarr
sys.path.insert(0, os.path.dirname(__file__))
from surfdist import Surface
from uvmap import nearest_uv
from process import SEGS, VOX_MM, PROV, sha

TOL = 20.0; DS = 4; s = 20
strip, mdir, gjson, maskf, sdir, ldir, outdir = sys.argv[1:8]
only = sys.argv[8].split(',') if len(sys.argv) > 8 else None
os.makedirs(os.path.join(outdir, 'labels'), exist_ok=True)
t0 = time.time()
g = json.load(open(gjson)); T = int(g.get('T_px') or g['T_canvas_px'])
G = np.stack([tifffile.imread(f'{mdir}/{a}.tif') for a in 'xyz'], -1)
V = (G >= 0).all(-1) & np.isfinite(G).all(-1); H, W = V.shape
masks = np.load(maskf)
keys = [k for k in masks.files if (only is None or k in only)]
Ss = {sg: Surface(np.load(f'{sdir}/{sg}.npz')['grid']) for sg in SEGS}
bb = {sg: (S.V.min(0), S.V.max(0)) for sg, S in Ss.items()}
LZ = {sg: (zarr.open_array(f'{ldir}/{sg}/inklabels.zarr/0', mode='r'), zarr.open_array(f'{ldir}/{sg}/supervision.zarr/0', mode='r')) for sg in SEGS}
print('loaded', round(time.time() - t0), 's', flush=True)
rng = np.random.default_rng(20260927)
files, dev_all = [], []
for key in keys:
    tt = time.time()
    r, c = (int(x[1:]) for x in key.split('_')[-2:])
    M = masks[key]; ny, nx = M.shape
    yy, xx = np.nonzero(M)
    gy = (r * T + DS * yy + (DS - 1) / 2) / s; gx = (c * T + DS * xx + (DS - 1) / 2) / s
    ci = np.floor(gy).astype(int); cj = np.floor(gx).astype(int); fy = gy - ci; fx = gx - cj
    i0, i1 = ci.min(), ci.max() + 2; j0, j1 = cj.min(), cj.max() + 2
    sub = V[i0:i1, j0:j1]; vi, vj = np.nonzero(sub); P = G[vi + i0, vj + j0].astype(np.float64)
    lo, hi = P.min(0) - 25, P.max(0) + 25
    best = np.full(len(yy), np.inf, np.float32); SUP = np.zeros(len(yy), np.uint8); INK = np.zeros(len(yy), np.uint8)
    for sg in SEGS:
        a, b = bb[sg]
        if (a > hi).any() or (b < lo).any():
            continue
        S = Ss[sg]
        D = np.full(len(P), np.inf); UV = np.full((len(P), 2), np.nan)
        for k in range(0, len(P), 100_000):
            d, uv, _ = nearest_uv(S, P[k:k + 100_000], TOL); D[k:k + 100_000] = d; UV[k:k + 100_000] = uv
        if not np.isfinite(D).any():
            continue
        Dg = np.full(sub.shape, np.inf); Ug = np.full(sub.shape + (2,), np.nan)
        Dg[vi, vj] = D; Ug[vi, vj] = UV
        li, lj = ci - i0, cj - j0
        c00, c01, c10, c11 = Dg[li, lj], Dg[li, lj + 1], Dg[li + 1, lj], Dg[li + 1, lj + 1]
        ok = np.isfinite(c00) & np.isfinite(c01) & np.isfinite(c10) & np.isfinite(c11)
        U = ((1 - fy) * (1 - fx))[:, None] * Ug[li, lj] + ((1 - fy) * fx)[:, None] * Ug[li, lj + 1] + \
            (fy * (1 - fx))[:, None] * Ug[li + 1, lj] + (fy * fx)[:, None] * Ug[li + 1, lj + 1]
        Dp = (1 - fy) * (1 - fx) * c00 + (1 - fy) * fx * c01 + fy * (1 - fx) * c10 + fy * fx * c11
        # corners of one quad must map to one contiguous patch of the segment (no fold/seam jump)
        span = np.maximum(np.abs(Ug[li, lj] - Ug[li + 1, lj + 1]).max(1), np.abs(Ug[li, lj + 1] - Ug[li + 1, lj]).max(1))
        ok &= span < 3.0
        idx = np.nonzero(ok)[0]
        if idx.size == 0:
            continue
        zi, zs = LZ[sg]
        pr = np.clip(np.rint(U[idx, 0] * 20).astype(np.int64), 0, zi.shape[0] - 1)
        pc = np.clip(np.rint(U[idx, 1] * 20).astype(np.int64), 0, zi.shape[1] - 1)
        r0, c0 = pr.min(), pc.min()
        bs = zs[r0:pr.max() + 1, c0:pc.max() + 1]; sv = bs[pr - r0, pc - c0] == 255; del bs
        bi = zi[r0:pr.max() + 1, c0:pc.max() + 1]; iv = bi[pr - r0, pc - c0] == 255; del bi
        upd = sv & (Dp[idx] < best[idx])
        best[idx[upd]] = Dp[idx[upd]]; SUP[idx[upd]] = 1; INK[idx[upd]] = iv[upd]
        # validation sample: exact mapping of the bilinear 3-D strip point
        if len(idx) > 0:
            smp = rng.choice(idx, min(200, len(idx)), replace=False)
            Ii, Jj = ci[smp], cj[smp]; Fy, Fx = fy[smp, None], fx[smp, None]
            f64 = lambda a, b: G[a, b].astype(np.float64)
            Q = (1 - Fy) * (1 - Fx) * f64(Ii, Jj) + (1 - Fy) * Fx * f64(Ii, Jj + 1) + Fy * (1 - Fx) * f64(Ii + 1, Jj) + Fy * Fx * f64(Ii + 1, Jj + 1)
            d2, uv2, _ = nearest_uv(S, Q, TOL)
            m2 = np.isfinite(d2)
            if m2.any():
                dev_all.append(np.abs(uv2[m2] - U[smp][m2]).max(1) * 20)
    ink = np.zeros((ny, nx), np.uint8); sup = np.zeros((ny, nx), np.uint8)
    ink[yy, xx] = INK; sup[yy, xx] = SUP
    fn = f'labels/{key}.npz'; path = os.path.join(outdir, fn)
    np.savez_compressed(path, ink=ink, sup=sup, n_sub=np.uint8(1))
    files.append({'file': fn, 'strip': strip, 'r': r, 'c': c, 'sha256': sha(path), 'bytes': os.path.getsize(path),
                  'shape': [ny, nx], 'n_certified_px': int(M.sum()), 'n_sup_px': int(sup.sum()), 'n_ink_px': int(ink.sum())})
    print(key, files[-1]['n_certified_px'], files[-1]['n_sup_px'], round(time.time() - tt, 1), 's', flush=True)
dev = np.concatenate(dev_all) if dev_all else np.zeros(0)
man = {'provenance': PROV, 'strip': strip, 'T_px': T, 'grid': 'x4 of tile', 'n_sub': 1,
       'what': 'DECL-P4-23 item 2 organizer ink labels on certified T pixels only (DECL-P4-21-A1); never any X pixel',
       'encoding': 'ink, sup uint8 (ceil(T/4) x ceil(T/4)); 1 = inklabel/supervision 255 at the mapped label px of the nearest '
                   'covering segment; 0 otherwise or outside the T mask; n_sub = 1 (one sample at each x4 pixel centre)',
       'mapping': {'tolerance_vox': TOL, 'rule': 'exact closest point (uvmap.nearest_uv) at strip vertices; segment UV and '
                   'distance bilinear inside the strip quad (4 corners mapped, UV span < 3 cells); label px round(uv*20)',
                   'validation_label_px_deviation_vs_exact': {'n': int(len(dev)), 'median': float(np.median(dev)) if len(dev) else None,
                                                              'p99': float(np.percentile(dev, 99)) if len(dev) else None,
                                                              'max': float(dev.max()) if len(dev) else None}},
       'inputs': {'mask_file_sha256': sha(maskf), 'strip_mesh_sha256': {f: sha(f'{mdir}/{f}') for f in ('x.tif', 'y.tif', 'z.tif')},
                  'labels': 'official 20260918 set; sha256 in logs/sib/p4-excl/downloads.jsonl'},
       'seconds': round(time.time() - t0, 1), 'files': files}
json.dump(man, open(os.path.join(outdir, f'labels_{strip}.json'), 'w'), indent=1)
print('done', man['seconds'], man['mapping']['validation_label_px_deviation_vs_exact'])
