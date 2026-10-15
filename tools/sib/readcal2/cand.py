# Provenance: Project HERCULES | owner the owner | [id removed]
"""READCAL-2 bank candidate search (task readcal2, item 2). Numbers only: no image is written, opened or viewed.

Stages (resumable; per-segment caches under /work/rc2/cand):
  ref     organizer 2.399 um reference map -> 9.362 um organizer canvas (geom.map_ref_to_canvas, the D1 J builder's
          declared per-axis affine c9 = (c2 + 10) N9/N2 - 10), stored as uint8-rounded npz + sha256.
  samples canvas samples at stride 4 px: xyz, mesh-valid, reference-covered, reference value.
  dist    per sample: point-to-surface (and nearest dense vertex) distance to every base-training trace, every
          earlier-used window surface, and the sealed D1 blank windows (0139 part of SEAL-J-D1).
  windows 2136 px windows on a 256 px grid: coverage, CORR-RETRACE-RULE same-papyrus tests (fail-closed (a) OR (b)),
          2-D overlap with used windows, sealed clearance lower bound; writes the candidate and blank lists.
Rules (declared in logs/sib/readcal2/REPORT.md before the lists were read):
  R1 candidate segments: tier E0 = clean controls w024, w047, w053; tier N = their non-base 3-D neighbours (pairs0139
     exclusion list minus base traces): w023 w025 w026 w037 w048 w049 w050 w051 w052 w054 w055 w056 w057; PHerc0814
     segments >= 184 vox from base-trained 46527 (RCBANK-1).
  R2 base-training traces (0139): w028 w029 w030 w035 w039 w040 w041 w043 w044 w045 w046 (official ink_9um aligned
     list + project list; w016/w017 have no S3 segment and cannot be certified: disclosed); 0814: 46527.
  R3 base exclusion: samples within 2 vox (point-to-surface) of a base trace, dilated by a 64 px halo, are excluded;
     a window that is SAME papyrus with any base trace by CORR-RETRACE-RULE (a) or (b) is rejected.
  R4 used windows (every earlier 0139 window in the records; 2136 px squares from the stated corner, conservative):
     a window is rejected if it overlaps one in 2-D on the same canvas or is SAME papyrus with it (CORR (a) or (b)).
  R5 sealed sets: point-to-surface lower bound >= 128 vox from the SEAL-J-D1 w053 blank windows (J1-J5 lie on
     PHerc0841, another scroll).
  R6 coverage = fraction of the window's samples that are mesh-valid, reference-covered and not base-excluded;
     TEXT candidate: coverage >= 0.90 (0139) or >= 0.75 (0814, ribbons; flagged); BLANK: coverage >= 0.90 and
     reference ink fraction (ref >= 150 among covered samples) < 0.01. Text candidates are NEVER ranked or filtered by
     ink; the list gives coverage only (feasibility), sorted by (segment, y0, x0).
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import sys
import time

import numpy as np
import tifffile
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'src'))
import geom as G  # noqa: E402
from hercules.geometry.tifxyz import read_tifxyz  # noqa: E402

PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
S3 = '/work/rc2/s3'
CACHE = '/work/rc2/cand'
OUTD = os.path.join(REPO, 'logs/sib/readcal2')
STRIDE = 4
WIN = 2136
GRID = 256
HALO_PX = 64
VOL = {'PHerc0139': '20250728140407', 'PHerc0814': '20250804134230'}
E0 = ['w024', 'w047', 'w053']
TIER_N = ['w023', 'w025', 'w026', 'w037', 'w048', 'w049', 'w050', 'w051', 'w052', 'w054', 'w055', 'w056', 'w057']
BASE_0139 = ['w028', 'w029', 'w030', 'w035', 'w039', 'w040', 'w041', 'w043', 'w044', 'w045', 'w046']
C0814 = ['20250925204843', '20250926165636', '20251001060526', '20250925222237', '20250925212701',
         '20260226123353', '20260225160055']
BASE_0814 = ['46527']
# every earlier window on PHerc0139 in the records (segment, y0, x0, size, source); organizer 9.362 um canvas
USED = [
    ('w041', 512, 512, 2136, 'HANDED-1'), ('w041', 768, 1792, 2136, 'HANDED-1'),
    ('w039', 2816, 512, 2136, 'HANDED-1'), ('w039', 3072, 1792, 2136, 'HANDED-1'),
    ('w035', 1792, 768, 2136, 'HANDED-R2/PROBE-1/2'), ('w030', 2816, 3072, 2136, 'HANDED-R2/PROBE-1/2'),
    ('w043', 3072, 4608, 2136, 'HANDED-R2/PROBE-1/2'), ('w039', 2816, 3840, 2136, 'HANDED-R2/PROBE-1/2'),
    ('w041', 2048, 256, 2136, 'HANDED-R3B'), ('w045', 2560, 1280, 2136, 'HANDED-R3B'),
    ('w043', 2816, 768, 2136, 'HANDED-R3B'), ('w039', 4352, 1024, 2136, 'HANDED-R3B'),
    ('w045', 512, 3584, 2136, 'HANDED-R3B'), ('w030', 512, 2816, 2136, 'HANDED-R3B'),
    ('w041', 3584, 2560, 2136, 'HANDED-R3B'), ('w030', 768, 256, 2136, 'HANDED-R3B'),
    ('w045', 768, 5888, 2136, 'PROBE-2 selection (not read)'),
    ('w044', 2816, 2816, 2136, 'PROBE-3 / D1 canary / D3 canary'), ('w040', 2560, 4096, 2136, 'PROBE-3'),
    ('w040', 256, 512, 2136, 'PROBE-3'),
    ('w040', 2048, 1152, 2136, 'C3 crop'), ('w040', 512, 5376, 2136, 'C3 crop'), ('w044', 2816, 2304, 2136, 'C3 crop'),
    ('w053', 256, 1536, 2136, 'D1 blank (SEAL-J-D1)'), ('w053', 256, 7168, 2136, 'D1 blank (SEAL-J-D1)'),
]
SEALED = [u for u in USED if 'SEAL-J-D1' in u[4]]


def save_npz(path, **kw):
    """Atomic compressed npz write (a reader never sees a half-written cache)."""
    tmp = path[:-4] + '.part.npz'
    np.savez_compressed(tmp, **kw)
    os.replace(tmp, path)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def seg_dir(scroll, key):
    ds = [d for d in glob.glob(f'{S3}/{scroll}/segments/*') if key in os.path.basename(d)]
    if len(ds) != 1:
        raise FileNotFoundError(f'{scroll} {key}: {ds}')
    return ds[0]


def mesh9(scroll, key):
    d = seg_dir(scroll, key)
    m = glob.glob(f'{d}/mesh/*-on-{VOL[scroll]}-9.362um.tifxyz')
    if len(m) != 1:
        raise FileNotFoundError(f'{scroll} {key} 9 um mesh: {m}')
    return read_tifxyz(m[0]), m[0]


def ink_tif(scroll, key):
    d = seg_dir(scroll, key)
    t = [p for p in glob.glob(f'{d}/ink-detection/*.tif') if '2.399um' in p and '20260417190342' in p]
    if len(t) != 1:
        raise FileNotFoundError(f'{scroll} {key} ink map: {t}')
    return t[0]


def voxel_um(scroll):
    md = json.load(open(glob.glob(f'{S3}/{scroll}/volumes/{VOL[scroll]}-*/metadata.json')[0]))
    return float(md['scan']['tomo']['acquisition']['detector']['samplePixelSize']) * 1000.0


def stage_ref(scroll, key):
    out = f'{CACHE}/{scroll}_{key}_ref9.npz'
    if os.path.exists(out):
        return dict(np.load(out.replace('.npz', '_meta.npz'), allow_pickle=True)['meta'].item())
    m, mp = mesh9(scroll, key)
    hw9 = G.canvas_shape(m)
    tp = ink_tif(scroll, key)
    ref2 = tifffile.imread(tp)
    if ref2.ndim != 2 or ref2.dtype != np.uint8:
        raise ValueError(f'unexpected ink map {ref2.shape} {ref2.dtype}')
    ref9 = G.map_ref_to_canvas(ref2, hw9)
    cov_rows = np.asarray(G.area_matrix(hw9[0], ref2.shape[0]).sum(1)).ravel() > 0.999
    cov_cols = np.asarray(G.area_matrix(hw9[1], ref2.shape[1]).sum(1)).ravel() > 0.999
    r8 = np.rint(np.clip(ref9, 0, 255)).astype(np.uint8)
    save_npz(out, ref9=r8, cov_rows=cov_rows, cov_cols=cov_cols)
    meta = dict(scroll=scroll, key=key, mesh=mp, ink_map=tp, N2_hw=list(ref2.shape), N9_hw=list(hw9),
                ratio_N2_over_N9_hw=[ref2.shape[0] / hw9[0], ref2.shape[1] / hw9[1]],
                ref9_u8_sha256=sha256_bytes(r8.tobytes()), mapping='c9 = (c2 + 10) N9/N2 - 10, exact separable area mean')
    np.savez(out.replace('.npz', '_meta.npz'), meta=np.array(meta, dtype=object))
    del ref2
    return meta


def load_ref(scroll, key):
    z = np.load(f'{CACHE}/{scroll}_{key}_ref9.npz')
    return z['ref9'], z['cov_rows'], z['cov_cols']


def surface_specs(scroll):
    """[(kind, name, segment, rect or None)] of every surface the samples are measured against."""
    specs = []
    if scroll == 'PHerc0139':
        specs += [('base', seg, seg, None) for seg in BASE_0139]
        for (seg, y0, x0, size, src) in USED:
            nm = f'{src}|{seg}_y{y0}_x{x0}'
            specs.append(('used', nm, seg, (y0, x0, size, size)))
            if 'SEAL-J-D1' in src:
                specs.append(('sealed', nm, seg, (y0, x0, size, size)))
    else:
        specs += [('base', k, k, None) for k in BASE_0814]
    return specs


def stage_dist(scroll, key):
    """Per-sample distances to every surface of surface_specs (one surface in memory at a time)."""
    out = f'{CACHE}/{scroll}_{key}_dist.npz'
    if os.path.exists(out):
        return
    m, _ = mesh9(scroll, key)
    yy, xx, xyz, mv = G.canvas_samples(m, STRIDE)
    pts = xyz.reshape(-1, 3)
    res = {'yy': yy.astype(np.int32), 'xx': xx.astype(np.int32), 'mv': mv}
    t0 = time.time()
    cache = {}
    for kind, name, seg, rect in surface_specs(scroll):
        if seg == key and kind == 'base':
            continue
        mm, _ = mesh9(scroll, seg)
        S = G.Surface(mm, rect=rect, name=name)
        dv, ds = G.distances(pts, S, radius=140.0 if kind == 'sealed' else 6.0)
        del S
        res[f'dv::{kind}|{name}'] = np.minimum(dv, 255).astype(np.float16).reshape(yy.shape)
        res[f'ds::{kind}|{name}'] = np.minimum(ds, 255).astype(np.float16).reshape(yy.shape)
        print(scroll, key, kind, name, 'n<2', int((ds < 2).sum()), round(time.time() - t0, 1), 's', flush=True)
    save_npz(out, **res)


def stage_e0dist(scroll, key):
    """Tier N only: distances to the whole E0 surfaces (w024, w047, w053). RCPICK-1 windows are unknown (ASK 1), so
    any E0 papyrus may have been shown to the RCPICK-1 picker; a tier-N window SAME papyrus with E0 is held."""
    out = f'{CACHE}/{scroll}_{key}_e0.npz'
    if os.path.exists(out) or scroll != 'PHerc0139' or key in E0:
        return
    m, _ = mesh9(scroll, key)
    yy, xx, xyz, mv = G.canvas_samples(m, STRIDE)
    pts = xyz.reshape(-1, 3)
    res = {}
    for seg in E0:
        mm, _ = mesh9(scroll, seg)
        S = G.Surface(mm, name=seg)
        dv, ds = G.distances(pts, S)
        del S
        res[f'dv::rcpickE0|{seg}'] = np.minimum(dv, 255).astype(np.float16).reshape(yy.shape)
        res[f'ds::rcpickE0|{seg}'] = np.minimum(ds, 255).astype(np.float16).reshape(yy.shape)
        print(scroll, key, 'rcpickE0', seg, 'n<2', int((ds < 2).sum()), flush=True)
    save_npz(out, **res)


def box_sum(a, k):
    """Sum over every k x k block (top-left aligned) via a summed-area table: out[i, j] = a[i:i+k, j:j+k].sum()."""
    c = np.pad(np.cumsum(np.cumsum(a.astype(np.int64), 0), 1), ((1, 0), (1, 0)))
    return c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]


def stage_windows(scroll, key, tier, min_cov, used_rects_same_canvas):
    z0 = np.load(f'{CACHE}/{scroll}_{key}_dist.npz')
    z = {k: z0[k] for k in z0.files}
    e0p = f'{CACHE}/{scroll}_{key}_e0.npz'
    if os.path.exists(e0p):
        z1 = np.load(e0p)
        z.update({k: z1[k] for k in z1.files})
    z = type('Z', (), {'files': list(z), '__getitem__': lambda self, k, _d=z: _d[k]})()
    ref9, cov_rows, cov_cols = load_ref(scroll, key)
    yy, xx, mv = z['yy'], z['xx'], z['mv']
    covered = cov_rows[yy] & cov_cols[xx]
    refv = ref9[yy, xx]
    base_keys = [k[4:] for k in z.files if k.startswith('ds::base|')]
    near_base = np.zeros(yy.shape, bool)
    for k in base_keys:
        near_base |= z[f'ds::{k}'].astype(np.float32) < 2.0
    halo = HALO_PX // STRIDE
    excl = ndimage.binary_dilation(near_base, structure=np.ones((2 * halo + 1, 2 * halo + 1), bool)) if near_base.any() else near_base
    good = mv & covered & ~excl
    n = WIN // STRIDE  # samples per window side
    step = GRID // STRIDE
    Hs, Ws = yy.shape
    y0s = np.arange(0, Hs - n + 1, step)
    x0s = np.arange(0, Ws - n + 1, step)
    cov = box_sum(good, n)[np.ix_(y0s, x0s)] / float(n * n)
    ink = box_sum(good & (refv >= 150), n)[np.ix_(y0s, x0s)]
    ngood = box_sum(good, n)[np.ix_(y0s, x0s)]
    # CORR same-papyrus bin counts per window for every base / used surface
    def binsum(key_, form):
        d = z[f'{form}::{key_}'].astype(np.float32)
        return [box_sum((d >= lo) & (d < lo + 1), n)[np.ix_(y0s, x0s)] for lo in (0, 1, 2)]
    same_any = np.zeros(cov.shape, bool)
    same_with = [[[] for _ in x0s] for _ in y0s]
    for k in base_keys + [k[4:] for k in z.files if k.startswith('ds::used|') or k.startswith('ds::rcpickE0|')]:
        for form in ('dv', 'ds'):
            c0, c1, c2 = binsum(k, form)
            s = ((c0 + c1) >= G.SP_MIN_WITHIN_2) & (c0 >= G.SP_RATIO * c2)
            if s.any():
                same_any |= s
                for i, j in zip(*np.nonzero(s)):
                    if k not in same_with[i][j]:
                        same_with[i][j].append(k)
    # sealed clearance lower bound: min over window samples of min(ds, dv - 3.5); inf when > 140 vox
    seal_keys = [k[4:] for k in z.files if k.startswith('ds::sealed|')]
    seal_lb = np.full(cov.shape, np.inf)
    for k in seal_keys:
        lb = np.minimum(z[f'ds::{k}'].astype(np.float32), z[f'dv::{k}'].astype(np.float32) - 3.5)
        lb = np.where(z[f'ds::{k}'].astype(np.float32) >= 255, np.inf, lb)
        lbm = ndimage.minimum_filter(lb, size=n, origin=(-(n // 2), -(n // 2)), mode='constant', cval=np.inf)
        seal_lb = np.minimum(seal_lb, lbm[np.ix_(y0s, x0s)])
    rows = []
    for i, y0 in enumerate(y0s * STRIDE):
        for j, x0 in enumerate(x0s * STRIDE):
            ov = [nm for (nm, r) in used_rects_same_canvas
                  if not (y0 + WIN <= r[0] or r[0] + r[2] <= y0 or x0 + WIN <= r[1] or r[1] + r[3] <= x0)]
            c = float(cov[i, j])
            if c < min(min_cov, 0.75):
                continue
            inkf = float(ink[i, j] / ngood[i, j]) if ngood[i, j] else float('nan')
            rows.append(dict(scroll=scroll, segment=key, tier=tier, y0=int(y0), x0=int(x0), coverage=round(c, 4),
                             base_same=[k for k in same_with[i][j] if k.startswith('base|')],
                             used_same=[k for k in same_with[i][j] if k.startswith('used|')],
                             e0_same=[k for k in same_with[i][j] if k.startswith('rcpickE0|')],
                             used_overlap_2d=ov,
                             sealed_lb_vox=(None if not np.isfinite(seal_lb[i, j]) else round(float(seal_lb[i, j]), 2)),
                             _ink=inkf))
    return rows, dict(n_samples=int(yy.size), mesh_valid=int(mv.sum()), covered=int((mv & covered).sum()),
                      base_excluded=int((mv & covered & excl).sum()), n_windows_grid=int(cov.size))


RCPICK_H1 = [u for u in USED if u[4] == 'HANDED-1']


def stage_rcpick_dist(key):
    """Distances (cap 140 vox) of an E0 segment's samples to the HANDED-1 windows (the 'sealed set' of the
    DECL-READCAL-A2 rule at RCPICK-1 time), for the reconstruction check only."""
    out = f'{CACHE}/PHerc0139_{key}_rcpick.npz'
    if os.path.exists(out):
        return
    m, _ = mesh9('PHerc0139', key)
    yy, xx, xyz, mv = G.canvas_samples(m, STRIDE)
    pts = xyz.reshape(-1, 3)
    res = {}
    for (seg, y0, x0, size, src) in RCPICK_H1:
        mm, _ = mesh9('PHerc0139', seg)
        S = G.Surface(mm, rect=(y0, x0, 1068, 1068))  # HANDED-1 windows are 1 x 1 cm (DECL-HANDED)
        dv, ds = G.distances(pts, S, radius=140.0)
        res[f'{seg}_y{y0}_x{x0}'] = np.minimum(np.minimum(ds, dv), 255).astype(np.float16).reshape(yy.shape)
    save_npz(out, **res)


def rcpick_reconstruct(key):
    """RCBANK-1 attempt-2 rule (DECL-READCAL-A2): eligible = not within 2 vox of a base trace (+64 px halo) and not
    within 128 vox of a HANDED-1 window; candidate = 2136 px window on a 256 px grid with >= 90 % reference-valid
    coverage and no ineligible sample. Returns (candidate list, count)."""
    z = np.load(f'{CACHE}/PHerc0139_{key}_dist.npz')
    zr = np.load(f'{CACHE}/PHerc0139_{key}_rcpick.npz')
    ref9, cov_rows, cov_cols = load_ref('PHerc0139', key)
    yy, xx, mv = z['yy'], z['xx'], z['mv']
    covered = cov_rows[yy] & cov_cols[xx] & mv
    near = np.zeros(yy.shape, bool)
    for k in z.files:
        if k.startswith('ds::base|'):
            near |= z[k].astype(np.float32) < 2.0
    halo = HALO_PX // STRIDE
    excl = ndimage.binary_dilation(near, structure=np.ones((2 * halo + 1,) * 2, bool)) if near.any() else near
    for k in zr.files:
        excl |= zr[k].astype(np.float32) < 128.0
    n, step = WIN // STRIDE, GRID // STRIDE
    Hs, Ws = yy.shape
    y0s, x0s = np.arange(0, Hs - n + 1, step), np.arange(0, Ws - n + 1, step)
    cov = box_sum(covered, n)[np.ix_(y0s, x0s)] / float(n * n)
    bad = box_sum(excl & covered, n)[np.ix_(y0s, x0s)]
    ok = (cov >= 0.90) & (bad == 0)
    cands = [(int(y0s[i] * STRIDE), int(x0s[j] * STRIDE)) for i, j in zip(*np.nonzero(ok))]
    return cands


def windows_all():
    out = {'provenance': PROV, 'rules': __doc__.split('Rules')[1], 'stride_px': STRIDE, 'window_px': WIN,
           'grid_px': GRID, 'segments': {}, 'text_candidates': [], 'blank_candidates': [], 'held_rcpick1': [],
           'rejected_counts': {}}
    ink_private = {}
    for scroll, key, tier in segments_all():
        if not os.path.exists(f'{CACHE}/{scroll}_{key}_dist.npz'):
            out['segments'][f'{scroll}:{key}'] = {'status': 'no distance cache'}
            continue
        rects = [(f'{u[4]}|{u[0]}_y{u[1]}_x{u[2]}', (u[1], u[2], u[3], u[3])) for u in USED if u[0] == key] \
            if scroll == 'PHerc0139' else []
        min_cov = 0.90 if scroll == 'PHerc0139' else 0.75
        rows, st = stage_windows(scroll, key, tier, min_cov, rects)
        rej = {'coverage': 0, 'base_same': 0, 'used_same': 0, 'used_overlap_2d': 0, 'sealed_lt_128': 0}
        n_text = n_blank = 0
        for r in rows:
            ink = r.pop('_ink')
            reasons = []
            if r['coverage'] < min_cov:
                reasons.append('coverage')
            if r['base_same']:
                reasons.append('base_same')
            if r['used_same']:
                reasons.append('used_same')
            if r['used_overlap_2d']:
                reasons.append('used_overlap_2d')
            if r['sealed_lb_vox'] is not None and r['sealed_lb_vox'] < 128.0:
                reasons.append('sealed_lt_128')
            for x in reasons:
                rej[x] += 1
            if reasons:
                continue
            held = None
            if tier == 'E0':
                held = 'RCPICK-1 windows unknown (ASK 1): any E0 window may overlap one'
            elif r.pop('e0_same', None):
                held = 'SAME papyrus with E0 (possible RCPICK-1 window; ASK 1)'
            r.pop('e0_same', None)
            if held:
                r['held'] = held
                r['flags'] = [f'tier-{tier}'] if tier != 'E0' else []
                if r['coverage'] >= 0.90 and np.isfinite(ink) and ink < 0.01:
                    r['blank'] = True
                out['held_rcpick1'].append(r)
                rej['held_rcpick1'] = rej.get('held_rcpick1', 0) + 1
                continue
            r['flags'] = [f for f in ([f'tier-{tier}'] if tier != 'E0' else []) + (['0814-ribbon'] if scroll == 'PHerc0814' else [])]
            is_blank = r['coverage'] >= 0.90 and np.isfinite(ink) and ink < 0.01
            if is_blank:
                out['blank_candidates'].append(dict(r, ref_ink_frac=round(ink, 5)))
                n_blank += 1
            else:
                out['text_candidates'].append(r)
                n_text += 1
            ink_private[(scroll, key, r['y0'], r['x0'])] = ink
        st.update(n_text=n_text, n_blank=n_blank, rejected=rej, tier=tier)
        out['segments'][f'{scroll}:{key}'] = st
    out['text_candidates'].sort(key=lambda r: (r['scroll'], r['segment'], r['y0'], r['x0']))
    out['blank_candidates'].sort(key=lambda r: (r['ref_ink_frac'], -r['coverage'], r['segment'], r['y0'], r['x0']))
    # picker tiling: per segment, greedy non-overlapping windows in (y0, x0) order (geometry only, never ink)
    tiling, taken = [], {}
    for r in out['text_candidates']:
        k = (r['scroll'], r['segment'])
        if any(not (r['y0'] + WIN <= t[0] or t[0] + WIN <= r['y0'] or r['x0'] + WIN <= t[1] or t[1] + WIN <= r['x0'])
               for t in taken.get(k, [])):
            continue
        taken.setdefault(k, []).append((r['y0'], r['x0']))
        tiling.append({kk: r[kk] for kk in ('scroll', 'segment', 'tier', 'y0', 'x0', 'coverage', 'flags')})
    out['picker_tiling'] = tiling
    return out


def segments_all():
    out = [('PHerc0139', k, 'E0') for k in E0] + [('PHerc0139', k, 'N') for k in TIER_N]
    out += [('PHerc0814', k, '0814') for k in C0814]
    return out


def main(stages):
    os.makedirs(CACHE, exist_ok=True)
    rec = {'provenance': PROV, 'voxel_um': {s: voxel_um(s) for s in VOL}, 'ref': {}, 'windows_stats': {}}
    for scroll, key, tier in segments_all():
        if 'ref' in stages:
            rec['ref'][f'{scroll}:{key}'] = stage_ref(scroll, key)
            print('ref', scroll, key, flush=True)
        if 'dist' in stages:
            stage_dist(scroll, key)
        if 'rcpick' in stages and tier == 'E0':
            stage_rcpick_dist(key)
        if 'e0dist' in stages and tier == 'N':
            stage_e0dist(scroll, key)
    if 'ref' in stages:
        json.dump(rec, open(f'{CACHE}/stage_record.json', 'w'), indent=1, default=str)
    if 'rcpick' in stages:
        recon = {}
        for key in E0:
            c = rcpick_reconstruct(key)
            on1024 = [x for x in c if x[0] % 1024 == 0 and x[1] % 1024 == 0]
            recon[key] = {'n_candidates_256grid': len(c), 'recorded_RCBANK1': {'w024': 251, 'w047': 165, 'w053': 1731}[key],
                          'n_on_1024_grid': len(on1024), 'recorded_picker_windows': {'w024': 6, 'w047': 3, 'w053': 24}[key],
                          'on_1024_grid': on1024}
        t = json.dumps({'provenance': PROV, 'rule': rcpick_reconstruct.__doc__, 'segments': recon}, indent=1) + '\n'
        open(os.path.join(OUTD, 'rcpick1_reconstruction.json'), 'w').write(t)
        print(json.dumps({k: {kk: v[kk] for kk in v if kk != 'on_1024_grid'} for k, v in recon.items()}))
    if 'windows' in stages:
        out = windows_all()
        out['voxel_um'] = rec['voxel_um']
        t = json.dumps(out, indent=1) + '\n'
        open(os.path.join(OUTD, 'candidates.json'), 'w').write(t)
        print(json.dumps({k: v for k, v in out['segments'].items()}, default=str)[:3000])
        print('text', len(out['text_candidates']), 'blank', len(out['blank_candidates']), 'tiling', len(out['picker_tiling']))


if __name__ == '__main__':
    main(sys.argv[1:] or ['ref', 'dist'])
