# Provenance: Project HERCULES | owner the owner | [id removed]
"""DEV registry builder (task devloop; RULES.md DECL-DEVLOOP item "DEV data"). Numbers only; no image is written,
opened or displayed. Reference maps are read as arrays for window statistics only.

Rules (fixed in this file before it was first run; the run record stores this file's sha256):
R1 Material. PHerc0139 clean controls w024, w047, w053 (D0-SETTLED item 3; title strip < 2 cm tall, unused);
   PHerc0814 segments >= 184 vox from base-trained 46527 with >= 10 cm^2 (RCBANK-1). Never PHerc0841 or an
   eligible scroll. PHerc0009B (MAY protocol) is added later from the reg0009b sibling's registration.
R2 Sampling. Canvas samples at stride 4 px of the organizer 9 um canvas (pixel P samples grid (P + 0.5) s), 3-D
   point = bilinear over the 4 quad corners (all valid).
R3 Base-training papyrus. A sample is same-papyrus with a base-training trace if a point of that trace (mesh
   densified to <= 4 vox spacing) lies within 6 vox (3-D) AND within 2 vox along that point's normal
   (DECL-READCAL-A2 rule (a)); such samples plus a 64 px in-plane halo are EXCLUDED (masked from every metric).
   Base-training traces: 0139 w028, w029, w030, w035, w039, w040, w041, w043, w044, w045 and re-trace w046 (the
   mesh-only w030 trace has no 9 um mesh; its 9 um twin w030 is used; w028 added from the official ink_9um
   aligned label list in data/catalogue/checkpoints.json, whose w016 and w017 have no segment on S3 and cannot
   be certified); 0814 46527 and every 0814 segment that is same-papyrus with it on >= 1000 vox^2.
   Rule v3 adds: every sample < 16 vox (3-D) from any point of a base-training trace is EXCLUDED as well (the
   +-15 vox -n 31 training render slab; the same 16 vox as the pairs0139 rule S), because v2 left a w047 window
   with a sample 2.6 vox from a base-trained trace that the strict same-papyrus test does not flag.
   Certificate: for every chosen window, the same-papyrus area with EVERY other trace of its scroll is listed.
R4 Used windows (rule v2). Every window that any earlier record names on PHerc0139 (D1 blanks and J-seal blank
   candidates, D1 canary, HANDED/PROBE/C3 windows; taken as 2136 px squares from their stated corner, conservative
   for smaller windows). A sample is FORBIDDEN (a window touching one is rejected) if (a) it lies inside a used
   window's footprint on the same segment, or is same-papyrus (R3 test) with a used window on another segment;
   or (b) it lies < 144 vox (3-D) from the still-live w053 blank windows of D1/D3 (y256 x1536, y256 x7168) or the
   J-seal blank candidates (y256 x1280, y512 x7168).
   Rule v1 (144 vox from EVERY used window) was run first and stopped: adjacent windings lie 20-40 vox apart, so
   it forbade 32 / 88 / 49 % of w024 / w047 / w053 and left 3 eligible 0139 windows (runs.jsonl registry_v1).
R5 Windows (rule v2). 2136 x 2136 px (2.0 cm at 9.362 um) on a 256 px grid of the organizer 9 um canvas.
   coverage = fraction of samples that are mesh-valid, inside the reference map and not excluded. TEXT: coverage
   >= 0.90 (0139) or >= 0.75 (0814; RCBANK-1 found no 0814 window >= 0.90), reference ink fraction (sub-samples
   >= 150 among covered) in [0.03, 0.30], no forbidden sample; taken in the order of a seeded permutation
   (numpy default_rng(20260925), eligible list sorted by segment, y0, x0), greedy, no 2-D overlap with a chosen
   window, <= 2 per segment, <= 4 per scroll. Rule v1 ranked by ink fraction (no upper bound) and so preferred
   saturated reference regions (w024 segment ink fraction 0.377 vs 0.10 / 0.03 on w047 / w053; 0841 organizer
   segments 0.11-0.14, logs/bank0841/summary.json); v2 bounds the fraction and draws by seed instead of ranking.
   Rule v3 adds: a text window that is same-papyrus (R3 test, >= 1000 vox^2)
   with an already chosen DEV window is skipped (v2 chose 0814 windows on 204843 and 165636, which re-trace the
   same papyrus, 5.0e6 vox^2). BLANK (rule v3): 1068 x 1068 px (1.0 cm) windows on the same 256 px grid (no
   2 cm window below 1 % reference ink survives R4 on any DEV segment), coverage >= 0.90, ink fraction < 0.01, no
   forbidden sample, no 2-D overlap with and not same-papyrus with a chosen window; ranked by ink fraction
   ascending then coverage descending; <= 2 per scroll, <= 1 per segment.
R6 Hold-out (0814 "per-arm hold-out"). Every other 0814 segment that is same-papyrus (R3 test) with a chosen
   0814 DEV window on >= 1000 vox^2 is listed; a recipe evaluated on DEV must not train on those segments nor on
   the DEV segments themselves (+ 16 vox, as pairs0139 rule S).
Output: logs/sib/devloop/dev_registry.json (+ per-segment stats npz under /work/devloop/registry).
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import sys
import time

import cv2
import numpy as np
import tifffile
import zarr
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'src'))
sys.path.insert(0, HERE)
from hercules.geometry.tifxyz import read_tifxyz, valid_mask  # noqa: E402
from hercules.pipeline.window import voxel_size_from_metadata  # noqa: E402
import devlib as D  # noqa: E402

S3 = '/work/devloop/s3'
OUT = '/work/devloop/registry'
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
STRIDE = 4
WIN = 2136
GRID = 256
VOL9 = {'PHerc0139': '20250728140407-9.362um-1.2m-113keV-masked.zarr',
        'PHerc0814': '20250804134230-9.362um-1.2m-113keV-masked.zarr'}
VOL2 = {'PHerc0139': '20260102150214-2.399um-0.2m-78keV-masked.zarr',
        'PHerc0814': '20260309142202-2.399um-0.2m-78keV-masked.zarr'}
DEV_SEGS = {'PHerc0139': ['w024', 'w047', 'w053'],
            'PHerc0814': ['204843', '165636', '060526', '222237', '212701']}
BASE_0139 = ['w028', 'w029', 'w030', 'w035', 'w039', 'w040', 'w041', 'w043', 'w044', 'w045', 'w046']
BASE_0814 = ['46527']
COV_TEXT = {'PHerc0139': 0.90, 'PHerc0814': 0.75}
INK_TEXT, INK_TEXT_MAX, INK_BLANK, COV_BLANK = 0.03, 0.30, 0.01, 0.90
SEED = 20260925
LIVE_BLANKS = [('w053', 256, 1536), ('w053', 256, 7168), ('w053', 256, 1280), ('w053', 512, 7168)]
MAX_PER_SEG, MAX_TEXT, MAX_BLANK = 2, 4, 2
WIN_BLANK = 1068
SLAB_VOX = 16.0
SAMEPAP_D, SAMEPAP_DN, HALO_PX, CLEAR_VOX = 6.0, 2.0, 64, 144.0


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def seg_dirs(scroll):
    return sorted(os.listdir(f'{S3}/{scroll}/segments'))


def short_id(sid):
    """w024 / title / 46527 for named traces; the last 6 digits of the timestamp for auto-grown 0814 traces."""
    tail = sid.split('-', 1)[1]
    if tail.startswith(('w0', 'title')) or tail[:1].isdigit():
        return tail.split('_')[0]
    return sid.split('-')[0][8:14]


def find_seg(scroll, short):
    c = [s for s in seg_dirs(scroll) if short_id(s) == short and os.path.isdir(mesh9_path(scroll, s))]
    assert len(c) == 1, (scroll, short, c)
    return c[0]


def mesh9_path(scroll, sid):
    ts = sid.split('-')[0]
    vid = VOL9[scroll].split('-')[0]
    return f'{S3}/{scroll}/segments/{sid}/mesh/{ts}-on-{vid}-9.362um.tifxyz'


def load_mesh(scroll, sid):
    m = read_tifxyz(mesh9_path(scroll, sid))
    return m


def samples(points, scale, stride=STRIDE, window=None):
    """3-D points of canvas pixels P = stride*i + (stride-1)/2 (centre of each stride block); grid g = (P+0.5) s.
    Returns pts (h, w, 3) float64 with NaN where a quad corner is invalid, and the canvas shape."""
    p = np.asarray(points, np.float64).copy()
    ok = valid_mask(p)
    p[~ok] = np.nan
    H, W = ok.shape
    s = float(np.float32(scale[0]))
    Hc, Wc = int(round(H / s)), int(round(W / s))
    if window is None:
        y0, x0, h, w = 0, 0, Hc, Wc
    else:
        y0, x0, h, w = window
    rows = y0 + np.arange(0, h, stride) + (stride - 1) / 2.0
    cols = x0 + np.arange(0, w, stride) + (stride - 1) / 2.0
    gv = (rows + 0.5) * s
    gu = (cols + 0.5) * s
    v0 = np.clip(np.floor(gv).astype(int), 0, H - 2)
    u0 = np.clip(np.floor(gu).astype(int), 0, W - 2)
    fv = (gv - v0)[:, None, None]
    fu = (gu - u0)[None, :, None]
    V0, U0 = np.meshgrid(v0, u0, indexing='ij')
    out = ((p[V0, U0] * (1 - fu) + p[V0, U0 + 1] * fu) * (1 - fv)
           + (p[V0 + 1, U0] * (1 - fu) + p[V0 + 1, U0 + 1] * fu) * fv)
    outside = (gv < 0) | (gv > H - 1)
    out[outside] = np.nan
    out[:, (gu < 0) | (gu > W - 1)] = np.nan
    return out, (Hc, Wc)


def dense_with_normals(points, k=5):
    """Vertices densified k x per quad (bilinear, all 4 corners valid; spacing = grid step / k) with per-quad
    unit normals (du x dv)."""
    p = np.asarray(points, np.float64)
    ok = valid_mask(p)
    q = ok[:-1, :-1] & ok[:-1, 1:] & ok[1:, :-1] & ok[1:, 1:]
    iv, iu = np.nonzero(q)
    a, b, c, d = p[iv, iu], p[iv, iu + 1], p[iv + 1, iu], p[iv + 1, iu + 1]
    du = 0.5 * ((b - a) + (d - c))
    dv = 0.5 * ((c - a) + (d - b))
    n = np.cross(du, dv)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    t = (np.arange(k) + 0.5) / k
    pts, nrm = [], []
    for ty in t:
        for tx in t:
            pts.append((a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty)
            nrm.append(n)
    return np.concatenate(pts), np.concatenate(nrm)


def samepap_mask(sp, tree, nrm, dpts):
    """Boolean (h, w): sample within SAMEPAP_D (3-D) and SAMEPAP_DN along the normal of a dense trace point."""
    flat = sp.reshape(-1, 3)
    good = np.isfinite(flat).all(1)
    res = np.zeros(flat.shape[0], bool)
    idx = np.nonzero(good)[0]
    if idx.size == 0:
        return res.reshape(sp.shape[:2])
    dd, ii = tree.query(flat[idx], k=8, distance_upper_bound=SAMEPAP_D, workers=3)
    for j in range(ii.shape[1]):
        m = np.isfinite(dd[:, j])
        if not m.any():
            continue
        q = ii[m, j]
        dn = np.abs(np.einsum('ij,ij->i', flat[idx[m]] - dpts[q], nrm[q]))
        res[idx[m][dn <= SAMEPAP_DN]] = True
    return res.reshape(sp.shape[:2])


def used_windows_0139():
    """Every window on PHerc0139 named in an earlier record (corner y, x on the organizer 9 um canvas)."""
    pat = re.compile(r'(w0\d\d)[_ ,:\-]*y(\d+)[_ ,:\-]*x(\d+)')
    found = {}
    for root, _, files in os.walk(os.path.join(REPO, 'logs')):
        if '/sib' in root or 'hrv1' in root:
            continue
        for fn in files:
            if not fn.endswith(('.json', '.tsv', '.jsonl')):
                continue
            t = open(os.path.join(root, fn), errors='ignore').read()
            for m in pat.finditer(t):
                key = (m.group(1), int(m.group(2)), int(m.group(3)))
                found.setdefault(key, set()).add(os.path.relpath(os.path.join(root, fn), REPO))
    return [dict(segment=k[0], y0=k[1], x0=k[2], size=WIN, sources=sorted(v)) for k, v in sorted(found.items())]


def box_mean(a, k):
    """Mean over every k x k box (top-left anchored), via an integral image; out[i, j] = mean(a[i:i+k, j:j+k])."""
    a = np.asarray(a, np.float64)
    ii = np.pad(a.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    return (ii[k:, k:] - ii[:-k, k:] - ii[k:, :-k] + ii[:-k, :-k]) / (k * k)


def box_any(a, k):
    return box_mean(a.astype(np.float64), k) > 0


def ink_stats(scroll, sid, shape9, ok_samples):
    """Reference statistics per stride block: fraction of 4 x 4 nearest sub-samples of the 2.4 um map that are
    >= 150 (ink) and inside the map. r = N2 / N9 per axis from the map shape (= the 2.4 um canvas)."""
    d = f'{S3}/{scroll}/segments/{sid}/ink-detection'
    f = [x for x in os.listdir(d) if x.endswith('.tif') and '2.399um' in x and '20260417190342' in x]
    assert len(f) == 1
    path = f'{d}/{f[0]}'
    ref = tifffile.imread(path)
    H2, W2 = ref.shape
    Hc, Wc = shape9
    r = (H2 / Hc, W2 / Wc)
    ink = (ref >= 150).astype(np.uint8)
    del ref
    h, w = ok_samples.shape
    acc = np.zeros((h, w), np.float32)
    ins = np.zeros((h, w), np.float32)
    offs = (np.arange(4) + 0.5) / 4 * STRIDE - 0.5  # sub-positions inside the stride block, in 9 um px
    rows = np.arange(h) * STRIDE
    cols = np.arange(w) * STRIDE
    for oy in offs:
        yy = D.c9_to_c2(rows + oy, r[0])
        for ox in offs:
            xx = D.c9_to_c2(cols + ox, r[1])
            iy, ix = np.rint(yy).astype(np.int64), np.rint(xx).astype(np.int64)  # nearest sample (separable)
            oky, okx = (iy >= 0) & (iy <= H2 - 1), (ix >= 0) & (ix <= W2 - 1)
            acc += ink[np.ix_(np.clip(iy, 0, H2 - 1), np.clip(ix, 0, W2 - 1))] * (oky[:, None] & okx[None, :])
            ins += oky[:, None] & okx[None, :]
    return acc / 16.0, ins / 16.0, r, path


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    rec = dict(provenance=PROV, generated_utc=utc(), task='devloop', serves='RULES.md DECL-DEVLOOP (DEV data)',
               viewing='no image was written, opened or displayed; numbers only',
               script=dict(path=os.path.relpath(__file__, REPO), sha256=sha256(__file__)),
               devlib_sha256=sha256(os.path.join(HERE, 'devlib.py')),
               rules=__doc__.split('Rules')[1].split('Output:')[0].strip(), scrolls={})
    used = used_windows_0139()
    rec['used_windows_0139'] = used
    for scroll in ['PHerc0139', 'PHerc0814']:
        vox9 = voxel_size_from_metadata(f'{S3}/{scroll}/volumes/{VOL9[scroll]}/metadata.json')
        vox2 = voxel_size_from_metadata(f'{S3}/{scroll}/volumes/{VOL2[scroll]}/metadata.json')
        srec = dict(voxel_um_9=vox9, voxel_um_2=vox2, vol9=VOL9[scroll], vol2=VOL2[scroll], segments={},
                    windows=[], blanks=[])
        # --- base-training traces (R3)
        all_ids = [s for s in seg_dirs(scroll) if os.path.isdir(mesh9_path(scroll, s))]
        base_short = BASE_0139 if scroll == 'PHerc0139' else BASE_0814
        base_ids = [find_seg(scroll, b) for b in base_short]
        meshes = {s: load_mesh(scroll, s) for s in all_ids}
        if scroll == 'PHerc0814':  # add every 0814 segment same-papyrus with 46527 on >= 1000 vox^2
            dp, dn = dense_with_normals(meshes[base_ids[0]].points)
            tr = cKDTree(dp)
            for s in all_ids:
                if s in base_ids:
                    continue
                sp, _ = samples(meshes[s].points, meshes[s].scale)
                area = float(samepap_mask(sp, tr, dn, dp).sum()) * STRIDE * STRIDE
                if area >= 1000:
                    base_ids.append(s)
            srec['base_retraces_found'] = [s for s in base_ids[1:]]
        srec['base_training_traces'] = base_ids
        dense = [dense_with_normals(meshes[b].points) for b in base_ids]
        bp = np.concatenate([d[0] for d in dense])
        bn = np.concatenate([d[1] for d in dense])
        btree = cKDTree(bp)
        # --- used windows (R4 v2): footprints, same-papyrus clouds, live-blank clearance clouds
        utree = None
        used_clouds = []
        live_pts = []
        if scroll == 'PHerc0139':
            for u in used:
                sid = find_seg(scroll, u['segment'])
                pts = meshes[sid].points
                q0, q1 = max(u['y0'] // 20 - 1, 0), (u['y0'] + WIN) // 20 + 2
                r0, r1 = max(u['x0'] // 20 - 1, 0), (u['x0'] + WIN) // 20 + 2
                dp, dn = dense_with_normals(pts[q0:q1, r0:r1])
                used_clouds.append((u, sid, dp, dn))
                if (u['segment'], u['y0'], u['x0']) in LIVE_BLANKS:
                    sp, _ = samples(pts, meshes[sid].scale, stride=8, window=(u['y0'], u['x0'], WIN, WIN))
                    sp = sp.reshape(-1, 3)
                    live_pts.append(sp[np.isfinite(sp).all(1)])
            utree = cKDTree(np.concatenate(live_pts))
            srec['used_windows_live_blanks'] = [list(x) for x in LIVE_BLANKS]
        # --- every other segment's dense cloud for the hold-out list (R6)
        cand = []
        bwins = []
        for short in DEV_SEGS[scroll]:
            sid = find_seg(scroll, short)
            m = meshes[sid]
            sp, shape9 = samples(m.points, m.scale)
            ok = np.isfinite(sp).all(-1)
            same = samepap_mask(sp, btree, bn, bp)
            halo = HALO_PX // STRIDE
            excl = ndimage.binary_dilation(same, structure=np.ones((2 * halo + 1, 2 * halo + 1), bool)) if same.any() \
                else same
            flat = sp.reshape(-1, 3)
            g = np.isfinite(flat).all(1)
            dbase = np.full(flat.shape[0], np.inf)
            dbase[g] = btree.query(flat[g], k=1, distance_upper_bound=SLAB_VOX + 1, workers=3)[0]
            slab = (dbase < SLAB_VOX).reshape(ok.shape)
            excl = excl | slab
            forb = np.zeros_like(ok)
            forb_detail = {}
            if utree is not None:
                flat = sp.reshape(-1, 3)
                g = np.isfinite(flat).all(1)
                dd = np.full(flat.shape[0], np.inf)
                dd[g] = utree.query(flat[g], k=1, distance_upper_bound=CLEAR_VOX + 50, workers=3)[0]
                live = (dd < CLEAR_VOX).reshape(ok.shape)
                forb |= live
                forb_detail['live_blank_clearance'] = int((live & ok).sum())
                rows_c = np.arange(ok.shape[0]) * STRIDE + (STRIDE - 1) / 2.0
                cols_c = np.arange(ok.shape[1]) * STRIDE + (STRIDE - 1) / 2.0
                for u, usid, dp, dn in used_clouds:
                    if usid == sid:
                        fp = np.zeros_like(ok)
                        ry_ = (rows_c >= u['y0']) & (rows_c < u['y0'] + WIN)
                        rx_ = (cols_c >= u['x0']) & (cols_c < u['x0'] + WIN)
                        fp[np.ix_(ry_, rx_)] = True
                    else:
                        if dp.size == 0:
                            continue
                        lo, hi = dp.min(0) - 10, dp.max(0) + 10
                        inb = np.all((sp >= lo) & (sp <= hi), axis=-1)
                        if not inb.any():
                            continue
                        fp = np.zeros_like(ok)
                        sub = np.where(inb[..., None], sp, np.nan)
                        fp = samepap_mask(sub, cKDTree(dp), dn, dp)
                    n = int((fp & ok).sum())
                    if n:
                        forb_detail[f"{u['segment']}_y{u['y0']}_x{u['x0']}"] = n
                    forb |= fp
            inkf, inside, r, refpath = ink_stats(scroll, sid, shape9, ok)
            cover = ok & (inside >= 1.0) & ~excl
            np.savez_compressed(f'{OUT}/{scroll}_{short}.npz', ok=ok, same=same, slab=slab, excl=excl, forb=forb,
                                inkf=inkf, inside=inside)
            k = WIN // STRIDE
            covm = box_mean(cover, k)
            inkm = box_mean(inkf * cover, k) / np.maximum(covm, 1e-9)
            forbm = box_any(forb, k)
            exclm = box_mean(excl & ok, k)
            step = GRID // STRIDE
            wins = []
            for i in range(0, covm.shape[0], step):
                for j in range(0, covm.shape[1], step):
                    wins.append(dict(segment=short, segment_id=sid, y0=i * STRIDE, x0=j * STRIDE, h=WIN, w=WIN,
                                     coverage=round(float(covm[i, j]), 4), ink_frac=round(float(inkm[i, j]), 4),
                                     excluded_frac=round(float(exclm[i, j]), 4), forbidden=bool(forbm[i, j])))
            srec['segments'][short] = dict(
                segment_id=sid, mesh9=os.path.relpath(mesh9_path(scroll, sid), S3),
                mesh9_sha256={b: sha256(f'{mesh9_path(scroll, sid)}/{b}') for b in ('x.tif', 'y.tif', 'z.tif',
                                                                                   'meta.json')},
                ref_map=os.path.relpath(refpath, S3), ref_map_sha256=sha256(refpath),
                canvas9=list(shape9), r_yx=[float(r[0]), float(r[1])],
                samepap_cm2=round(float(same.sum()) * (STRIDE * vox9 / 1e4) ** 2, 4),
                slab16_cm2=round(float((slab & ok).sum()) * (STRIDE * vox9 / 1e4) ** 2, 4),
                excluded_cm2=round(float((excl & ok).sum()) * (STRIDE * vox9 / 1e4) ** 2, 4),
                forbidden_cm2=round(float((forb & ok).sum()) * (STRIDE * vox9 / 1e4) ** 2, 4),
                forbidden_samples_by_source=forb_detail,
                valid_cm2=round(float(ok.sum()) * (STRIDE * vox9 / 1e4) ** 2, 4),
                n_grid_windows=len(wins))
            kb = WIN_BLANK // STRIDE
            covb = box_mean(cover, kb)
            inkb = box_mean(inkf * cover, kb) / np.maximum(covb, 1e-9)
            forbb = box_any(forb, kb)
            exclb = box_mean(excl & ok, kb)
            for i in range(0, covb.shape[0], step):
                for j in range(0, covb.shape[1], step):
                    bwins.append(dict(segment=short, segment_id=sid, y0=i * STRIDE, x0=j * STRIDE, h=WIN_BLANK,
                                      w=WIN_BLANK, coverage=round(float(covb[i, j]), 4),
                                      ink_frac=round(float(inkb[i, j]), 4), excluded_frac=round(float(exclb[i, j]), 4),
                                      forbidden=bool(forbb[i, j])))
            cand += wins
        # --- selection (R5)
        def overlaps(a, b):
            return (a['segment'] == b['segment'] and a['y0'] < b['y0'] + b['h'] and b['y0'] < a['y0'] + a['h']
                    and a['x0'] < b['x0'] + b['w'] and b['x0'] < a['x0'] + a['w'])

        cloud_cache = {}

        def win_cloud(w):
            key = (w['segment_id'], w['y0'], w['x0'], w['h'])
            if key not in cloud_cache:
                pts = meshes[w['segment_id']].points
                q0, q1 = max(w['y0'] // 20 - 1, 0), (w['y0'] + w['h']) // 20 + 2
                r0, r1 = max(w['x0'] // 20 - 1, 0), (w['x0'] + w['w']) // 20 + 2
                dp, dn = dense_with_normals(pts[q0:q1, r0:r1])
                cloud_cache[key] = (cKDTree(dp), dn, dp)
            return cloud_cache[key]

        def samepap_with(w, others):
            if not others:
                return 0.0
            m = meshes[w['segment_id']]
            sp, _ = samples(m.points, m.scale, window=(w['y0'], w['x0'], w['h'], w['w']))
            best = 0.0
            for c in others:
                if c['segment_id'] == w['segment_id']:
                    continue  # same trace: 2-D overlap rule applies
                tr, dn, dp = win_cloud(c)
                best = max(best, float(samepap_mask(sp, tr, dn, dp).sum()) * STRIDE * STRIDE)
            return best
        chosen = []
        skipped_samepap = []
        text = [w for w in cand if w['coverage'] >= COV_TEXT[scroll] and INK_TEXT <= w['ink_frac'] <= INK_TEXT_MAX
                and not w['forbidden']]
        text.sort(key=lambda w: (w['segment'], w['y0'], w['x0']))
        perm = np.random.default_rng(SEED).permutation(len(text))
        text = [text[i] for i in perm]
        for w in text:
            if len(chosen) >= MAX_TEXT:
                break
            if sum(c['segment'] == w['segment'] for c in chosen) >= MAX_PER_SEG:
                continue
            if any(overlaps(w, c) for c in chosen):
                continue
            a = samepap_with(w, chosen)
            if a >= 1000:
                skipped_samepap.append(dict(id=f"{w['segment']}_y{w['y0']}_x{w['x0']}", samepap_vox2=a))
                continue
            chosen.append(dict(w, role='text'))
        blanks = [w for w in bwins if w['coverage'] >= COV_BLANK and w['ink_frac'] < INK_BLANK and not w['forbidden']]
        blanks.sort(key=lambda w: (w['ink_frac'], -w['coverage'], w['segment'], w['y0'], w['x0']))
        bl = []
        for w in blanks:
            if len(bl) >= MAX_BLANK:
                break
            if any(c['segment'] == w['segment'] for c in bl):
                continue
            if any(overlaps(w, c) for c in chosen + bl):
                continue
            if samepap_with(w, chosen + bl) >= 1000:
                continue
            bl.append(dict(w, role='blank'))
        srec['text_skipped_samepap'] = skipped_samepap
        srec['n_blank_grid_windows_1cm'] = len(bwins)
        srec['n_text_candidates'] = len(text)
        srec['candidate_counts'] = dict(
            grid_windows=len(cand), cov_ok=sum(w['coverage'] >= COV_TEXT[scroll] for w in cand),
            cov_ok_not_forbidden=sum(w['coverage'] >= COV_TEXT[scroll] and not w['forbidden'] for w in cand),
            ink_quantiles_cov_ok_not_forbidden=[round(float(q), 4) for q in np.quantile(
                [w['ink_frac'] for w in cand if w['coverage'] >= COV_TEXT[scroll] and not w['forbidden']] or [np.nan],
                [0, .1, .25, .5, .75, .9, 1])])
        np.savez_compressed(f'{OUT}/{scroll}_grid_windows.npz', **{k: np.array([w[k] for w in cand]) for k in
                            ('segment', 'y0', 'x0', 'coverage', 'ink_frac', 'excluded_frac', 'forbidden')})
        srec['n_blank_candidates'] = len(blanks)
        srec['windows'] = chosen
        srec['blanks'] = bl
        # --- certificates: min 3-D distance of each chosen window to used windows and base-training traces
        for w in chosen + bl:
            m = meshes[w['segment_id']]
            sp, _ = samples(m.points, m.scale, stride=2, window=(w['y0'], w['x0'], w['h'], w['w']))
            flat = sp.reshape(-1, 3)
            flat = flat[np.isfinite(flat).all(1)]
            w['cert_min_dist_live_blanks_vox'] = (round(float(utree.query(flat, k=1)[0].min()), 2)
                                          if utree is not None else None)
            w['cert_min_dist_base_vox'] = round(float(btree.query(flat, k=1)[0].min()), 2)
            sp4, _ = samples(m.points, m.scale, window=(w['y0'], w['x0'], w['h'], w['w']))
            bbox_lo, bbox_hi = np.nanmin(flat, 0) - 10, np.nanmax(flat, 0) + 10
            sp_other = {}
            for s_id, mm in meshes.items():
                if s_id == w['segment_id']:
                    continue
                pv = mm.points[valid_mask(mm.points)]
                if pv.size == 0 or (pv.max(0) < bbox_lo).any() or (pv.min(0) > bbox_hi).any():
                    continue
                dp, dn = dense_with_normals(mm.points)
                a = float(samepap_mask(sp4, cKDTree(dp), dn, dp).sum()) * STRIDE * STRIDE
                if a > 0:
                    sp_other[s_id] = dict(samepap_vox2=a, base_training=s_id in base_ids)
            w['cert_samepap_other_traces'] = sp_other
            w['cert_samepap_base_vox2_before_exclusion'] = sum(
                v['samepap_vox2'] for v in sp_other.values() if v['base_training'])
            w['id'] = f"{scroll[5:]}_{w['segment']}_y{w['y0']}_x{w['x0']}"
        # --- hold-out list (R6)
        if scroll == 'PHerc0814':
            hold = {}
            dev_ids = sorted({w['segment_id'] for w in chosen + bl})
            for did in dev_ids:
                wins_d = [w for w in chosen + bl if w['segment_id'] == did]
                pts = []
                for w in wins_d:
                    sp, _ = samples(meshes[did].points, meshes[did].scale, window=(w['y0'], w['x0'], w['h'], w['w']))
                    pts.append(sp.reshape(-1, 3))
                sp = np.concatenate(pts)[:, None, :]
                for s in all_ids:
                    if s == did:
                        continue
                    dp, dn = dense_with_normals(meshes[s].points)
                    if dp.size == 0:
                        continue
                    area = float(samepap_mask(sp, cKDTree(dp), dn, dp).sum()) * STRIDE * STRIDE
                    if area >= 1000:
                        hold.setdefault(s, []).append(dict(dev_segment=did, samepap_vox2=area))
            srec['holdout_segments'] = dict(dev_segments=dev_ids, samepap_with_dev=hold,
                                            rule='a recipe evaluated on DEV never trains on these segments')
        rec['scrolls'][scroll] = srec
        print(scroll, 'text', [(w['id'], w['coverage'], w['ink_frac']) for w in chosen],
              'blank', [(w['id'], w['coverage'], w['ink_frac']) for w in bl], flush=True)
    rec['seconds'] = round(time.time() - t0, 1)
    out = os.path.join(REPO, 'logs/sib/devloop/dev_registry.json')
    txt = json.dumps(rec, indent=1) + '\n'
    assert txt.isascii()
    open(out, 'w').write(txt)
    print('wrote', out, hashlib.sha256(txt.encode()).hexdigest())


if __name__ == '__main__':
    main()
