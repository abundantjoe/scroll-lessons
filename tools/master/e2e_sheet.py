#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-E2E-1 stages of the HERCULES master pipeline (one sheet trace -> surface over a y band -> render -> master ink model -> gold).
Frame (UMB-GEOMETRY-RESULT): sections are xz planes indexed by y; everything at the scan's native voxel size (OME level 0).
stages (all write into <out>):
  trace  : the organizers' surface prediction (level 0) is the ridge prior; the seed section's strongest ridge nearest the
           mask centre is traced both ways with the ridge-tangent tracer of tools/umb/uturns.py (u = signed arc length);
           the trace is propagated to the band's sections by re-seeding at u = 0 (snap within one sheet width) and re-tracing;
           writes surface.npz (Z, X per (section, u)), surface tifxyz (x/y/z.tif at 8-vox u cells), trace_checks.json (G1-G3).
  render : the CT is sampled along the in-section normal at offsets -8..+8 (trilinear) for EVERY y of the band (bilinear
           S(u, y) between traced sections); writes render.npz (17, Y, U) uint8, centre.png, fibre metrics (G5, coherence).
  ink    : the DECL-FL-7 master model (EdgeBank + UNet3D, fp32) on 16-layer stacks, 64x64 crops, stride 32, Hann blending,
           forward and reversed layer order; writes ink_fwd.png, ink_rev.png, ink.npz, agreement.
  gold   : centre layer with gold where p_fwd > threshold; writes gold.png (+ gold_preview.png at 1/4), checks.json (all bars).
