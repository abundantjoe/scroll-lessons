# Provenance: Project HERCULES | owner the owner | [id removed]
[line withheld: prize-candidate detail under review]
2.4 um surface-volume chunks be replaced by rendering from the raw 2.4 um CT along the official mesh?
Numbers only: CT and surface-volume voxels are streamed as numbers, reduced to statistics and
discarded; no image is written or viewed; no ink model is run.

Official product (zarr .zattrs): num_slices 109, slice_step 1.0, source_group 0 (level 0 of the
masked 2.4 um volume), canvas = tifxyz grid x 20 (scale 0.05), chunks (109, 128, 128) uint8.
Our reproduction (stated, not documented by the product): canvas px (i, j) -> grid (i/20, j/20);
xyz and vertex normals (normalised central-difference du x dv, du along columns, dv along rows)
bilinearly interpolated; layer L = 0..108 at offset (L - 54) * 1 voxel along s * n, s in {+1, -1}
(both reported); trilinear interpolation of the raw level-0 volume; rounded to uint8.

usage: nodata_recovery.py coverage <tiles.json> <out.json>
       nodata_recovery.py fidelity <seg> <r> <c> <out.json> [window_px=1024] [signs=+1,-1]
"""
from __future__ import annotations

import io
import json
import math
import os
import sys
import time
import concurrent.futures as cf
import urllib.request
import urllib.parse
import re
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mesh_audit import normals  # noqa: E402

S3 = 'https://vesuvius-challenge-open-data.s3.amazonaws.com/PHercParis4'
RAW = f'{S3}/volumes/20260411134726-2.400um-0.2m-78keV-masked.zarr/0'
SV = S3 + '/segments/{seg}/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr/0'
[line withheld: prize-candidate detail under review]
MESH_CACHE = Path('/home/user/scratch/outer')
CH = 128
CHUNK_BYTES = CH ** 3
Z0, Z1 = 23, 85


def fetch(url, rng=None, head=False, tries=6):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, method='HEAD' if head else 'GET')
            if rng:
                req.add_header('Range', f'bytes={rng[0]}-{rng[1]}')
            with urllib.request.urlopen(req, timeout=120) as r:
                return (r.status, None if head else r.read())
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return (e.code, None)
        except Exception:
            pass
        time.sleep(2 ** k)
    raise RuntimeError(url)


def load_mesh(seg):
    f = [MESH_CACHE / f'{seg}_{c}.npy' for c in 'xyz']
    if not all(p.exists() for p in f):
        import tifffile
        MESH_CACHE.mkdir(parents=True, exist_ok=True)
        base = f'{S3}/segments/{seg}/mesh/{seg.split("-")[0]}-on-20260411134726-2.4um.tifxyz/'
        for c, p in zip('xyz', f):
            np.save(p, tifffile.imread(io.BytesIO(fetch(base + c + '.tif')[1])).astype(np.float32))
    X, Y, Z = (np.load(p) for p in f)
    V = (X != -1) & np.isfinite(Z) & (Z > 0)
    return np.stack([X, Y, Z], -1).astype(np.float64), V


def tile_grid(seg, r, c, H, W):
    T = TILE_PX[seg]
    return (r * T) // 20, min(H, -(-((r + 1) * T) // 20)), (c * T) // 20, min(W, -(-((c + 1) * T) // 20))


# ---------------------------------------------------------------- coverage
def cmd_coverage(tiles_json, out):
    tiles = json.load(open(tiles_json))['nodata_or_partial']
    by_seg = {}
    for t in tiles:
        seg, rc = t['tile'].rsplit('_r', 1)
        r, c = map(int, rc.split('_c'))
        by_seg.setdefault(seg, []).append((r, c, t))
    status = {}
    res = json.load(open(out))['tiles'] if os.path.exists(out) else []
    done = {x['tile'] for x in res}
    rc_file = out + '.rowcache.json'
    rowcache = {tuple(map(int, k.split(','))): set(v) for k, v in json.load(open(rc_file)).items()} if os.path.exists(rc_file) else {}
    t_all = time.time()
    budget = float(os.environ.get('COV_BUDGET_S', '1e9'))
    with cf.ThreadPoolExecutor(64) as pool:
        for seg, lst in by_seg.items():
            P, V = load_mesh(seg)
            H, W = V.shape
            for (r, c, t) in lst:
                if t['tile'] in done:
                    continue
                if time.time() - t_all > budget:
                    print('BUDGET_EXIT', flush=True)
                    return
                t0 = time.time()
                g0, g1, h0, h1 = tile_grid(seg, r, c, H, W)
                Pt = P[g0:g1, h0:h1]
                v = V[g0:g1, h0:h1]
                N = normals(np.where(v[..., None], Pt, np.nan))
                okn = v & np.all(np.isfinite(N), -1)
                pts = Pt[okn]
                nn = N[okn]
                offs = np.r_[np.arange(-54, 55, 16), 54.0]
                keys_v = []
                for o in offs:
                    q = np.floor(pts + o * nn).astype(np.int64) // CH
                    keys_v.append((q[:, 2] << 40) | (q[:, 1] << 20) | q[:, 0])
                K = np.stack(keys_v, 1)
                uk = np.unique(K)
                rows_needed = sorted({(int(k) >> 40, (int(k) >> 20) & 0xFFFFF) for k in uk} - set(rowcache))

                def list_row(zy):
                    cz, cy = zy
                    got, token = set(), None
                    for _ in range(20):
                        url = (f'https://vesuvius-challenge-open-data.s3.amazonaws.com/?list-type=2&prefix='
                               f'PHercParis4/volumes/20260411134726-2.400um-0.2m-78keV-masked.zarr/0/{cz}/{cy}/&max-keys=1000'
                               + (f'&continuation-token={urllib.parse.quote(token)}' if token else ''))
                        body = fetch(url)[1].decode()
                        got |= {int(x) for x in re.findall(r'/0/%d/%d/(\d+)</Key>' % (cz, cy), body)}
                        m = re.search(r'<NextContinuationToken>([^<]+)</NextContinuationToken>', body)
                        if not m:
                            break
                        token = m.group(1)
                    return zy, got
                for zy, got in pool.map(list_row, rows_needed):
                    rowcache[zy] = got
                for k in uk:
                    k = int(k)
                    status[k] = 200 if (k & 0xFFFFF) in rowcache[(k >> 40, (k >> 20) & 0xFFFFF)] else 404
                ex = np.array([status[int(k)] == 200 for k in uk])
                exists = dict(zip(uk.tolist(), ex.tolist()))
                cov = np.array([all(exists[int(k)] for k in row) for row in K]) if len(K) else np.zeros(0, bool)
                # the vertex itself only
                q0 = np.floor(pts).astype(np.int64) // CH
                k0 = (q0[:, 2] << 40) | (q0[:, 1] << 20) | q0[:, 0]
                cov0 = np.array([exists.get(int(k), status.get(int(k)) == 200) for k in k0]) if len(k0) else np.zeros(0, bool)
                rec = {'tile': t['tile'], 'frac91_dryrun': t.get('frac91'), 'n_mesh_valid_vertices': int(v.sum()),
                       'n_vertices_with_normal': int(okn.sum()),
                       'frac_vertices_chunk_at_vertex': float(cov0.mean()) if cov0.size else None,
                       'frac_vertices_all_chunks_pm54': float(cov.mean()) if cov.size else None,
                       'n_unique_chunks': int(len(uk)), 'n_chunks_present': int(ex.sum()),
                       'raw_bytes_needed': int(ex.sum()) * CHUNK_BYTES,
                       'raw_gb_needed': round(int(ex.sum()) * CHUNK_BYTES / 1e9, 2), 'wall_s': round(time.time() - t0, 1)}
                res.append(rec)
                json.dump({f'{a},{b}': sorted(v) for (a, b), v in rowcache.items()}, open(rc_file, 'w'))
                print(json.dumps(rec), flush=True)
                json.dump({'provenance': 'Project HERCULES | owner the owner | [id removed]',
                           'raw_volume': RAW, 'rule': 'vertex covered iff every raw level-0 chunk (128^3 u8, 2 MiB, uncompressed) touched at offsets -54..+54 vox along the normal (sampled every 16 vox and at +-54) exists in the bucket (first 6 tiles: HTTP HEAD; later tiles: S3 ListObjectsV2 of each chunk row, equivalent)',
                           'tiles': res, 'wall_s': round(time.time() - t_all, 1)}, open(out, 'w'), indent=1)


# ---------------------------------------------------------------- fidelity
class Cache:
    def __init__(self):
        self.d = {}

    def get(self, keys, pool):
        need = [k for k in keys if k not in self.d]

        def g(k):
            s, b = fetch(f'{RAW}/{k[0]}/{k[1]}/{k[2]}')
            return k, (np.frombuffer(b, np.uint8).reshape(CH, CH, CH) if s == 200 else None)
        for k, a in pool.map(g, need):
            self.d[k] = a
        return self.d


def trilinear(pts, cache, pool):
    lo = np.floor(pts).astype(np.int64)
    fr = (pts - lo).astype(np.float32)
    keys = set()
    for dz in (0, 1):
        for dy in (0, 1):
            for dx in (0, 1):
                c = (lo + [dx, dy, dz]) // CH
                keys.update(map(tuple, np.unique(c[:, ::-1], axis=0).tolist()))
    ch = cache.get(sorted(keys), pool)
    out = np.zeros(len(pts), np.float32)
    missing = np.zeros(len(pts), bool)
    for dz in (0, 1):
        for dy in (0, 1):
            for dx in (0, 1):
                v = lo + [dx, dy, dz]
                w = (fr[:, 0] if dx else 1 - fr[:, 0]) * (fr[:, 1] if dy else 1 - fr[:, 1]) * (fr[:, 2] if dz else 1 - fr[:, 2])
                c = v // CH
                o = v % CH
                key = (c[:, 2] << 40) | (c[:, 1] << 20) | c[:, 0]
                order = np.argsort(key, kind='stable')
                ks = key[order]
                cut = np.r_[0, np.nonzero(np.diff(ks))[0] + 1, len(ks)]
                vals = np.zeros(len(v), np.float32)
                for a0, a1 in zip(cut[:-1], cut[1:]):
                    idx = order[a0:a1]
                    k = (int(c[idx[0], 2]), int(c[idx[0], 1]), int(c[idx[0], 0]))
                    arr = ch[k]
                    if arr is None:
                        missing[idx] = True
                        continue
                    vals[idx] = arr[o[idx, 2], o[idx, 1], o[idx, 0]]
                out += w * vals
    return out, missing


def bilinear_grid(G, gy, gx):
    y0 = np.clip(np.floor(gy).astype(int), 0, G.shape[0] - 2)
    x0 = np.clip(np.floor(gx).astype(int), 0, G.shape[1] - 2)
    fy = (gy - y0)[..., None]
    fx = (gx - x0)[..., None]
    return (G[y0, x0] * (1 - fy) * (1 - fx) + G[y0 + 1, x0] * fy * (1 - fx) +
            G[y0, x0 + 1] * (1 - fy) * fx + G[y0 + 1, x0 + 1] * fy * fx)


def cmd_fidelity(seg, r, c, out, window=1024, signs='+1,-1'):
    r, c, window = int(r), int(c), int(window)
    signs = [int(x) for x in signs.split(',')]
    t0 = time.time()
    P, V = load_mesh(seg)
    H, W = V.shape
    T = TILE_PX[seg]
    cy0 = r * T + T // 2 - window // 2
    cx0 = c * T + T // 2 - window // 2
    # grid block around the window (+2 cells margin)
    gy0, gy1 = max(0, cy0 // 20 - 2), min(H, (cy0 + window) // 20 + 3)
    gx0, gx1 = max(0, cx0 // 20 - 2), min(W, (cx0 + window) // 20 + 3)
    Pb = np.where(V[gy0:gy1, gx0:gx1, None], P[gy0:gy1, gx0:gx1], np.nan)
    Nb = normals(Pb)
    ii, jj = np.mgrid[cy0:cy0 + window, cx0:cx0 + window]
    gy, gx = ii / 20.0 - gy0, jj / 20.0 - gx0
    xyz = bilinear_grid(Pb, gy, gx)
    nrm = bilinear_grid(Nb, gy, gx)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True) + 1e-12
    valid = np.all(np.isfinite(xyz), -1) & np.all(np.isfinite(nrm), -1)
    # official window (all 109 layers)
    t1 = time.time()
    off = np.zeros((109, window, window), np.uint8)
    base = SV.format(seg=seg)
    jobs = [(a, b) for a in range(cy0 // CH, (cy0 + window - 1) // CH + 1) for b in range(cx0 // CH, (cx0 + window - 1) // CH + 1)]
    with cf.ThreadPoolExecutor(32) as pool:
        for (a, b), (s, raw) in zip(jobs, pool.map(lambda ab: fetch(f'{base}/0/{ab[0]}/{ab[1]}'), jobs)):
            if s != 200:
                continue
            arr = np.frombuffer(raw, np.uint8).reshape(109, CH, CH)
            ya, yb = max(cy0, a * CH), min(cy0 + window, (a + 1) * CH)
            xa, xb = max(cx0, b * CH), min(cx0 + window, (b + 1) * CH)
            off[:, ya - cy0:yb - cy0, xa - cx0:xb - cx0] = arr[:, ya - a * CH:yb - a * CH, xa - b * CH:xb - b * CH]
        t_off = time.time() - t1
        cache = Cache()
        pts0 = xyz[valid]
        n0 = nrm[valid]
        res = {'seg': seg, 'tile': f'r{r}_c{c}', 'window_px': window, 'window_canvas_yx': [int(cy0), int(cx0)],
               'mesh_valid_frac_window': float(valid.mean()), 'official_read_s': round(t_off, 1),
               'official_zero_frac_layers23_84': float((off[Z0:Z1][:, valid] == 0).mean())}
        for s in signs:
            t2 = time.time()
            ours = np.zeros((109, int(valid.sum())), np.uint8)
            miss = np.zeros(int(valid.sum()), bool)
            for L in range(109):
                v, m = trilinear(pts0 + (s * (L - 54)) * n0, cache, pool)
                ours[L] = np.clip(np.rint(v), 0, 255).astype(np.uint8)
                miss |= m
            t_render = time.time() - t2
            per = []
            for L in range(Z0, Z1):
                a = ours[L].astype(np.float64)
                b = off[L][valid].astype(np.float64)
                rr = float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else None
                nz = b > 0
                rnz = float(np.corrcoef(a[nz], b[nz])[0, 1]) if nz.sum() > 10 and a[nz].std() > 0 and b[nz].std() > 0 else None
                per.append({'layer': L, 'r': rr, 'r_official_nonzero': rnz,
                            'mean_diff': float(a.mean() - b.mean()), 'std_diff': float(a.std() - b.std()),
                            'p1_ours': float(np.percentile(a, 1)), 'p1_off': float(np.percentile(b, 1)),
                            'p99_ours': float(np.percentile(a, 99)), 'p99_off': float(np.percentile(b, 99)),
                            'exact_equal_frac': float(np.mean(a == b))})
            rs = [x['r'] for x in per if x['r'] is not None]
            res[f'sign_{s:+d}'] = {'render_s': round(t_render, 1), 'raw_chunks_fetched': len(cache.d),
                                   'missing_raw_sample_frac': float(miss.mean()),
                                   'median_r': float(np.median(rs)) if rs else None, 'worst_r': float(np.min(rs)) if rs else None,
                                   'median_exact_equal_frac': float(np.median([x['exact_equal_frac'] for x in per])),
                                   'layers': per}
            print(seg, r, c, s, res[f'sign_{s:+d}']['median_r'], res[f'sign_{s:+d}']['worst_r'], round(t_render), flush=True)
    res['wall_s'] = round(time.time() - t0, 1)
    res['tile_extrapolation_factor'] = round((TILE_PX[seg] ** 2) / (window ** 2), 1)
    json.dump(res, open(out, 'w'), indent=1)


if __name__ == '__main__':
    if sys.argv[1] == 'coverage':
        cmd_coverage(*sys.argv[2:4])
    else:
        cmd_fidelity(*sys.argv[2:])
