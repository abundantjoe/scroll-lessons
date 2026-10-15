#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""First Letters screen (RULES.md DECL-FL-1), worker fl-pherc0306b: numeric helpers for pipeline.sh.

Numbers, hashes and file lists only: no image, tile or CT pixel is ever viewed or described.

Subcommands
  listing  OUT_JSON                     anonymous S3 listing of PHerc0306B/ (segments + representations)
  seeds    OUT_JSON                     declared seed list for GrowPatch from the organizer surface prediction
  organizer LISTING_JSON OUT_JSON       pick the 3 largest organizer tifxyz segments (if any)
  accept   SEGDIR SELFCROSS_JSON OUT_JSON   acceptance record of one grown segment (0 transverse, >= 16 cm^2)
  tiles    SEG RENDER_ZARR PRED_FWD PRED_REV OUTDIR SOURCE   2 x 2 cm u8 tiles + manifest.json
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import os
import sys
import time

import numpy as np

BUCKET = 'vesuvius-challenge-open-data'
SCROLL = 'PHerc0306B'
VOL = 'PHerc0306B/volumes/20250521133212-8.640um-1.2m-116keV-masked.zarr'
PRED = ('PHerc0306B/representations/predictions/surfaces/'
        '20250521133212-surface-20260413222639-surface-m7-L0-th0.2.zarr')
NGRID = ('PHerc0306B/representations/predictions/surfaces/'
         '20250521133212-surface-20260413222639-surface-m7-L0-th0.2.normal-grids')
VOXEL_UM = 8.64
TILE_MM = 20.0
OUT_SIDE = 1068
MIN_VALID = 0.50
MIN_AREA_CM2 = 16.0
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def s3():
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    return boto3.client('s3', config=Config(signature_version=UNSIGNED, retries={'max_attempts': 8}))


def ls_all(cli, prefix, delimiter=None):
    kw = dict(Bucket=BUCKET, Prefix=prefix)
    if delimiter:
        kw['Delimiter'] = delimiter
    pre, obj = [], []
    while True:
        r = cli.list_objects_v2(**kw)
        pre += [c['Prefix'] for c in r.get('CommonPrefixes', [])]
        obj += [{'key': o['Key'], 'size': o['Size'], 'etag': o.get('ETag', '').strip('"'),
                 'last_modified': o['LastModified'].isoformat()} for o in r.get('Contents', [])]
        if not r.get('IsTruncated'):
            return pre, obj
        kw['ContinuationToken'] = r['NextContinuationToken']