Nothing here reads letters; the gold layer is model output whose held-out accuracy is written beside it.
usage: e2e_sheet.py <stage> <config.json> <out_dir> [--ct_l4 /dev/shm/e2e/ct_L4.npy] [--threads 32]"""
import argparse, json, os, sys, time, numpy as np
from scipy import ndimage as ndi
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'umb')); import uturns as UT
from st_axis import st_accumulate, st_eigen

class Zarr0:
    """Threaded level-0 chunk reader (raw uint8 or blosc), dimension_separator '/', keys i/j/k over (z, y, x)."""
    def __init__(self, key, threads=32):
        import s3fs; self.fs = s3fs.S3FileSystem(anon=True); self.key = key; za = json.loads(self.fs.cat_file(key + '/.zarray'))
        self.shape, self.chunks, self.comp = za['shape'], za['chunks'], za.get('compressor'); self.ex = ThreadPoolExecutor(threads)
        if self.comp: from numcodecs import get_codec; self.codec = get_codec(self.comp)
    def chunk(self, ijk):
        i, j, k = ijk
        for attempt in range(5):                                                                   # transient S3 stream errors: retry with backoff
            try: raw = self.fs.cat_file(f'{self.key}/{i}/{j}/{k}'); break
            except FileNotFoundError: return ijk, None
            except Exception as e:
                if attempt == 4: raise
                time.sleep(1.5 * (attempt + 1))
        if self.comp: raw = self.codec.decode(raw)
        return ijk, np.frombuffer(raw, np.uint8).reshape(self.chunks)
    def block(self, z0, z1, y0, y1, x0, x1):
        """dense uint8 block (z1-z0, y1-y0, x1-x0); missing chunks are 0."""
        cz, cy, cx = self.chunks; Z, Y, X = self.shape; z1, y1, x1 = min(z1, Z), min(y1, Y), min(x1, X); out = np.zeros((z1 - z0, y1 - y0, x1 - x0), np.uint8)
        keys = [(i, j, k) for i in range(z0 // cz, (z1 - 1) // cz + 1) for j in range(y0 // cy, (y1 - 1) // cy + 1) for k in range(x0 // cx, (x1 - 1) // cx + 1)]
        for b0 in range(0, len(keys), 256):
            for (i, j, k), a in self.ex.map(self.chunk, keys[b0:b0 + 256]):
                if a is None: continue
                zs, ze = max(z0, i * cz), min(z1, (i + 1) * cz); ys, ye = max(y0, j * cy), min(y1, (j + 1) * cy); xs, xe = max(x0, k * cx), min(x1, (k + 1) * cx)
                out[zs - z0:ze - z0, ys - y0:ye - y0, xs - x0:xe - x0] = a[zs - i * cz:ze - i * cz, ys - j * cy:ye - j * cy, xs - k * cx:xe - k * cx]
        return out
    def sections(self, ys, z0, z1, x0, x1):
        """dict y -> (z1-z0, x1-x0) uint8 xz section, fetching each chunk row once."""
        cz, cy, cx = self.chunks; out = {}
        for j in sorted({y // cy for y in ys}):
            yy = [y for y in ys if y // cy == j]; blk = {}
            keys = [(i, j, k) for i in range(z0 // cz, (z1 - 1) // cz + 1) for k in range(x0 // cx, (x1 - 1) // cx + 1)]
            secs = {y: np.zeros((z1 - z0, x1 - x0), np.uint8) for y in yy}
            for b0 in range(0, len(keys), 256):
                for (i, _, k), a in self.ex.map(self.chunk, keys[b0:b0 + 256]):
                    if a is None: continue
                    zs, ze = max(z0, i * cz), min(z1, (i + 1) * cz); xs, xe = max(x0, k * cx), min(x1, (k + 1) * cx)
                    for y in yy: secs[y][zs - z0:ze - z0, xs - x0:xe - x0] = a[zs - i * cz:ze - i * cz, y - j * cy, xs - k * cx:xe - k * cx]
            out.update({y: np.packbits(secs[y] > 0, axis=1) for y in secs}); del secs                                         # bit-packed (the prediction is binary): 8x smaller
        return out

def ct_sections(ct, ys, z0, z1, x0, x1, store, n=16):
    """For every band y: the stripe-removed mean of CT sections y..y+n-1 (uint8, 1..255 inside the mask, 0 outside), saved as
    <store>/sec_<y>.npy. Streams one chunk row and one x strip (1024) at a time; per-y means live in uint8 memmaps on disk."""
    from st_axis import stripe_removal
    os.makedirs(store, exist_ok=True); todo = [y for y in ys if not os.path.exists(f'{store}/sec_{y}.npy')]
    if not todo: return
    Z, X = z1 - z0, x1 - x0; cz, cy, cx = ct.chunks
    mm_ = {y: (np.lib.format.open_memmap(f'{store}/raw_{y}.npy', mode='r+') if os.path.exists(f'{store}/raw_{y}.npy') else np.lib.format.open_memmap(f'{store}/raw_{y}.npy', mode='w+', dtype=np.uint8, shape=(int(Z), int(X)))) for y in todo}
    rows = sorted({y // cy for y in todo} | {(y + n - 1) // cy for y in todo})
    for j in rows:
        if os.path.exists(f'{store}/row_{j}.done'): print('ct row', j, 'already done', flush=True); continue                 # resume after a crash
        yy = [y for y in todo if y // cy == j or (y + n - 1) // cy == j]; ry0, ry1 = j * cy, (j + 1) * cy
        for xs0 in range(x0, x1, 1024):
            xs1 = min(x1, xs0 + 1024); blk = ct.block(z0, z1, ry0, ry1, xs0, xs1)                              # (Z, 128, X') uint8, one fetch per row and strip
            for y in yy:
                a, b = max(y, ry0) - ry0, min(y + n, ry1) - ry0
                if b <= a: continue
                part = blk[:, a:b, :].astype(np.float32).sum(1) / n                                            # partial mean (sections of this row); rows add up
                mm_[y][:, xs0 - x0:xs1 - x0] = np.clip(mm_[y][:, xs0 - x0:xs1 - x0].astype(np.float32) + part, 0, 255).astype(np.uint8)
            del blk
        open(f'{store}/row_{j}.done', 'w').write('1'); print('ct row', j, 'strips done', flush=True)
    for y in todo:
        raw = np.asarray(mm_[y]); mask = raw > 0; img = stripe_removal(raw.astype(np.float32) / 255.0, mask); lo, hi = np.percentile(img[mask], [0.5, 99.5]) if mask.any() else (0, 1)
        sec = (np.clip((img - lo) / (hi - lo + 1e-6), 0, 1) * 254 + 1).astype(np.uint8) * mask; np.save(f'{store}/sec_{y}.npy', sec); del mm_[y], raw, img, sec; os.remove(f'{store}/raw_{y}.npy')

def band_sections(cfg):
    b = cfg['band']; mm = 1000.0 / cfg['vox_um']; h = int(round(b['half_mm'] * mm)); y0 = b['y0']; dy = b['dy']
    ys = list(range(y0, y0 - h - 1, -dy))[::-1][:-1] + list(range(y0, y0 + h + 1, dy)); return sorted(set(ys)), y0, h

def bbox_from_l4(l4_path, y, margin=400):
    """mask bbox (z0, z1, x0, x1) at level 0 from the level-4 volume at the band's y."""
    V = np.load(l4_path, mmap_mode='r'); m = np.asarray(V[:, min(y // 16, V.shape[1] - 1), :]) > 0; m = ndi.binary_opening(m, iterations=3)
    lab, n = ndi.label(m); sizes = ndi.sum(m, lab, range(1, n + 1)); m = lab == (1 + int(np.argmax(sizes)))                     # the scroll body = the largest component
    rows = np.nonzero(m.sum(1) > 0)[0]; cols = np.nonzero(m.sum(0) > 0)[0]; Z0, X0 = V.shape[0] * 16, V.shape[2] * 16
    return max(0, rows.min() * 16 - margin), min(Z0, (rows.max() + 1) * 16 + margin), max(0, cols.min() * 16 - margin), min(X0, (cols.max() + 1) * 16 + margin)

def prep(sec, sigma=3.0, X=None):
    if sec.dtype == np.uint8 and X is not None and sec.shape[1] * 8 >= X: sec = np.unpackbits(sec, axis=1)[:, :X] * np.uint8(255)
    img = ndi.gaussian_filter(sec.astype(np.float32) / 255.0, sigma); mask = ndi.binary_dilation(sec > 0, iterations=1, structure=np.ones((3, 3), bool)); mask = ndi.binary_dilation(mask, structure=np.ones((5, 5), bool), iterations=8)
    return img, mask

def trace_coast(R, nz, nx, mask, seed, tau, max_len, gap_max=60, snap_r=6):
    """Single ridge-tangent trace with COASTING: when the ridge is lost (R < tau/2) the walk continues straight along the last
    tangent for up to gap_max steps, re-acquiring the ridge within +-snap_r along the normal; returns (path, gaps)."""
    Z, X = R.shape; out = []; gaps = []
    for sign in (1.0, -1.0):
        z, x = float(seed[0]), float(seed[1]); d = None; pts = []; lost = 0; n_gap = 0
        for step in range(max_len):
            zi, xi = int(round(z)), int(round(x))
            if not (0 <= zi < Z and 0 <= xi < X and mask[zi, xi]): break
            n0, n1 = nz[zi, xi], nx[zi, xi]; t = np.array([-n1, n0]); t /= (np.hypot(*t) + 1e-9)
            if d is None: d = t * sign
            elif float(t @ d) < 0: t = -t
            r0 = R[zi, xi]
            if r0 >= 0.5 * tau:                                                           # on the ridge: snap across (+-snap_r along the normal, best R)
                best, bz, bx = r0, z, x
                for o in range(-snap_r, snap_r + 1):
                    zz, xx = int(round(z + o * n0)), int(round(x + o * n1))
                    if 0 <= zz < Z and 0 <= xx < X and R[zz, xx] > best: best, bz, bx = R[zz, xx], zz, xx
                z, x = float(bz), float(bx); d = 0.7 * d + 0.3 * t; d /= (np.hypot(*d) + 1e-9)
                if lost: gaps.append(lost); lost = 0
            else:                                                                        # coasting through a gap along the last tangent
                lost += 1
                if lost > gap_max: break
                found = False
                for o in range(-snap_r, snap_r + 1):
                    zz, xx = int(round(z + o * n0)), int(round(x + o * n1))
                    if 0 <= zz < Z and 0 <= xx < X and R[zz, xx] >= tau: z, x = float(zz), float(xx); found = True; break
                if found: gaps.append(lost); lost = 0; continue
            pts.append((z, x)); z += d[0]; x += d[1]
        out.append(np.array(pts, np.float32))
    a, b = out; poly = np.concatenate([a[::-1], b[1:]]) if len(a) and len(b) else (a if len(a) else b)
    return poly, gaps

def trace_from(R, nz, nx, cl, mask, seed, tau, p):
    poly, gaps = trace_coast(R, nz, nx, mask, seed, tau, p['max_len'])
    if len(poly) < 10: return None
    d = np.hypot(*np.diff(poly, axis=0).T); s = np.concatenate([[0], np.cumsum(d)]); k = int(np.argmin(np.hypot(poly[:, 0] - seed[0], poly[:, 1] - seed[1]))); return poly, s - s[k]

def snap(cl, pt, r):
    z, x = int(round(pt[0])), int(round(pt[1])); Z, X = cl.shape; sub = cl[max(0, z - r):z + r + 1, max(0, x - r):x + r + 1]
    if not sub.any(): return None
    zz, xx = np.nonzero(sub); d = np.hypot(zz - (z - max(0, z - r)), xx - (x - max(0, x - r))); i = int(np.argmin(d)); return (zz[i] + max(0, z - r), xx[i] + max(0, x - r)) if d[i] <= r else None

def sheet_fields(sec, mask):
    """Gated ridge strength (symmetric flanks at half a pitch, voids excluded), orientation field (normal dz, dx), coherence, void mask, tau."""
    from st_axis import st_accumulate, st_eigen
    Z, X = sec.shape; img = ndi.gaussian_filter(sec.astype(np.float32) / 255.0, 1.0); R, nz, nx = UT.hessian_ridge(img, 4.0); d = 22.0; sym = np.zeros_like(R)
    for z0 in range(0, Z, 1024):
        z1 = min(Z, z0 + 1024); zz, xx = np.mgrid[z0:z1, 0:X].astype(np.float32); c = img[z0:z1]
        a_ = ndi.map_coordinates(img, [zz + d * nz[z0:z1], xx + d * nx[z0:z1]], order=1, mode='nearest'); b_ = ndi.map_coordinates(img, [zz - d * nz[z0:z1], xx - d * nx[z0:z1]], order=1, mode='nearest'); sym[z0:z1] = np.minimum(c - a_, c - b_)
    void = ndi.binary_dilation((sec < np.percentile(sec[mask], 2)) & mask, iterations=4); Rs = np.where((sym > 0.02) & ~void, R, 0).astype(np.float32); del sym, R, nz, nx
    th, coh, _ = st_eigen(st_accumulate([img], 2.0), 8.0); del img; nzv = Rs[mask & (Rs > 0)]; tau = float(np.median(nzv) + 3 * np.median(np.abs(nzv - np.median(nzv)))) if nzv.size else 1e9; del nzv
    FZ, FX = np.sin(th).astype(np.float16), np.cos(th).astype(np.float16); del th; import gc; gc.collect()
    return Rs, FZ, FX, coh.astype(np.float16), void, tau

def trace_field(Rs, FZ, FX, coh, mask, void, seed, tau, max_len=60000, snap_r=6, unanch_max=300, coh_min=0.2):
    """Streamline of the orientation field from the seed, both ways, re-anchored to the gated ridge within snap_r along the normal.
    Returns (poly (L,2) as (z,x), stats: anchored fraction, jumps > 3 vox, stop reasons)."""
    Z, X = Rs.shape; out = []; stats = {'anchored': 0, 'steps': 0, 'jumps': 0, 'stop': []}; last = np.full((Z // 4 + 1, X // 4 + 1), -10**9, np.int64)
    for sign in (1.0, -1.0):
        z, x = float(seed[0]), float(seed[1]); dv = None; pts = []; un = 0; low = 0; why = 'max_len'
        for step in range(max_len):
            zi, xi = int(round(z)), int(round(x))
            if not (0 <= zi < Z and 0 <= xi < X): why = 'edge'; break
            if not mask[zi, xi]: why = 'mask'; break
            if void[zi, xi]: why = 'void'; break
            if last[zi // 4, xi // 4] > -10**8 and step - last[zi // 4, xi // 4] > 200: why = 'loop'; break
            last[zi // 4, xi // 4] = step
            if step % 500 == 499 and len(pts) >= 500:                                               # progress test: 500 steps must move the walk >= 100 vox
                if np.hypot(z - pts[-500][0], x - pts[-500][1]) < 100: why = 'stall'; break
            n0, n1 = float(FZ[zi, xi]), float(FX[zi, xi]); t = np.array([-n1, n0], np.float64)
            if dv is None: dv = t * sign
            elif float(t @ dv) < 0: t = -t
            if coh[zi, xi] < coh_min:
                low += 1
                if low > 50: why = 'lowcoh'; break
            else: low = 0
            best, bz, bx = 0.5 * tau, None, None
            for o in range(-snap_r, snap_r + 1):
                zz_, xx_ = int(round(z + o * n0)), int(round(x + o * n1))
                if 0 <= zz_ < Z and 0 <= xx_ < X and Rs[zz_, xx_] > best: best, bz, bx = Rs[zz_, xx_], zz_, xx_
            if bz is not None:
                if abs(bz - z) + abs(bx - x) > 3: stats['jumps'] += 1
                z, x = float(bz), float(bx); un = 0; stats['anchored'] += 1
            else:
                un += 1
                if un > unanch_max: why = 'unanchored'; break
            dv = 0.8 * dv + 0.2 * t; dv /= (np.hypot(*dv) + 1e-9); pts.append((z, x)); z += dv[0]; x += dv[1]; stats['steps'] += 1
        stats['stop'].append(why); out.append(np.array(pts, np.float32))
    a_, b_ = out; poly = np.concatenate([a_[::-1], b_[1:]]) if len(a_) and len(b_) else (a_ if len(a_) else b_); return poly, stats

def stage_trace(cfg, out, a):
    t0 = time.time(); ys, y0, h = band_sections(cfg); mm = 1000.0 / cfg['vox_um']; sheet = 14.0; p = dict(UT.DEFAULTS); p['max_len'] = 40000
    z0, z1, x0, x1 = bbox_from_l4(a.ct_l4, y0); print('bbox z', z0, z1, 'x', x0, x1, 'sections', len(ys), flush=True)
    ct = Zarr0(cfg['ct_l0'], a.threads); store = f"/work/e2e/{cfg['name']}_{y0}"; ct_sections(ct, ys, z0, z1, x0, x1, store); print('ct sections ready', round(time.time() - t0), 's', flush=True)
    secs = {y: np.load(f'{store}/sec_{y}.npy', mmap_mode='r') for y in ys}
    cache = f"/dev/shm/e2e/secs_{cfg['name']}_{y0}_{len(ys)}.npz"; pred = None
    if os.path.exists(cache): F = np.load(cache); pred = {int(k): F[k] for k in F.files}                                  # the prediction, report only
    order = [y0] + sorted([y for y in ys if y > y0]) + sorted([y for y in ys if y < y0], reverse=True)           # seed section first, then outward both ways
    res = {}; prev = {}
    # seed section: grid search (cached) and the reference curve
    sec = np.asarray(secs[y0]); mask = sec > 0; Rs, FZ, FX, coh, void, tau = sheet_fields(sec, mask); cl = Rs > tau
    seedcache = f"/work/e2e/{cfg['name']}_{y0}/seed_{y0}.json"
    if os.path.exists(seedcache):
        J = json.load(open(seedcache)); sd = tuple(J['sd']); cand_lengths_mm = J['cand_lengths_mm']; print('seed from cache', sd, flush=True)
    else:
        cands = []; mm4, mm8 = int(4 * mm), int(8 * mm)
        for zc in range(400, z1 - z0 - 400, mm4):
            for xc in range(400, x1 - x0 - 400, mm8):
                sd0 = snap(cl, (zc, xc), 80)
                if sd0 is None or not mask[sd0] or void[sd0]: continue
                poly0, st0 = trace_field(Rs, FZ, FX, coh, mask, void, sd0, tau)
                if len(poly0) < 10: continue
                cands.append((float(np.hypot(np.ptp(poly0[:, 0]), np.ptp(poly0[:, 1]))), len(poly0), round(st0['anchored'] / max(st0['steps'], 1), 2), st0['stop'], (int(sd0[0]), int(sd0[1]))))
        if not cands: raise SystemExit('no ridge candidates on the grid')
        cands.sort(key=lambda c: -c[0]); sd = cands[0][4]; cand_lengths_mm = [[round(c[0] / mm, 1), c[1], c[2], c[3]] for c in cands[:20]]
        print('seed candidates (extent mm, points, anchored, stops):', cand_lengths_mm[:6], 'chosen', sd, 'of', len(cands), flush=True); json.dump({'sd': [int(sd[0]), int(sd[1])], 'cand_lengths_mm': cand_lengths_mm}, open(seedcache, 'w'))
    poly, st = trace_field(Rs, FZ, FX, coh, mask, void, sd, tau); poly = ndi.gaussian_filter1d(poly.astype(np.float64), 3, axis=0).astype(np.float32)
    dd = np.hypot(*np.diff(poly, axis=0).T); su = np.concatenate([[0], np.cumsum(dd)]); k = int(np.argmin(np.hypot(poly[:, 0] - sd[0], poly[:, 1] - sd[1]))); u = su - su[k]
    U = np.arange(np.floor(u.min()), np.ceil(u.max()) + 1, 4.0); C0 = np.stack([np.interp(U, u, poly[:, 0]), np.interp(U, u, poly[:, 1])], 1)          # the reference curve, window coords, every 4 vox of u
    res[y0] = {'status': 'ok', 'curve': C0, 'seed': [int(sd[0]) + z0, int(sd[1]) + x0], 'anchored_frac': round(st['anchored'] / max(st['steps'], 1), 3), 'jumps': st['jumps'], 'stops': st['stop'], 'extent_mm': round(float(np.hypot(np.ptp(poly[:, 0]), np.ptp(poly[:, 1])) / mm), 2), 'n': int(len(poly)), 'umin': float(u.min()), 'umax': float(u.max()), 'tracked_frac': 1.0}
    if pred is not None and y0 in pred:
        pm = np.unpackbits(pred[y0], axis=1); pz = np.clip(np.rint(poly[:, 0]).astype(int), 0, pm.shape[0] - 1); px = np.clip(np.rint(poly[:, 1]).astype(int) + (x0 - 544), 0, pm.shape[1] - 1); res[y0]['pred_frac'] = float(ndi.maximum_filter(pm, 5)[pz, px].mean())
    print(y0, 'seed trace', len(poly), 'u', round(u.min() / mm, 1), round(u.max() / mm, 1), 'mm', 'stops', st['stop'], 'anch', res[y0]['anchored_frac'], 'pred', res[y0].get('pred_frac'), flush=True)
    del Rs, FZ, FX, coh, void, cl, sec, mask; import gc; gc.collect()
    # propagation across y by ridge tracking along the local normal (A3), on a region of interest around the reference curve
    for y in order[1:]:
        ref = res[y - 32] if (y > y0 and (y - 32) in res) else res.get(y + 32) if y < y0 else None
        if ref is None or ref.get('status') != 'ok': res[y] = {'status': 'no reference'}; continue
        C = ref['curve']; ok = np.isfinite(C[:, 0])
        if ok.sum() < 10: res[y] = {'status': 'reference empty'}; continue
        zlo, zhi = int(np.nanmin(C[:, 0])) - 64, int(np.nanmax(C[:, 0])) + 65; xlo, xhi = int(np.nanmin(C[:, 1])) - 64, int(np.nanmax(C[:, 1])) + 65
        zlo, xlo = max(0, zlo), max(0, xlo); sec = np.asarray(secs[y])[zlo:zhi, xlo:xhi]; mask = sec > 0
        if mask.sum() < 100: res[y] = {'status': 'no mask'}; continue
        Rs, FZ, FX, coh, void, tau = sheet_fields(sec, mask); Zr, Xr = Rs.shape; Cn = np.full_like(C, np.nan); steps = []
        for q in np.nonzero(ok)[0]:
            z, x = C[q, 0] - zlo, C[q, 1] - xlo; zi, xi = int(round(z)), int(round(x))
            if not (0 <= zi < Zr and 0 <= xi < Xr): continue
            n0, n1 = float(FZ[zi, xi]), float(FX[zi, xi]); best, bz, bx = 0.5 * tau, None, None
            for o in range(-8, 9):
                zz_, xx_ = int(round(z + o * n0)), int(round(x + o * n1))
                if 0 <= zz_ < Zr and 0 <= xx_ < Xr and not void[zz_, xx_] and Rs[zz_, xx_] > best: best, bz, bx = Rs[zz_, xx_], zz_, xx_
            if bz is not None: Cn[q] = (bz + zlo, bx + xlo); steps.append(float(np.hypot(bz - z, bx - x)))
        tf_ = float(np.isfinite(Cn[:, 0]).mean()); res[y] = {'status': 'ok' if tf_ > 0 else 'lost', 'curve': Cn, 'tracked_frac': round(tf_, 3), 'step_med': round(float(np.median(steps)), 2) if steps else None, 'seam_ok_frac': round(float(np.mean(np.array(steps) <= 8)), 3) if steps else None, 'umin': float(U[np.isfinite(Cn[:, 0])].min()) if tf_ > 0 else None, 'umax': float(U[np.isfinite(Cn[:, 0])].max()) if tf_ > 0 else None}
        if pred is not None and y in pred and tf_ > 0:
            pm = np.unpackbits(pred[y], axis=1); fin = np.isfinite(Cn[:, 0]); pz = np.clip(np.rint(Cn[fin, 0]).astype(int), 0, pm.shape[0] - 1); px = np.clip(np.rint(Cn[fin, 1]).astype(int) + (x0 - 544), 0, pm.shape[1] - 1); res[y]['pred_frac'] = float(ndi.maximum_filter(pm, 5)[pz, px].mean())
        print(y, 'tracked', res[y]['tracked_frac'], 'step med', res[y]['step_med'], 'pred', None if res[y].get('pred_frac') is None else round(res[y]['pred_frac'], 2), flush=True)
        del Rs, FZ, FX, coh, void, sec, mask; gc.collect()
    for y in res:
        if res[y].get('status') == 'ok': res[y]['poly'] = res[y]['curve'] + np.array([z0, x0], np.float32); res[y]['u'] = U
    seed_rec = res[y0]; umin, umax = seed_rec['umin'], seed_rec['umax']; Zs = np.full((len(ys), len(U)), np.nan, np.float32); Xs = np.full_like(Zs, np.nan)
    for i, y in enumerate(ys):
        r = res.get(y, {})
        if r.get('status') != 'ok': continue
        Zs[i] = r['poly'][:, 0]; Xs[i] = r['poly'][:, 1]
    ok = [y for y in ys if res.get(y, {}).get('status') == 'ok']; cov = [float(np.isfinite(Zs[i]).mean()) for i in range(len(ys))]
    G1 = (umax - umin) / mm; G2 = float(np.mean([c >= 0.9 for c in cov])); seams = [res[y]['seam_ok_frac'] for y in ok if res[y].get('seam_ok_frac') is not None]; G3 = float(np.mean([s >= 0.95 for s in seams])) if seams else None
    checks = {'G1_seed_trace_mm': round(G1, 2), 'G1_pass': G1 >= 20, 'G2_coverage_frac': round(G2, 3), 'G2_pass': G2 >= 0.9, 'G3_seam_frac_sections_ge95': G3, 'G3_pass': (G3 is not None and G3 >= 0.95), 'seam_ok_frac_per_section': {y: res[y].get('seam_ok_frac') for y in ok}, 'tracked_frac_per_section': {y: res[y].get('tracked_frac') for y in ok},
              'coverage_per_section': dict(zip(map(str, ys), [round(c, 3) for c in cov])), 'n_sections': len(ys), 'n_traced': len(ok), 'seed_l0': seed_rec['seed'], 'seed_candidates': cand_lengths_mm, 'seed_trace': {k: res[y0].get(k) for k in ['anchored_frac', 'jumps', 'stops', 'extent_mm', 'n', 'pred_frac']}, 'pred_frac_per_section': {y: res[y].get('pred_frac') for y in ok}, 'status_per_section': {y: res.get(y, {}).get('status') for y in ys}, 'bbox': [int(z0), int(z1), int(x0), int(x1)], 'secs': round(time.time() - t0)}
    np.savez_compressed(os.path.join(out, 'surface.npz'), Z=Zs, X=Xs, U=U.astype(np.float32), ys=np.array(ys)); json.dump(checks, open(os.path.join(out, 'trace_checks.json'), 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o)); print(json.dumps({k: checks[k] for k in checks if 'per_section' not in k}, default=lambda o: o.item() if hasattr(o, 'item') else str(o)), flush=True)
    # tifxyz (8-vox u cells, dy rows) for the mesh checks: x.tif y.tif z.tif in level-0 voxel coords, -1 invalid
    import tifffile; d = os.path.join(out, 'surface_tifxyz'); os.makedirs(d, exist_ok=True); cells = np.arange(0, len(U), 2)
    Xg = np.where(np.isfinite(Xs[:, cells]), Xs[:, cells], -1).astype(np.float32); Zg = np.where(np.isfinite(Zs[:, cells]), Zs[:, cells], -1).astype(np.float32); Yg = np.where(np.isfinite(Zs[:, cells]), np.array(ys, np.float32)[:, None], -1).astype(np.float32)
    tifffile.imwrite(os.path.join(d, 'x.tif'), Xg, metadata=None, software=False); tifffile.imwrite(os.path.join(d, 'y.tif'), Yg, metadata=None, software=False); tifffile.imwrite(os.path.join(d, 'z.tif'), Zg, metadata=None, software=False); json.dump({'scale': [1 / 8.0, 1 / cfg['band']['dy']], 'frame': 'level-0 voxels (x, y, z)', 'declaration': cfg['declaration']}, open(os.path.join(d, 'meta.json'), 'w'))

def stage_render(cfg, out, a):
    t0 = time.time(); S = np.load(os.path.join(out, 'surface.npz')); Zs, Xs, U, ys = S['Z'], S['X'], S['U'], S['ys']; ys_all = np.arange(ys.min(), ys.max() + 1); OFF = np.arange(-8, 9)
    if len(U) > 1 and (U[1] - U[0]) > 1:                                                                     # native sampling along u (1 vox): linear between tracked samples, gaps stay gaps
        Uf = np.arange(U.min(), U.max() + 1, 1.0); Zf_, Xf_ = np.full((len(ys), len(Uf)), np.nan, np.float32), np.full((len(ys), len(Uf)), np.nan, np.float32)
        for i in range(len(ys)):
            ok = np.isfinite(Zs[i])
            if ok.sum() < 2: continue
            Zf_[i] = np.interp(Uf, U[ok], Zs[i][ok]); Xf_[i] = np.interp(Uf, U[ok], Xs[i][ok]); gap = np.interp(Uf, U, (~ok).astype(float)) > 0; Zf_[i][gap] = np.nan; Xf_[i][gap] = np.nan
        Zs, Xs, U = Zf_, Xf_, Uf
    ct = Zarr0(cfg['ct_l0'], a.threads); T = np.zeros((len(OFF), len(ys_all), len(U)), np.uint8)
    # in-section tangent/normal per traced section, then linear in y between sections
    def interp_rows(A):
        out_ = np.full((len(ys_all), A.shape[1]), np.nan, np.float32)
        for j in range(A.shape[1]):
            col = A[:, j]; ok = np.isfinite(col)
            if ok.sum() >= 2: out_[:, j] = np.interp(ys_all, ys[ok], col[ok], left=np.nan, right=np.nan)
            elif ok.sum() == 1: out_[np.abs(ys_all - ys[ok][0]) <= cfg['band']['dy'] // 2, j] = col[ok][0]
        return out_
    Zf, Xf = interp_rows(Zs), interp_rows(Xs); valid = np.isfinite(Zf) & np.isfinite(Xf)
    tz = np.gradient(np.nan_to_num(Zf), axis=1); tx = np.gradient(np.nan_to_num(Xf), axis=1); nrm = np.hypot(tz, tx) + 1e-6; NZ, NX = -tx / nrm, tz / nrm       # in-section normal
    cz, cy, cx = ct.chunks
    for yr0 in range(int(ys_all.min()) // cy * cy, int(ys_all.max()) + 1, cy):                                            # one CT chunk row at a time, x strips of 1024
        yr1 = yr0 + cy; rows = (ys_all >= yr0) & (ys_all < yr1)
        if not rows.any(): continue
        for xs0 in range(0, ct.shape[2], 1024):
            sel = rows[:, None] & valid & (Xf >= xs0) & (Xf < xs0 + 1024)
            if not sel.any(): continue
            iy, iu = np.nonzero(sel); zc_ = Zf[iy, iu]; xc_ = Xf[iy, iu]; nzz, nxx = NZ[iy, iu], NX[iy, iu]
            zq = zc_[None, :] + OFF[:, None] * nzz[None, :]; xq = xc_[None, :] + OFF[:, None] * nxx[None, :]; yq = np.broadcast_to(ys_all[iy][None, :], zq.shape).astype(np.float32)
            bz0, bz1 = max(0, int(zq.min()) - 2), min(ct.shape[0], int(zq.max()) + 3); bx0, bx1 = max(0, int(xq.min()) - 2), min(ct.shape[2], int(xq.max()) + 3); by0, by1 = int(yq.min()), int(yq.max()) + 1
            blk = ct.block(bz0, bz1, by0, by1, bx0, bx1)
            v = ndi.map_coordinates(blk, [zq - bz0, yq - by0, xq - bx0], order=1, mode='nearest'); T[:, iy, iu] = np.clip(v, 0, 255).astype(np.uint8); del blk
        print('rows', yr0, round(time.time() - t0), 's', flush=True)
    np.savez_compressed(os.path.join(out, 'render.npz'), T=T, OFF=OFF, ys=ys_all, U=U); c = T[8]
    from PIL import Image; Image.fromarray(c).save(os.path.join(out, 'centre.png'))
    # G5 ridge profile and fibre metrics on the centre layer
    v = valid; prof_ok = ((c.astype(np.int16) > T[2].astype(np.int16)) & (c.astype(np.int16) > T[14].astype(np.int16)))[v]; G5 = float(prof_ok.mean()) if v.any() else None
    cf = c.astype(np.float32) / 255.0; th, coh, _ = st_eigen(st_accumulate([cf], 1.0), 4.0); coh_med = float(np.median(coh[v])) if v.any() else None
    ang = th[v]; # orientation consistency across y: circular std of the doubled angle per u column over the band
    ok_cols = []
    for j in range(0, len(U), 64):
        col = th[:, j][valid[:, j]]
        if len(col) < 10: continue
        Rbar = np.abs(np.mean(np.exp(2j * col))); cstd = np.sqrt(-2 * np.log(max(Rbar, 1e-9))) / 2; ok_cols.append(np.rad2deg(cstd) <= 20)
    fib = {'coherence_median': None if coh_med is None else round(coh_med, 3), 'coherence_pass': (coh_med is not None and coh_med >= 0.30), 'orientation_consistent_frac': (round(float(np.mean(ok_cols)), 3) if ok_cols else None), 'orientation_pass': (bool(ok_cols) and float(np.mean(ok_cols)) >= 0.8)}
    json.dump({'G5_ridge_frac': None if G5 is None else round(G5, 3), 'G5_pass': (G5 is not None and G5 >= 0.9), 'fibre': fib, 'texture_shape_layers_y_u': list(T.shape), 'valid_frac': round(float(v.mean()), 3), 'secs': round(time.time() - t0)}, open(os.path.join(out, 'render_checks.json'), 'w'), indent=1); print('render done', T.shape, 'G5', G5, 'fibre', fib, flush=True)

def stage_ink(cfg, out, a):
    import torch; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from master import Master
    t0 = time.time(); R = np.load(os.path.join(out, 'render.npz')); T = R['T']; stack = T[:16].astype(np.float32) / 255.0      # offsets -8..+7
    ck = torch.load(cfg['ink_model'], map_location='cpu'); m = Master(ssl_encoder=None, base=ck.get('base', 16), ssl_dim=192); m.load_state_dict(ck['model']); m.eval(); torch.set_num_threads(max(1, os.cpu_count() or 4))
    Y, U = stack.shape[1:]; win = np.outer(np.hanning(66)[1:-1], np.hanning(66)[1:-1]).astype(np.float32) + 1e-3; valid = T[8] > 0
    def run(st):
        acc = np.zeros((Y, U), np.float32); wt = np.zeros_like(acc); crops = []; pos = []
        ys_ = list(range(0, max(1, Y - 64 + 1), 32)) + ([Y - 64] if Y >= 64 else []); xs_ = list(range(0, max(1, U - 64 + 1), 32)) + ([U - 64] if U >= 64 else [])
        def flush():
            x = torch.from_numpy(np.stack(crops)).unsqueeze(1)
            with torch.no_grad(): p_ = torch.sigmoid(m(x)).numpy()[:, 0]
            for (yy, xx), pm in zip(pos, p_): acc[yy:yy + 64, xx:xx + 64] += pm * win; wt[yy:yy + 64, xx:xx + 64] += win
            crops.clear(); pos.clear()
        for yy in ys_:
            for xx in xs_:
                c = st[:, yy:yy + 64, xx:xx + 64]
                if c.shape[1] != 64 or c.shape[2] != 64 or (valid[yy:yy + 64, xx:xx + 64].mean() < 0.2): continue
                crops.append(c); pos.append((yy, xx))
                if len(crops) == 16: flush()
        if crops: flush()
        return np.where(wt > 0, acc / np.maximum(wt, 1e-6), 0).astype(np.float32)
    pf = run(stack); pr = run(stack[::-1].copy()); pf[~valid] = 0; pr[~valid] = 0
    from PIL import Image; Image.fromarray((pf * 255).astype(np.uint8)).save(os.path.join(out, 'ink_fwd.png')); Image.fromarray((pr * 255).astype(np.uint8)).save(os.path.join(out, 'ink_rev.png'))
    np.savez_compressed(os.path.join(out, 'ink.npz'), fwd=pf, rev=pr)
    # forward/reverse agreement at 0.5 mm smoothing vs rotation controls
    s = 0.5 * 1000 / cfg['vox_um']; A = ndi.gaussian_filter(pf, s); B = ndi.gaussian_filter(pr, s); v = valid & (A > 0) & (B > 0)
    r = float(np.corrcoef(A[v], B[v])[0, 1]) if v.sum() > 100 else None; ctrl = [float(np.corrcoef(A[v], np.rot90(B, 2)[v])[0, 1]), float(np.corrcoef(A[v], B[:, ::-1][v])[0, 1])] if v.sum() > 100 else None
    json.dump({'fwd_rev_pearson_0p5mm': None if r is None else round(r, 3), 'controls_rot180_flip': None if ctrl is None else [round(c, 3) for c in ctrl], 'frac_gt_thr_fwd': round(float((pf[valid] > cfg['gold_threshold']).mean()), 4), 'frac_gt_thr_rev': round(float((pr[valid] > cfg['gold_threshold']).mean()), 4), 'model': cfg['ink_model'], 'heldout': cfg['ink_model_heldout'], 'secs': round(time.time() - t0)}, open(os.path.join(out, 'ink_checks.json'), 'w'), indent=1); print('ink done', round(time.time() - t0), 's; agreement', r, flush=True)

def stage_gold(cfg, out, a):
    from PIL import Image; R = np.load(os.path.join(out, 'render.npz')); c = R['T'][8]; P = np.load(os.path.join(out, 'ink.npz'))['fwd']; thr = cfg['gold_threshold']
    rgb = np.repeat(c[:, :, None], 3, 2).astype(np.float32); g = P > thr; gold = np.array([255, 196, 0], np.float32); al = 0.75
    rgb[g] = (1 - al) * rgb[g] + al * gold; img = Image.fromarray(rgb.astype(np.uint8)); img.save(os.path.join(out, 'gold.png')); img.resize((max(1, img.width // 4), max(1, img.height // 4))).save(os.path.join(out, 'gold_preview.png'))
    ch = {}
    for f in ['trace_checks.json', 'render_checks.json', 'ink_checks.json', 'mesh_checks.json', 'umbilicus_checks.json', 'frame.json']:
        fp = os.path.join(out, f)
        if os.path.isdir(fp): fp = os.path.join(fp, f)                                                   # mesh_checks.py writes a directory
        if os.path.exists(fp):
            try: ch[f.replace('.json', '')] = json.load(open(fp))
            except Exception as e: ch[f.replace('.json', '')] = {'error': str(e)}
    ch['gold'] = {'threshold': thr, 'frac_gold_of_valid': round(float(g[c > 0].mean()), 4), 'pixels_gold': int(g.sum()), 'statement': 'model output of the DECL-FL-7 master model (held-out AUC below the declared bar): not validated ink; no letter claimed'}
    ch['declaration'] = cfg['declaration']; json.dump(ch, open(os.path.join(out, 'checks.json'), 'w'), indent=1); print('gold done:', ch['gold'])

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('stage'); ap.add_argument('config'); ap.add_argument('out'); ap.add_argument('--ct_l4', default='/dev/shm/e2e/ct_L4.npy'); ap.add_argument('--threads', type=int, default=32)
    a = ap.parse_args(); cfg = json.load(open(a.config)); os.makedirs(a.out, exist_ok=True)
    {'trace': stage_trace, 'render': stage_render, 'ink': stage_ink, 'gold': stage_gold}[a.stage](cfg, a.out, a)
