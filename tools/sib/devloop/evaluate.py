# Provenance: Project HERCULES | owner the owner | [id removed]
"""DEV-LOOP evaluator (task devloop; RULES.md DECL-DEVLOOP). Numbers only: no image is written for viewing,
opened or displayed; model maps and references are handled as arrays and summarised by metrics and hashes.

Stages
  prep   (once per DEV window, candidate-independent; cached in /work/devloop/win/<id>/)
         1. official vc_render_tifxyz of the organizer 9 um mesh, -n 31 --flip-normals --scale 1, voxel size from
            the volume's metadata.json, crop = window + 256 px margin (intersected with the canvas);
         2. render-valid = any of the 31 slices nonzero;
         3. CT registration (candidate-independent): our slice 15 vs the 2.4 um organizer SV (pyramid level 2,
            mean of slices 52..56 of 109, surface = 54) mapped by the canvas formula; 3 x 3 tiles, NCC over
            integer shifts +-4 px, parabola refinement; GATE: >= 5 of 9 tiles with NCC >= 0.35 off the search
            border, MAD <= 1.0 px per axis and |median shift| <= 3 px; a failing window is dropped and recorded;
         4. reference on the 9 um window = area average (4 x 4 sub-samples) of the official 2.4 um map at the
            registered coordinates; valid = render-valid & inside the map & 2.4 um SV nonzero & not excluded by
            the registry (base-training papyrus + halo).
  infer  (per checkpoint) official `vesuvius.ink_detection.inference.infer <render.zarr> <ckpt> <out.tif>
         --direction both --batch-size 4 --num-workers 1 --no-compile` (C2-NT: no TTA), CPU, OMP threads recorded.
  score  sigma_eq (hercules.metrics.pixel.sigma_eq) of the text-order map vs the reference per text window and
         pooled per scroll; blob_f180 of both orders on blank windows (constraint: NON-text-order <= 0.0272);
         the text order per scroll is chosen ONCE from the base checkpoint (AUC vs reference labels ink >= 150,
         blank <= 100, pooled over the scroll's text windows) and stored in logs/sib/devloop/text_order.json.
Usage: python evaluate.py prep | eval --ckpt PATH --tag TAG [--base] [--threads 3] [--windows ID ...]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'src'))
sys.path.insert(0, HERE)
import devlib as D  # noqa: E402
from hercules.metrics import pixel as PX  # noqa: E402

PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
S3DIR = '/work/devloop/s3'
WIN = '/work/devloop/win'
EVAL = '/work/devloop/eval'
BUCKET = 'vesuvius-challenge-open-data'
REG = os.path.join(REPO, 'logs/sib/devloop/dev_registry.json')
TEXT_ORDER = os.path.join(REPO, 'logs/sib/devloop/text_order.json')
MARGIN = 256
N_SLICES = 31
SV2_LEVEL, SV2_SLICES = 2, (52, 57)
GATE = dict(min_tiles=5, min_ncc=0.35, max_mad=1.0, max_shift=3.0)
PY_INK = '/opt/hv-ink/bin/python'
VC = '/work/bin/vc'
SIGMA_CRIT_MM = 0.30  # RULES.md D1-REF-RESULT


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def arr_sha(a):
    a = np.ascontiguousarray(a)
    return hashlib.sha256(a.tobytes() + str(a.dtype).encode() + str(a.shape).encode()).hexdigest()


def tree_sha(root):
    h = hashlib.sha256()
    for dp, dn, fn in sorted(os.walk(root)):
        dn.sort()
        for f in sorted(fn):
            p = os.path.join(dp, f)
            h.update(os.path.relpath(p, root).encode() + b'\0' + sha256(p).encode())
    return h.hexdigest()


def jdump(path, obj):
    d = {'provenance': PROV}
    d.update(obj)
    t = json.dumps(d, indent=1, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o)) + '\n'
    assert t.isascii()
    with open(path + '.tmp', 'w') as f:
        f.write(t)
    os.replace(path + '.tmp', path)
    return hashlib.sha256(t.encode()).hexdigest()


def windows_from_registry():
    reg = json.load(open(REG))
    out = []
    for scroll, s in reg['scrolls'].items():
        for w in s['windows'] + s['blanks']:
            seg = s['segments'][w['segment']]
            out.append(dict(w, scroll=scroll, vol9=s['vol9'], vol2=s['vol2'], voxel_um_9=s['voxel_um_9'],
                            mesh9=seg['mesh9'], ref_map=seg['ref_map'], ref_map_sha256=seg['ref_map_sha256'],
                            canvas9=seg['canvas9'], r_yx=seg['r_yx']))
    return reg, out


# ---------------------------------------------------------------------------------------------------------------
# 2.4 um SV reader: byte-range reads of the surface slab of uncompressed (109, 128, 128) chunks
# ---------------------------------------------------------------------------------------------------------------

def _s3():
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    return boto3.client('s3', config=Config(signature_version=UNSIGNED, max_pool_connections=32,
                                            retries={'max_attempts': 8, 'mode': 'adaptive'}))


def sv2_slab(scroll, seg_id, vol2, y0, x0, h, w, level=SV2_LEVEL, zs=SV2_SLICES):
    """Mean of slices zs[0]..zs[1]-1 of the 2.4 um organizer SV at pyramid ``level`` over rows y0..y0+h,
    cols x0..x0+w (level pixels; clipped to the array). Returns (float32 mean, bool any-slice-zero mask, meta)."""
    cli = _s3()
    vid = vol2.split('-')[0]
    pre = f'{scroll}/segments/{seg_id}/surface-volumes/'
    r = cli.list_objects_v2(Bucket=BUCKET, Prefix=pre, Delimiter='/')
    zarrs = [c['Prefix'] for c in r.get('CommonPrefixes', []) if vid in c['Prefix'] and c['Prefix'].endswith('.zarr/')]
    assert len(zarrs) == 1, zarrs
    zp = zarrs[0]
    za = json.loads(cli.get_object(Bucket=BUCKET, Key=f'{zp}{level}/.zarray')['Body'].read())
    Z, Hs, Ws = za['shape']
    cz, cy, cx = za['chunks']
    assert za['compressor'] is None and za['dtype'] == '|u1' and za['order'] == 'C' and cz == Z, za
    assert za.get('dimension_separator') == '/'
    ya, yb = max(0, y0), min(Hs, y0 + h)
    xa, xb = max(0, x0), min(Ws, x0 + w)
    out = np.zeros((zs[1] - zs[0], h, w), np.uint8)
    plane = cy * cx
    rng = f'bytes={zs[0] * plane}-{zs[1] * plane - 1}'
    jobs = [(iy, ix) for iy in range(ya // cy, (yb - 1) // cy + 1) for ix in range(xa // cx, (xb - 1) // cx + 1)]

    def fetch(job):
        iy, ix = job
        key = f'{zp}{level}/0/{iy}/{ix}'
        for k in range(6):
            try:
                b = cli.get_object(Bucket=BUCKET, Key=key, Range=rng)['Body'].read()
                return job, np.frombuffer(b, np.uint8).reshape(zs[1] - zs[0], cy, cx)
            except cli.exceptions.NoSuchKey:
                return job, np.zeros((zs[1] - zs[0], cy, cx), np.uint8)  # fill value 0
            except Exception:
                if k == 5:
                    raise
                time.sleep(2 ** k)

    nbytes = 0
    with cf.ThreadPoolExecutor(16) as ex:
        for (iy, ix), blk in ex.map(fetch, jobs):
            nbytes += blk.nbytes
            gy0, gx0 = iy * cy, ix * cx
            sy0, sy1 = max(gy0, ya), min(gy0 + cy, yb)
            sx0, sx1 = max(gx0, xa), min(gx0 + cx, xb)
            out[:, sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = blk[:, sy0 - gy0:sy1 - gy0, sx0 - gx0:sx1 - gx0]
    zero = (out == 0).any(0)
    return out.astype(np.float32).mean(0), zero, dict(zarr=zp, level=level, slices=list(range(*zs)), shape=za['shape'],
                                                         chunks=[cz, cy, cx], n_chunks=len(jobs), bytes_read=nbytes)


# ---------------------------------------------------------------------------------------------------------------
# prep
# ---------------------------------------------------------------------------------------------------------------

def render(w, wd):
    Hc, Wc = w['canvas9']
    x, y = w['x0'] - MARGIN, w['y0'] - MARGIN
    ww, hh = w['w'] + 2 * MARGIN, w['h'] + 2 * MARGIN
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + ww, Wc), min(y + hh, Hc)
    crop = (x0, y0, x1 - x0, y1 - y0)
    vol = f's3://{BUCKET}/{w["scroll"]}/volumes/{w["vol9"]}/'
    out = f'{wd}/render.zarr'
    cmd = [VC, 'vc_render_tifxyz', '-v', vol, '--remote-url', vol, '--segmentation', f'{S3DIR}/{w["mesh9"]}',
           '--scale', '1', '--group-idx', '0', '--num-slices', str(N_SLICES), '--slice-step', '1',
           '--voxel-size', f'{w["voxel_um_9"]:g}', '--voxel-unit', 'micrometer',
           '--crop-x', str(crop[0]), '--crop-y', str(crop[1]), '--crop-width', str(crop[2]),
           '--crop-height', str(crop[3]), '--flip-normals', '--cache-gb', '4', '--zarr-output', out]
    t0 = time.time()
    with open(f'{wd}/render.log', 'w') as lf:
        pr = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT, env=dict(os.environ, VC_CPUS='3',
                                                                                OMP_NUM_THREADS='3'))
    return dict(command=' '.join(cmd), returncode=pr.returncode, seconds=round(time.time() - t0, 1),
                crop_xywh=list(crop), origin_yx=[crop[1], crop[0]], output=out)


def load_render(path):
    import zarr
    z = zarr.open(path, mode='r')
    a = z['0'] if hasattr(z, 'keys') and '0' in z else z
    return np.asarray(a[:])


def read_ref_crop(path, y0, x0, h, w):
    import tifffile
    import zarr
    with tifffile.TiffFile(path) as t:
        z = zarr.open(t.aszarr(), mode='r')
        H, W = z.shape
        out = np.zeros((h, w), np.uint8)
        ya, yb, xa, xb = max(0, y0), min(H, y0 + h), max(0, x0), min(W, x0 + w)
        if yb > ya and xb > xa:
            out[ya - y0:yb - y0, xa - x0:xb - x0] = z[ya:yb, xa:xb]
    return out


def prep_window(w, reg_excl):
    wd = f'{WIN}/{w["id"]}'
    os.makedirs(wd, exist_ok=True)
    recp = f'{wd}/prep.json'
    if os.path.exists(recp) and json.load(open(recp)).get('done'):
        return json.load(open(recp))
    rec = dict(generated_utc=utc(), window=w, stage='prep')
    rj = f'{wd}/render.json'
    rr = json.load(open(rj)) if os.path.exists(rj) and json.load(open(rj))['returncode'] == 0 else render(w, wd)
    rec['render'] = rr
    if rr['returncode'] != 0:
        rec['done'] = False
        jdump(recp, rec)
        return rec
    stack = load_render(rr['output'])
    rec['render']['shape'] = list(stack.shape)
    rec['render']['tree_sha256'] = tree_sha(rr['output'])
    oy, ox = rr['origin_yx']
    wy, wx = w['y0'] - oy, w['x0'] - ox
    h, ww = w['h'], w['w']
    rv = (stack > 0).any(0)
    ours = stack[N_SLICES // 2].astype(np.float32)
    ry, rx = w['r_yx']
    # 2.4 um SV level-2 slab covering the window + pad, mapped to the 9 um window grid by the canvas formula
    pad = 8
    rows9 = np.arange(-pad, h + pad) + w['y0']
    cols9 = np.arange(-pad, ww + pad) + w['x0']
    ly = D.level_coord(D.c9_to_c2(rows9, ry), SV2_LEVEL)
    lx = D.level_coord(D.c9_to_c2(cols9, rx), SV2_LEVEL)
    Y0, X0 = int(np.floor(ly.min())) - 2, int(np.floor(lx.min())) - 2
    Hh, Wh = int(np.ceil(ly.max())) - Y0 + 3, int(np.ceil(lx.max())) - X0 + 3
    slab, zero, svmeta = sv2_slab(w['scroll'], w['segment_id'], w['vol2'], Y0, X0, Hh, Wh)
    rec['sv2'] = dict(svmeta, origin_yx=[Y0, X0], shape=[Hh, Wh])
    import cv2
    slab_nan = np.where(zero, np.nan, slab).astype(np.float32)

    def ct2_on9(dy9, dx9, S):
        yy = D.level_coord(D.c9_to_c2(np.arange(-S, h + S) + w['y0'] + dy9, ry), SV2_LEVEL) - Y0
        xx = D.level_coord(D.c9_to_c2(np.arange(-S, ww + S) + w['x0'] + dx9, rx), SV2_LEVEL) - X0
        my, mx = np.meshgrid(yy.astype(np.float32), xx.astype(np.float32), indexing='ij')
        img = cv2.remap(np.nan_to_num(slab_nan, nan=0.0), mx, my, cv2.INTER_LINEAR, borderValue=0)
        bad = cv2.remap(np.isnan(slab_nan).astype(np.float32), mx, my, cv2.INTER_LINEAR, borderValue=1)
        return img, bad < 1e-6

    ov = ours[wy:wy + h, wx:wx + ww]
    vv = rv[wy:wy + h, wx:wx + ww] & (ov > 0)
    reg = D.ct_residual_shift(ov, vv, ct2_on9, sub_windows=3, max_shift=4, min_ncc=GATE['min_ncc'])
    gate = (reg['n_good'] >= GATE['min_tiles'] and reg['mad9'] is not None and max(reg['mad9']) <= GATE['max_mad']
            and max(abs(reg['shift9'][0]), abs(reg['shift9'][1])) <= GATE['max_shift'])
    rec['ct_registration'] = dict(reg, gate=GATE, passed=bool(gate))
    if not gate:
        rec['done'] = True
        rec['dropped'] = 'CT registration gate failed'
        jdump(recp, rec)
        return rec
    dy9, dx9 = reg['shift9']
    shift2 = (dy9 * ry, dx9 * rx)
    # reference crop on the 2.4 um canvas covering the window
    y2a = int(np.floor(D.c9_to_c2(w['y0'] - 1 + dy9, ry))) - 4
    y2b = int(np.ceil(D.c9_to_c2(w['y0'] + h + 1 + dy9, ry))) + 4
    x2a = int(np.floor(D.c9_to_c2(w['x0'] - 1 + dx9, rx))) - 4
    x2b = int(np.ceil(D.c9_to_c2(w['x0'] + ww + 1 + dx9, rx))) + 4
    refpath = f'{S3DIR}/{w["ref_map"]}'
    ref2 = read_ref_crop(refpath, y2a, x2a, y2b - y2a, x2b - x2a)
    ref9, inside = D.ref_on_9(ref2, (w['y0'], w['x0'], h, ww), (ry, rx), shift2_yx=shift2, ref_origin_yx=(y2a, x2a))
    ct9, ctok = ct2_on9(dy9, dx9, 0)
    excl = reg_excl(w)
    valid = vv & inside & ctok & ~excl
    np.save(f'{wd}/ref9.npy', ref9)
    np.save(f'{wd}/valid.npy', valid)
    rec.update(done=True, shift2_yx=list(shift2), ref9_sha256=arr_sha(ref9), valid_sha256=arr_sha(valid),
               render_valid_frac=float(vv.mean()), valid_frac=float(valid.mean()),
               excluded_frac=float(excl.mean()), ref_ink_frac=float((ref9[valid] >= 150).mean()) if valid.any()
               else None, ref_map_sha256_check=sha256(refpath) == w['ref_map_sha256'],
               ncc_ours_vs_ct2_registered=float(D._ncc(ov, ct9, vv & ctok)))
    jdump(recp, rec)
    return rec


def make_excl():
    """Registry exclusion mask (stride-4 samples: base-training papyrus + halo) upsampled to the window."""
    cache = {}

    def f(w):
        key = (w['scroll'], w['segment'])
        if key not in cache:
            z = np.load(f'/work/devloop/registry/{w["scroll"]}_{w["segment"]}.npz')
            cache[key] = z['excl']
        e = cache[key]
        s = 4
        rows = (np.arange(w['h']) + w['y0']) // s
        cols = (np.arange(w['w']) + w['x0']) // s
        rows = np.clip(rows, 0, e.shape[0] - 1)
        cols = np.clip(cols, 0, e.shape[1] - 1)
        out = e[np.ix_(rows, cols)]
        # CORR-RETRACE-RULE v4 mask (point-to-surface < 16 vox from base-training traces), stride 2, OR-ed in
        v4 = np.load(f'/work/devloop/registry/v4mask_{w["id"]}.npz')
        m2 = v4['mask']
        st = int(v4['stride'])
        r2 = np.clip(np.arange(w['h']) // st, 0, m2.shape[0] - 1)
        c2 = np.clip(np.arange(w['w']) // st, 0, m2.shape[1] - 1)
        return out | m2[np.ix_(r2, c2)]
    return f


def accepted_ids():
    c = json.load(open(os.path.join(REPO, 'logs/sib/devloop/dev_certificate_v4.json')))
    return {k for s in c['scrolls'].values() for k, v in s['windows'].items() if v['accepted']}


def cmd_render(ids):
    reg, wins = windows_from_registry()
    for w in wins:
        if ids and w['id'] not in ids:
            continue
        wd = f'{WIN}/{w["id"]}'
        os.makedirs(wd, exist_ok=True)
        if os.path.exists(f'{wd}/render.json') and json.load(open(f'{wd}/render.json'))['returncode'] == 0:
            continue
        rr = render(w, wd)
        jdump(f'{wd}/render.json', rr)
        print(w['id'], rr['returncode'], rr['seconds'], flush=True)


def cmd_prep(ids):
    reg, wins = windows_from_registry()
    acc = accepted_ids()
    wins = [w for w in wins if w['id'] in acc]
    ex = make_excl()
    out = {}
    for w in wins:
        if ids and w['id'] not in ids:
            continue
        t0 = time.time()
        r = prep_window(w, ex)
        out[w['id']] = dict(role=w['role'], done=r.get('done'), dropped=r.get('dropped'),
                            render_seconds=r.get('render', {}).get('seconds'),
                            ct=dict(passed=r.get('ct_registration', {}).get('passed'),
                                    shift9=r.get('ct_registration', {}).get('shift9'),
                                    mad9=r.get('ct_registration', {}).get('mad9'),
                                    n_good=r.get('ct_registration', {}).get('n_good'),
                                    ncc_median=r.get('ct_registration', {}).get('ncc_median')),
                            valid_frac=r.get('valid_frac'), ref_ink_frac=r.get('ref_ink_frac'),
                            ncc_registered=r.get('ncc_ours_vs_ct2_registered'), seconds=round(time.time() - t0, 1))
        print(w['id'], json.dumps(out[w['id']]), flush=True)
    s = jdump(os.path.join(REPO, 'logs/sib/devloop/prep_summary.json'),
              dict(generated_utc=utc(), registry_sha256=sha256(REG), evaluate_sha256=sha256(__file__),
                   devlib_sha256=sha256(os.path.join(HERE, 'devlib.py')), windows=out))
    print('prep_summary', s)


# ---------------------------------------------------------------------------------------------------------------
# infer + score
# ---------------------------------------------------------------------------------------------------------------

def infer_window(ckpt, tag, wid, threads):
    od = f'{EVAL}/{tag}/{wid}'
    os.makedirs(od, exist_ok=True)
    recp = f'{od}/infer.json'
    if os.path.exists(recp) and json.load(open(recp)).get('returncode') == 0:
        return json.load(open(recp))
    fwd, rev = f'{od}/{wid}.tif', f'{od}/{wid}_reverse.tif'
    cmd = [PY_INK, '-m', 'vesuvius.ink_detection.inference.infer', f'{WIN}/{wid}/render.zarr', ckpt, fwd,
           '--direction', 'both', '--batch-size', '4', '--num-workers', '1', '--no-compile']
    t = str(int(threads))
    env = dict(os.environ, OMP_NUM_THREADS=t, MKL_NUM_THREADS=t, OPENBLAS_NUM_THREADS=t, PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONPATH', None)
    t0 = time.time()
    start = utc()
    with open(f'{od}/infer.log', 'w') as lf:
        pr = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT, env=env, cwd=od)
    rec = dict(command=' '.join(cmd), threads=int(threads), start_utc=start, end_utc=utc(),
               seconds=round(time.time() - t0, 1), returncode=pr.returncode)
    if pr.returncode == 0:
        rec['outputs'] = {os.path.basename(p): sha256(p) for p in (fwd, rev)}
    jdump(recp, rec)
    return rec


def load_map(path):
    import tifffile
    a = tifffile.imread(path)
    assert a.dtype == np.uint8 and a.ndim == 2, (a.dtype, a.shape)
    return a


def cmd_eval(ckpt, tag, is_base, threads, ids):
    reg, wins = windows_from_registry()
    acc = accepted_ids()
    wins = [w for w in wins if w['id'] in acc]
    ck_sha = sha256(ckpt)
    t_all = time.time()
    if not is_base and not os.path.exists(TEXT_ORDER):
        raise SystemExit('text order not yet fixed: run the base checkpoint first (--base)')
    per = {}
    for w in wins:
        if ids and w['id'] not in ids:
            continue
        pr = json.load(open(f'{WIN}/{w["id"]}/prep.json'))
        if not pr.get('done') or pr.get('dropped'):
            per[w['id']] = dict(skipped=pr.get('dropped', 'prep not done'))
            continue
        ir = infer_window(ckpt, tag, w['id'], threads)
        if ir['returncode'] != 0:
            per[w['id']] = dict(infer=ir)
            continue
        oy, ox = pr['render']['origin_yx']
        wy, wx = w['y0'] - oy, w['x0'] - ox
        ref9 = np.load(f'{WIN}/{w["id"]}/ref9.npy')
        valid = np.load(f'{WIN}/{w["id"]}/valid.npy')
        maps = {}
        for order, suf in (('forward', ''), ('reverse', '_reverse')):
            m = load_map(f'{EVAL}/{tag}/{w["id"]}/{w["id"]}{suf}.tif')
            maps[order] = m[wy:wy + w['h'], wx:wx + w['w']]
        lab = D.ref_labels(ref9, valid)
        rec = dict(role=w['role'], scroll=w['scroll'], infer_seconds=ir['seconds'], threads=ir['threads'],
                   map_sha256={k: arr_sha(v) for k, v in maps.items()}, n_valid=int(valid.sum()))
        for order, m in maps.items():
            d = dict(auc=PX.auc(m, lab, valid), mean_valid=float(m[valid].mean()))
            if w['role'] == 'text':
                d.update(D.sigma_eq_window(m, ref9, valid, w['voxel_um_9']))
                # diagnostic only (never used in the metric): best integer shift of the map against the reference
                # blurred to sigma_eq; a nonzero shift would flag a render/inference frame offset
                import cv2
                sp = d['sigma_eq_mm'] * D.px_per_mm(w['voxel_um_9'])
                rb = ref9 if sp == 0 else cv2.GaussianBlur(ref9, (0, 0), sp, borderType=cv2.BORDER_REFLECT)
                S = 3
                ss = D.shift_search(m[S:-S, S:-S].astype(np.float32), rb, valid[S:-S, S:-S], valid, S)
                d['diag_map_vs_ref_shift_px'] = [float(v) for v in ss['shift']]
                d['diag_map_vs_ref_ncc_best_vs_zero'] = [ss['ncc'], ss['ncc0']]
            d.update(D.blob_f180_window(m, valid, w['voxel_um_9']))
            rec[order] = d
        per[w['id']] = rec
        np.savez_compressed(f'{EVAL}/{tag}/{w["id"]}/win_maps.npz', **maps)
    # text order
    if is_base and not os.path.exists(TEXT_ORDER):
        to = {}
        for scroll in reg['scrolls']:
            items = [(w, per[w['id']]) for w in wins if w['scroll'] == scroll and w['role'] == 'text'
                     and 'forward' in per.get(w['id'], {})]
            if not items:
                continue
            scores = {}
            for order in ('forward', 'reverse'):
                ms, ls = [], []
                for w, _ in items:
                    npz = np.load(f'{EVAL}/{tag}/{w["id"]}/win_maps.npz')
                    v = np.load(f'{WIN}/{w["id"]}/valid.npy')
                    lab = D.ref_labels(np.load(f'{WIN}/{w["id"]}/ref9.npy'), v)
                    ms.append(npz[order][v]); ls.append(lab[v])
                scores[order] = PX.auc(np.concatenate(ms), np.concatenate(ls))
            to[scroll] = dict(auc_forward=scores['forward'], auc_reverse=scores['reverse'],
                              text_order=D.text_order_choice(scores['forward'], scores['reverse']),
                              windows=[w['id'] for w, _ in items])
        jdump(TEXT_ORDER, dict(generated_utc=utc(), rule='text order per scroll = higher pooled AUC of the base '
                               'checkpoint map vs reference labels (ink >= 150, blank <= 100) over the scroll text '
                               'windows; fixed once, before any candidate; never revisited',
                               checkpoint_sha256=ck_sha, scrolls=to))
    tord = json.load(open(TEXT_ORDER))['scrolls']
    # aggregate
    agg = {}
    for scroll in reg['scrolls']:
        if scroll not in tord or tord[scroll]['text_order'] is None:
            continue
        o = tord[scroll]['text_order']
        no = 'reverse' if o == 'forward' else 'forward'
        tw = [w for w in wins if w['scroll'] == scroll and w['role'] == 'text' and o in per.get(w['id'], {})]
        bw = [w for w in wins if w['scroll'] == scroll and w['role'] == 'blank' and o in per.get(w['id'], {})]
        items = []
        for w in tw:
            npz = np.load(f'{EVAL}/{tag}/{w["id"]}/win_maps.npz')
            items.append((npz[o], np.load(f'{WIN}/{w["id"]}/ref9.npy'), np.load(f'{WIN}/{w["id"]}/valid.npy')))
        pooled = D.sigma_eq_pooled(items, tw[0]['voxel_um_9']) if items else None
        # CHANCE (negative control): map of window i against the reference of window i+1 (cyclic, same scroll)
        chance = None
        if len(items) >= 2:
            ch = [(items[i][0], items[(i + 1) % len(items)][1], items[i][2] & items[(i + 1) % len(items)][2])
                  for i in range(len(items))]
            c = D.sigma_eq_pooled(ch, tw[0]['voxel_um_9'])
            chance = dict(sigma_eq_mm=c['sigma_eq_mm'], r_best=c['r_best'])
        per_w = [per[w['id']][o]['sigma_eq_mm'] for w in tw]
        agg[scroll] = dict(text_order=o, n_text=len(tw), n_blank=len(bw),
                           sigma_eq_pooled_mm=pooled['sigma_eq_mm'] if pooled else None,
                           r_pooled=pooled['r_best'] if pooled else None,
                           pooled_table=pooled['table'] if pooled else None,
                           sigma_eq_windows_mm=per_w, chance_pooled=chance,
                           r_windows=[per[w['id']][o]['r_best'] for w in tw],
                           sigma_eq_median_mm=float(np.median(per_w)) if per_w else None,
                           blank_blob_f180_nontext=[per[w['id']][no]['blob_f180'] for w in bw],
                           blank_blob_f180_text=[per[w['id']][o]['blob_f180'] for w in bw])
    blobs = [b for a in agg.values() for b in a['blank_blob_f180_nontext']]
    blob_ok = bool(blobs) and max(blobs) <= D.BLOB_BAR
    fin = D.finalist({s: a['sigma_eq_pooled_mm'] for s, a in agg.items()}, SIGMA_CRIT_MM, blob_ok)
    out = dict(generated_utc=utc(), tag=tag, checkpoint=dict(path=ckpt, sha256=ck_sha), is_base=is_base,
               registry_sha256=sha256(REG), text_order_sha256=sha256(TEXT_ORDER),
               code=dict(evaluate=sha256(__file__), devlib=sha256(os.path.join(HERE, 'devlib.py')),
                         pixel=sha256(os.path.join(REPO, 'src/hercules/metrics/pixel.py'))),
               sigma_crit_mm=SIGMA_CRIT_MM, sigma_crit_source='RULES.md D1-REF-RESULT', finalist_rule=fin,
               blank_constraint=dict(bar=D.BLOB_BAR, max_nontext=max(blobs) if blobs else None, ok=blob_ok),
               per_scroll=agg, per_window=per, wall_seconds=round(time.time() - t_all, 1),
               viewing='no image was written, opened or displayed; numbers only')
    s = jdump(os.path.join(REPO, f'logs/sib/devloop/eval_{tag}.json'), out)
    print('eval', tag, s, json.dumps(dict(per_scroll={k: {kk: vv for kk, vv in v.items() if kk != 'pooled_table'}
                                                      for k, v in agg.items()}, finalist=fin)))


def cmd_calib(ids):
    """Real-data positive control of the metric, no model involved: on every prepared DEV text window the 'model
    map' is the registered reference itself blurred by a KNOWN sigma (0, 0.15, 0.30 mm) and quantised to uint8,
    optionally shifted by 2 px; sigma_eq must return the known sigma (unshifted) and a larger value (shifted)."""
    import cv2
    reg, wins = windows_from_registry()
    out = {}
    for w in wins:
        if w['role'] != 'text' or (ids and w['id'] not in ids):
            continue
        pr = json.load(open(f'{WIN}/{w["id"]}/prep.json'))
        if not pr.get('done') or pr.get('dropped'):
            continue
        ref9 = np.load(f'{WIN}/{w["id"]}/ref9.npy').astype(np.float64)
        valid = np.load(f'{WIN}/{w["id"]}/valid.npy')
        ppm = D.px_per_mm(w['voxel_um_9'])
        rec = {}
        for true_mm in (0.0, 0.15, 0.30):
            m = ref9 if true_mm == 0 else cv2.GaussianBlur(ref9, (0, 0), true_mm * ppm, borderType=cv2.BORDER_REFLECT)
            m8 = np.clip(np.rint(m), 0, 255).astype(np.uint8)
            a = D.sigma_eq_window(m8, ref9, valid, w['voxel_um_9'])
            sh = np.roll(m8, 2, axis=1)
            v2 = valid.copy(); v2[:, :4] = False
            b = D.sigma_eq_window(sh, ref9, v2, w['voxel_um_9'])
            rec[f'{true_mm:.2f}'] = dict(sigma_eq_mm=a['sigma_eq_mm'], r_best=a['r_best'],
                                         shifted2px_sigma_eq_mm=b['sigma_eq_mm'], shifted2px_r_best=b['r_best'])
        out[w['id']] = rec
    ok = all(abs(v[k]['sigma_eq_mm'] - float(k)) <= 0.025 + 1e-9 for v in out.values() for k in v)
    s = jdump(os.path.join(REPO, 'logs/sib/devloop/calib_summary.json'),
              dict(generated_utc=utc(), purpose='real-data positive control of sigma_eq (no model)', all_recovered=ok,
                   evaluate_sha256=sha256(__file__), windows=out))
    print('calib', ok, s)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=['render', 'prep', 'eval', 'calib'])
    ap.add_argument('--ckpt')
    ap.add_argument('--tag')
    ap.add_argument('--base', action='store_true')
    ap.add_argument('--threads', type=int, default=3)
    ap.add_argument('--windows', nargs='*', default=[])
    a = ap.parse_args()
    if a.stage == 'render':
        cmd_render(a.windows)
    elif a.stage == 'prep':
        cmd_prep(a.windows)
    elif a.stage == 'calib':
        cmd_calib(a.windows)
    else:
        cmd_eval(a.ckpt, a.tag, a.base, a.threads, a.windows)