def dump(obj, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(obj, f, indent=1, sort_keys=False)
        f.write('\n')
    os.replace(tmp, path)


# ----------------------------------------------------------------------------------------------- listing
def cmd_listing(out):
    cli = s3()
    top, top_obj = ls_all(cli, f'{SCROLL}/', '/')
    rec = {'provenance': PROV, 'utc': utc(), 'bucket': BUCKET, 'scroll': SCROLL, 'anonymous': True,
           'top_prefixes': top, 'top_objects': top_obj}
    # every key under segments/ (tifxyz meta.json + x.tif are what matter) and the representations tree
    seg_pre, seg_obj = ls_all(cli, f'{SCROLL}/segments/')
    rec['segments_object_count'] = len(seg_obj)
    rec['segments_objects'] = [o for o in seg_obj if o['key'].endswith(('meta.json', '/x.tif', '/y.tif', '/z.tif'))]
    tifxyz = sorted({o['key'].rsplit('/', 1)[0] for o in seg_obj
                     if o['key'].endswith('/meta.json') and '.tifxyz' in o['key']}
                    | {o['key'].rsplit('/', 1)[0] for o in seg_obj if o['key'].endswith('/x.tif')})
    rec['organizer_tifxyz_dirs'] = tifxyz
    rp, _ = ls_all(cli, f'{SCROLL}/representations/predictions/surfaces/', '/')
    rec['surface_predictions'] = rp
    rec['source'] = 'organizer' if tifxyz else 'auto'
    dump(rec, out)
    print(rec['source'], len(tifxyz))


# ------------------------------------------------------------------------------------------ zarr fetch
def zarr_meta(cli, root, level):
    za = json.loads(cli.get_object(Bucket=BUCKET, Key=f'{root}/{level}/.zarray')['Body'].read())
    return za


def fetch_chunk(cli, root, level, za, cz, cy, cx):
    import numcodecs
    sep = za.get('dimension_separator', '.')
    key = f'{root}/{level}/' + sep.join(str(i) for i in (cz, cy, cx))
    try:
        raw = cli.get_object(Bucket=BUCKET, Key=key)['Body'].read()
    except cli.exceptions.NoSuchKey:
        return None
    comp = za.get('compressor')
    if comp:
        raw = numcodecs.get_codec(comp).decode(raw)
    return np.frombuffer(raw, dtype=np.dtype(za['dtype'])).reshape(za['chunks'])


def read_level(cli, root, level):
    za = zarr_meta(cli, root, level)
    shp, ch = za['shape'], za['chunks']
    arr = np.zeros(shp, dtype=np.dtype(za['dtype']))
    n = [math.ceil(s / c) for s, c in zip(shp, ch)]
    got = 0
    for cz in range(n[0]):
        for cy in range(n[1]):
            for cx in range(n[2]):
                b = fetch_chunk(cli, root, level, za, cz, cy, cx)
                if b is None:
                    continue
                got += 1
                z0, y0, x0 = cz * ch[0], cy * ch[1], cx * ch[2]
                sl = arr[z0:z0 + ch[0], y0:y0 + ch[1], x0:x0 + ch[2]]
                sl[...] = b[:sl.shape[0], :sl.shape[1], :sl.shape[2]]
    return arr, za, got


# --------------------------------------------------------------------------------------------- seeds
# Declared before any growth: 8 candidates, z fractions 0.35 / 0.65 of the predicted-surface z extent, 8 angles
# (interleaved so the first 4 cover both heights and all 4 quadrants), radius = 0.5 x the wedge's 95th-percentile
# outer radius (mid radius). Growth runs in this order and stops at 4 accepted segments.
SEED_PLAN = [(0.35, 0), (0.65, 135), (0.35, 180), (0.65, 315), (0.35, 90), (0.65, 225), (0.35, 270), (0.65, 45)]
WEDGE_DEG = 15.0
RADIUS_FRAC = 0.5
SLAB = 2          # level-5 slices either side


def cmd_seeds(out):
    cli = s3()
    zat = json.loads(cli.get_object(Bucket=BUCKET, Key=f'{PRED}/.zattrs')['Body'].read())
    ds = {d['path']: d['coordinateTransformations'][0]['scale'] for d in zat['multiscales'][0]['datasets']}
    lvl = '5'
    scale = ds[lvl]
    assert scale[0] == scale[1] == scale[2], scale
    f = int(round(scale[0]))
    lo, za5, nchunks = read_level(cli, PRED, lvl)
    za0 = zarr_meta(cli, PRED, '0')
    pos = lo > 0
    zs = np.nonzero(pos.any(axis=(1, 2)))[0]
    zmin, zmax = int(zs.min()), int(zs.max())
    seeds = []
    for k, (zf, ang) in enumerate(SEED_PLAN):
        z5 = int(round(zmin + zf * (zmax - zmin)))
        slab = pos[max(z5 - SLAB, 0):z5 + SLAB + 1].any(axis=0)
        yy, xx = np.nonzero(slab)
        cy, cx = float(np.median(yy)), float(np.median(xx))
        r = np.hypot(yy - cy, xx - cx)
        th = np.degrees(np.arctan2(yy - cy, xx - cx)) % 360.0
        d = np.abs((th - ang + 180.0) % 360.0 - 180.0)
        w = d <= WEDGE_DEG
        rec = {'k': k, 'z_frac': zf, 'angle_deg': ang, 'z5': z5, 'center_yx5': [cy, cx],
               'wedge_points': int(w.sum())}
        if w.sum() < 10:
            rec['status'] = 'no_prediction_in_wedge'
            seeds.append(rec)
            continue
        rout = float(np.percentile(r[w], 95))
        target = RADIUS_FRAC * rout
        # prediction voxel of this slice (not the slab) in the wedge nearest the target radius
        y1, x1 = np.nonzero(pos[z5])
        r1 = np.hypot(y1 - cy, x1 - cx)
        t1 = np.degrees(np.arctan2(y1 - cy, x1 - cx)) % 360.0
        w1 = np.abs((t1 - ang + 180.0) % 360.0 - 180.0) <= WEDGE_DEG
        if not w1.any():
            rec['status'] = 'no_prediction_in_slice_wedge'
            seeds.append(rec)
            continue
        i = np.argmin(np.where(w1, np.abs(r1 - target), np.inf))
        p5 = (z5, int(y1[i]), int(x1[i]))
        rec.update({'r_out5_p95': rout, 'r_target5': target, 'seed5_zyx': list(p5), 'r_seed5': float(r1[i])})
        # refine at level 0: nearest voxel >= 128 inside the level-0 chunk holding the up-scaled point
        c0 = [min(p5[j] * f + f // 2, za0['shape'][j] - 1) for j in range(3)]
        ch = za0['chunks']
        cid = [c0[j] // ch[j] for j in range(3)]
        blk = fetch_chunk(cli, PRED, '0', za0, *cid)
        if blk is None or not (blk >= 128).any():
            rec['status'] = 'no_level0_voxel_ge128_in_chunk'
            rec['level0_chunk'] = cid
            seeds.append(rec)
            continue
        zz, yy0, xx0 = np.nonzero(blk >= 128)
        loc = [c0[j] - cid[j] * ch[j] for j in range(3)]
        dd = (zz - loc[0]) ** 2 + (yy0 - loc[1]) ** 2 + (xx0 - loc[2]) ** 2
        j = int(np.argmin(dd))
        s0 = [int(zz[j] + cid[0] * ch[0]), int(yy0[j] + cid[1] * ch[1]), int(xx0[j] + cid[2] * ch[2])]
        rec.update({'status': 'ok', 'seed0_zyx': s0, 'seed0_xyz': [s0[2], s0[1], s0[0]],
                    'seed0_value': int(blk[zz[j], yy0[j], xx0[j]]), 'refine_dist_vox': float(math.sqrt(dd[j])),
                    'r_seed0_vox': float(math.hypot(s0[1] - cy * f, s0[2] - cx * f)),
                    'r_out0_p95_vox': rout * f})
        seeds.append(rec)
    res = {'provenance': PROV, 'utc': utc(), 'decl': 'RULES.md DECL-FL-1 item 1 (auto-grown segments)',
           'prediction': f's3://{BUCKET}/{PRED}/', 'level_used': lvl, 'level_scale': f,
           'level_shape': za5['shape'], 'level_chunks_present': nchunks, 'z_extent5': [zmin, zmax],
           'plan': {'seed_plan': SEED_PLAN, 'wedge_deg': WEDGE_DEG, 'radius_frac': RADIUS_FRAC, 'slab': SLAB,
                    'center': 'median of predicted voxels in the slab', 'r_out': '95th pct radius in wedge',
                    'refine': 'nearest level-0 voxel >= 128 in the level-0 chunk of the up-scaled point',
                    'order': 'grow in list order; stop at 4 accepted'},
           'seeds': seeds}
    dump(res, out)
    print(sum(s['status'] == 'ok' for s in seeds), 'ok seeds')


# ------------------------------------------------------------------------------------------ organizer
def cmd_organizer(listing, out):
    L = json.load(open(listing))
    cli = s3()
    cands = []
    for d in L['organizer_tifxyz_dirs']:
        area = None
        try:
            m = json.loads(cli.get_object(Bucket=BUCKET, Key=d + '/meta.json')['Body'].read())
            area = m.get('area_cm2')
        except Exception:
            m = None
        xs = [o['size'] for o in L['segments_objects'] if o['key'] == d + '/x.tif']
        cands.append({'dir': d, 'area_cm2': area, 'x_tif_bytes': xs[0] if xs else None})
    key = lambda c: (c['area_cm2'] if c['area_cm2'] is not None else -1, c['x_tif_bytes'] or 0)
    cands.sort(key=key, reverse=True)
    dump({'provenance': PROV, 'utc': utc(), 'rule': '3 largest by meta.json area_cm2 (x.tif bytes tie-break)',
          'candidates': cands, 'chosen': cands[:3]}, out)


# --------------------------------------------------------------------------------------------- accept
def cmd_accept(segdir, selfcross, out):
    meta = json.load(open(os.path.join(segdir, 'meta.json')))
    sc = json.load(open(selfcross))
    census = sc.get('census', [])
    transverse = int(sum(int(c.get('transverse', 0)) for c in census))
    area = float(meta.get('area_cm2', float('nan')))
    shas = {}
    for fn in sorted(os.listdir(segdir)):
        p = os.path.join(segdir, fn)
        if os.path.isfile(p):
            shas[fn] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    ok = transverse == 0 and area >= MIN_AREA_CM2
    rec = {'provenance': PROV, 'utc': utc(), 'area_cm2': area, 'transverse_self_intersections': transverse,
           'coplanar': int(sum(int(c.get('coplanar', 0)) for c in census)),
           'grazing': int(sum(int(c.get('grazing', 0)) for c in census)),
           'grid_rows': sc.get('grid_rows'), 'grid_cols': sc.get('grid_cols'),
           'rule': f'accept iff transverse == 0 and area_cm2 >= {MIN_AREA_CM2}', 'accepted': ok,
           'files_sha256': shas}
    dump(rec, out)
    print('ACCEPT' if ok else 'REJECT', area, transverse)


# ---------------------------------------------------------------------------------------------- tiles
def png_bytes(img_u8):
    from PIL import Image
    buf = io.BytesIO()
    Image.fromarray(img_u8, mode='L').save(buf, format='PNG', optimize=False)
    return buf.getvalue()


def cmd_tiles(seg, render_zarr, pred_fwd, pred_rev, outdir, source):
    import cv2
    import tifffile
    import zarr
    g = zarr.open(render_zarr, mode='r')
    arr = g['0'] if hasattr(g, 'keys') and '0' in g else g
    n, H, W = arr.shape
    # valid = mesh-valid render pixels: any of the 31 slices non-zero (the renderer writes 0 off-mesh)
    valid = np.zeros((H, W), dtype=bool)
    step = 1024
    for y in range(0, H, step):
        valid[y:y + step] = (np.asarray(arr[:, y:y + step, :]) != 0).any(axis=0)
    preds = {}
    for name, p in (('fwd', pred_fwd), ('rev', pred_rev)):
        a = np.squeeze(np.asarray(tifffile.imread(p)))
        assert a.dtype == np.uint8, a.dtype
        assert a.shape == (H, W), (a.shape, H, W)
        preds[name] = np.where(valid, a, 0).astype(np.uint8)
    T = int(round(TILE_MM * 1000.0 / VOXEL_UM))          # 2315 px at 8.64 um
    ppm = OUT_SIDE / (T * VOXEL_UM / 1000.0)
    tdir = os.path.join(outdir, 'tiles')
    os.makedirs(tdir, exist_ok=True)
    items = []
    for r in range(H // T):
        for c in range(W // T):
            y0, x0 = r * T, c * T
            vf = float(valid[y0:y0 + T, x0:x0 + T].mean())
            if vf < MIN_VALID:
                continue
            for d, a in preds.items():
                t = cv2.resize(a[y0:y0 + T, x0:x0 + T], (OUT_SIDE, OUT_SIDE), interpolation=cv2.INTER_AREA)
                v = cv2.resize(valid[y0:y0 + T, x0:x0 + T].astype(np.uint8), (OUT_SIDE, OUT_SIDE),
                               interpolation=cv2.INTER_NEAREST).astype(bool)
                b = png_bytes(t)
                fn = f'{seg}_r{r:02d}_c{c:02d}_{d}.png'
                with open(os.path.join(tdir, fn), 'wb') as f:
                    f.write(b)
                nv = int(v.sum())
                items.append({'segment': seg, 'r': r, 'c': c, 'direction': d, 'file': f'tiles/{fn}',
                              'png_sha256': hashlib.sha256(b).hexdigest(), 'valid_fraction': round(vf, 6),
                              'px_per_mm': round(ppm, 6), 'source': source,
                              'canvas_yx': [y0, x0], 'canvas_side_px': T,
                              'ink_score': (round(float((t[v] >= 128).mean()), 6) if nv else None)})
    man = {'provenance': PROV, 'utc': utc(), 'decl': 'RULES.md DECL-FL-1', 'scroll': SCROLL, 'segment': seg,
           'source': source, 'voxel_um': VOXEL_UM, 'tile_mm': TILE_MM, 'tile_canvas_px': T, 'out_side_px': OUT_SIDE,
           'px_per_mm': round(ppm, 6), 'min_valid_fraction': MIN_VALID, 'canvas_hw': [H, W], 'render_slices': n,
           'prediction': 'official infer.py u8 (clip(p*255) truncated), 0 outside mesh-valid, INTER_AREA to 1068 px',
           'valid_rule': 'render pixel non-zero in any of the 31 slices',
           'grid': 'non-overlapping 2 x 2 cm grid from canvas origin (0, 0); full tiles only',
           'ink_score_rule': 'fraction of >= 128 among valid px of the 1068 px tile (DECL-FL-1 item 2)',
           'pred_sha256': {k: hashlib.sha256(open(p, 'rb').read()).hexdigest()
                           for k, p in (('fwd', pred_fwd), ('rev', pred_rev))},
           'n_tiles': len(items), 'tiles': items}
    dump(man, os.path.join(outdir, 'manifest.json'))
    print(len(items), 'tiles')


if __name__ == '__main__':
    a = sys.argv[1:]
    {'listing': lambda: cmd_listing(a[1]), 'seeds': lambda: cmd_seeds(a[1]),
     'organizer': lambda: cmd_organizer(a[1], a[2]), 'accept': lambda: cmd_accept(a[1], a[2], a[3]),
     'tiles': lambda: cmd_tiles(*a[1:7])}[a[0]]()
