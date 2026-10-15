#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""fl-pherc0490a helpers (DECL-FL-1 First Letters screen, PHerc0490A). Numbers, hashes and file lists only:
no tile, map or CT image is opened, displayed or described.
  listing OUT.json                 anonymous S3 listing of s3://vesuvius-challenge-open-data/PHerc0490A/ ;
                                   mode = organizer (tifxyz segments exist, 3 largest) or auto (GrowPatch seeds)
  seeds LISTING.json OUT.json      auto mode: seed points spread over mid radius, on surface-prediction voxels >= 128
  gate SEGDIR SELFCROSS.json OUT   area (cm^2, from x/y/z grid quads) + transverse self-crossing count -> keep/drop
  fetch MESHKEY DIR                download one organizer tifxyz
  prep SEG MESHDIR WORK            crop.json (mesh-valid bbox on the render canvas, capped) + grid_valid.npy
  tiles WORK PRED.tif OUTDIR TAG SOURCE   2x2 cm tiles, u8, INTER_AREA -> 1068 px, PNG, keep valid_fraction >= 0.5
"""
import hashlib, json, os, sys, time
import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
B = 'vesuvius-challenge-open-data'
HTTP = 'https://vesuvius-challenge-open-data.s3.amazonaws.com/'
SCROLL = 'PHerc0490A'
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
VOX_UM = 8.64
MAX_MPX = float(os.environ.get('FL_MAX_MPX', '40'))
MIN_AREA_CM2 = 16.0
OUT_SIDE = 1068


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def s3c():
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    return boto3.client('s3', config=Config(signature_version=UNSIGNED, retries={'max_attempts': 8, 'mode': 'adaptive'}))


def ls_all(s3, prefix):
    kw = dict(Bucket=B, Prefix=prefix)
    O = []
    while True:
        r = s3.list_objects_v2(**kw)
        O += [(o['Key'], o['Size'], o['LastModified'].strftime('%Y-%m-%dT%H:%M:%SZ')) for o in r.get('Contents', [])]
        if not r.get('IsTruncated'):
            return O
        kw['ContinuationToken'] = r['NextContinuationToken']


def cmd_listing(out):
    s3 = s3c()
    cat = json.load(open(os.path.join(REPO, 'data/catalogue/eligible_products.json')))
    v = [v for v in cat['volumes'] if v['scroll'] == SCROLL][0]
    prefixes = {}
    tif = {}
    surf = set()
    n_obj = 0
    # full listing except the volume and normal-grid trees (sizes only, keys not kept)
    for top in ('segments/', 'representations/', 'photos/'):
        for k, sz, lm in ls_all(s3, SCROLL + '/' + top):
            n_obj += 1
            parts = k.split('/')
            key3 = '/'.join(parts[:4]) + '/'
            e = prefixes.setdefault(key3, {'objects': 0, 'bytes': 0})
            e['objects'] += 1; e['bytes'] += sz
            if '.tifxyz/' in k or (top == 'segments/' and k.endswith(('/x.tif', '/meta.json'))):
                d = k.rsplit('/', 1)[0] + '/'
                t = tif.setdefault(d, {'mesh_key': d, 'files': [], 'bytes': 0})
                t['files'].append(k.rsplit('/', 1)[1]); t['bytes'] += sz
            if 'surface-m7' in k and '.zarr/' in k:
                surf.add(k.split('.zarr/')[0] + '.zarr/')
    tif = {d: t for d, t in tif.items() if 'x.tif' in t['files'] and 'meta.json' in t['files']}
    rows = []
    for d, t in tif.items():
        try:
            m = json.loads(s3.get_object(Bucket=B, Key=d + 'meta.json')['Body'].read())
        except Exception:
            m = {}
        rows.append({**t, 'segment': d.rstrip('/').split('/')[-1], 'area_cm2_meta': m.get('area_cm2'),
                     'organized': '/segments/raw/' not in d})
    rows.sort(key=lambda r: (-(r['area_cm2_meta'] or 0), -r['bytes']))
    mode = 'organizer' if rows else 'auto'
    res = {'provenance': PROV, 'generated_utc': utc(), 'scroll': SCROLL, 'bucket': B, 'volume_id': v['volume_id'],
           'volume_zarr': v['volume_zarr'], 'voxel_um': v['expected_voxel_um'], 'objects_listed': n_obj,
           'prefixes': prefixes, 'tifxyz_segments': rows, 'surface_m7_zarrs': sorted(surf), 'mode': mode,
           'selected_organizer': rows[:3],
           'rule': 'organizer tifxyz -> 3 largest (meta area_cm2 desc, then bytes); else auto-grow up to 4 (GrowPatch on surface-m7)'}
    json.dump(res, open(out, 'w'), indent=1)
    print(mode, len(rows), len(surf))


# ---------- zarr chunk reads over anonymous HTTPS (numbers only) ----------
_ZA = {}


def zarray(base, lvl):
    import requests
    k = (base, lvl)
    if k not in _ZA:
        _ZA[k] = requests.get(HTTP + base + f'{lvl}/.zarray', timeout=60).json()
    return _ZA[k]


def chunk(base, lvl, cz, cy, cx):
    import requests, numcodecs
    za = zarray(base, lvl)
    C = za['chunks']
    sep = za.get('dimension_separator', '.')
    url = HTTP + base + f'{lvl}/' + sep.join(map(str, (cz, cy, cx)))
    for i in range(6):
        try:
            r = requests.get(url, timeout=120)
            break
        except Exception:
            time.sleep(2 ** i)
    if r.status_code in (403, 404):
        return np.full(C, za.get('fill_value') or 0, np.uint8)
    r.raise_for_status()
    buf = r.content
    if za.get('compressor'):
        buf = numcodecs.get_codec(za['compressor']).decode(buf)
    return np.frombuffer(buf, np.uint8).reshape(C)


def zslice(base, lvl, z):
    za = zarray(base, lvl); Z, Y, X = za['shape']; C = za['chunks']
    out = np.zeros((Y, X), np.uint8)
    cz = z // C[0]
    for cy in range(-(-Y // C[1])):
        for cx in range(-(-X // C[2])):
            a = chunk(base, lvl, cz, cy, cx)[z - cz * C[0]]
            y0, x0 = cy * C[1], cx * C[2]
            out[y0:y0 + C[1], x0:x0 + C[2]] = a[:min(C[1], Y - y0), :min(C[2], X - x0)]
    return out


def cmd_seeds(listing, out):
    L = json.load(open(listing))
    base = L['surface_m7_zarrs'][0].replace('s3://' + B + '/', '')
    thr = 128
    # z extent of the prediction from the coarsest level
    lv = 5
    za5 = zarray(base, lv); Z5, Y5, X5 = za5['shape']; C5 = za5['chunks']
    fz = np.zeros(Z5, np.int64)
    for cz in range(-(-Z5 // C5[0])):
        for cy in range(-(-Y5 // C5[1])):
            for cx in range(-(-X5 // C5[2])):
                a = chunk(base, lv, cz, cy, cx)
                n = (a >= thr).sum(axis=(1, 2))
                z0 = cz * C5[0]; m = min(C5[0], Z5 - z0)
                fz[z0:z0 + m] += n[:m]
    f5 = 2 ** lv
    cdf = np.cumsum(fz) / max(1, fz.sum())
    zlo, zhi = int(np.searchsorted(cdf, 0.05)) * f5, int(np.searchsorted(cdf, 0.95)) * f5
    lv3 = 3; f3 = 2 ** lv3
    plan = [(0, 0.40), (90, 0.60), (180, 0.40), (270, 0.60), (45, 0.60), (135, 0.40), (225, 0.60), (315, 0.40)]
    slabs, seeds = {}, []
    for k, (ang, zf) in enumerate(plan):
        z0 = int(zlo + zf * (zhi - zlo))
        z3 = z0 // f3
        if z3 not in slabs:
            S = zslice(base, lv3, z3)
            fg = S >= thr
            ys, xs = np.nonzero(fg)
            cy_, cx_ = float(ys.mean()), float(xs.mean())
            r = np.hypot(ys - cy_, xs - cx_)
            slabs[z3] = dict(ys=ys, xs=xs, r=r, cy=cy_, cx=cx_, rmax=float(np.percentile(r, 98)), n=int(fg.sum()))
        s = slabs[z3]
        rt = 0.5 * s['rmax']
        ty, tx = s['cy'] + rt * np.sin(np.radians(ang)), s['cx'] + rt * np.cos(np.radians(ang))
        band = np.abs(s['r'] - rt) <= 0.1 * s['rmax']
        cand = np.nonzero(band)[0]
        i = cand[np.argmin(np.hypot(s['ys'][cand] - ty, s['xs'][cand] - tx))]
        p0 = np.array([z3 * f3 + f3 // 2, s['ys'][i] * f3 + f3 // 2, s['xs'][i] * f3 + f3 // 2])
        # refine at level 0: nearest voxel >= thr inside the level-0 chunk holding p0
        za0 = zarray(base, 0); C0 = za0['chunks']
        cid = p0 // np.array(C0)
        a = chunk(base, 0, *cid)
        o = cid * np.array(C0)
        zz, yy, xx = np.nonzero(a >= thr)
        refined = False
        v0 = None
        if len(zz):
            d = np.hypot(np.hypot(zz + o[0] - p0[0], yy + o[1] - p0[1]), xx + o[2] - p0[2])
            j = int(np.argmin(d))
            if d[j] <= 32:
                p0 = np.array([zz[j] + o[0], yy[j] + o[1], xx[j] + o[2]]); refined = True
                v0 = int(a[zz[j], yy[j], xx[j]])
        seeds.append({'k': k, 'angle_deg': ang, 'z_frac': zf, 'seed_xyz': [int(p0[2]), int(p0[1]), int(p0[0])],
                      'level0_value': v0, 'refined_at_level0': refined,
                      'radius_frac_of_r98': round(float(np.hypot(p0[1] / f3 - s['cy'], p0[2] / f3 - s['cx']) / s['rmax']), 4),
                      'slice_level3_z': z3, 'slice_center_yx_level0': [round(s['cy'] * f3, 1), round(s['cx'] * f3, 1)],
                      'slice_r98_level0_vox': round(s['rmax'] * f3, 1), 'slice_fg_px_level3': s['n']})
        print(k, seeds[-1]['seed_xyz'], refined, v0, flush=True)
    json.dump({'provenance': PROV, 'generated_utc': utc(), 'surface_zarr': base, 'threshold_u8': thr,
               'z_extent_level0': [zlo, zhi], 'z_extent_rule': 'level-5 per-z count of voxels >= 128, 5th..95th percentile',
               'rule': 'per target z: level-3 slice, centroid of voxels >= 128, r98 = 98th pct radius; target = 0.5*r98 at angle; '
                       'nearest fg pixel within |r-0.5 r98| <= 0.1 r98; refined to nearest level-0 voxel >= 128 within 32 vox (same chunk)',
               'attempt_order': 'seeds tried in k order until 4 segments pass the gate or all 8 are tried',
               'seeds': seeds}, open(out, 'w'), indent=1)


def read_grid(md):
    import tifffile
    x = tifffile.imread(os.path.join(md, 'x.tif')).astype(np.float64)
    y = tifffile.imread(os.path.join(md, 'y.tif')).astype(np.float64)
    z = tifffile.imread(os.path.join(md, 'z.tif')).astype(np.float64)
    valid = (x != -1) & (z > 0) & np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    mp = os.path.join(md, 'mask.tif')
    if os.path.exists(mp):
        mk = tifffile.imread(mp)
        if mk.shape[:2] == valid.shape:
            valid &= (mk[..., 0] if mk.ndim == 3 else mk) > 0
    return x, y, z, valid


def cmd_gate(md, selfcross, out):
    x, y, z, v = read_grid(md)
    P = np.stack([x, y, z], -1)
    q = v[:-1, :-1] & v[1:, :-1] & v[:-1, 1:] & v[1:, 1:]
    a = P[:-1, :-1]; b = P[:-1, 1:]; c = P[1:, :-1]; d = P[1:, 1:]
    t1 = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=-1)
    t2 = 0.5 * np.linalg.norm(np.cross(b - d, c - d), axis=-1)
    area_vx2 = float(np.where(q, t1 + t2, 0).sum())
    area_cm2 = area_vx2 * (VOX_UM * 1e-4) ** 2
    meta = json.load(open(os.path.join(md, 'meta.json')))
    tv = None; sc = {}
    if os.path.exists(selfcross):
        R = json.load(open(selfcross))
        cen = R.get('census', [])
        cen = cen if isinstance(cen, list) else list(cen.values())
        sc = {f"diag{e.get('diagonal')}": {k: e.get(k) for k in ('triangles', 'transverse', 'coplanar', 'grazing',
              'quads_dropped_for_edge_length')} for e in cen}
        tv = int(sum(int(e.get('transverse', 0)) for e in cen)) if cen else None
    keep = tv == 0 and area_cm2 >= MIN_AREA_CM2
    res = {'provenance': PROV, 'generated_utc': utc(), 'segment': os.path.basename(md.rstrip('/')),
           'grid_shape': list(v.shape), 'valid_points': int(v.sum()), 'valid_quads': int(q.sum()),
           'area_cm2_grid_quads': round(area_cm2, 3), 'area_rule': 'sum of 2-triangle quad areas over fully valid quads, x (8.64 um)^2',
           'area_cm2_meta': meta.get('area_cm2'), 'meta_scale': meta.get('scale'),
           'selfcross_transverse_total': tv, 'selfcross': sc, 'min_area_cm2': MIN_AREA_CM2,
           'keep': bool(keep), 'reason': 'ok' if keep else ('selfcross missing' if tv is None else
                                                          f'transverse={tv}' if tv else f'area {area_cm2:.2f} < {MIN_AREA_CM2}')}
    json.dump(res, open(out, 'w'), indent=1)
    print('KEEP' if keep else 'DROP', res['reason'], round(area_cm2, 2))


def cmd_prep(seg, md, work):
    os.makedirs(work, exist_ok=True)
    meta = json.load(open(os.path.join(md, 'meta.json')))
    sc = meta['scale']
    s = float(sc[0] if isinstance(sc, list) else sc)
    _, _, _, valid = read_grid(md)
    ys, xs = np.nonzero(valid)
    gy0, gy1, gx0, gx1 = int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1
    cx0, cy0 = int(np.floor(gx0 / s)), int(np.floor(gy0 / s))
    cw, ch = int(np.ceil(gx1 / s)) - cx0, int(np.ceil(gy1 / s)) - cy0
    capped = False
    if cw * ch > MAX_MPX * 1e6:
        f = (MAX_MPX * 1e6 / (cw * ch)) ** 0.5
        nw, nh = int(cw * f), int(ch * f)
        cx0 += (cw - nw) // 2; cy0 += (ch - nh) // 2; cw, ch = nw, nh; capped = True
    np.save(os.path.join(work, 'grid_valid.npy'), valid)
    crop = {'segment': seg, 'mesh_dir': md, 'meta_scale': s, 'grid_shape': list(valid.shape),
            'grid_valid_points': int(valid.sum()), 'grid_valid_bbox_yx': [gy0, gy1, gx0, gx1],
            'crop_xywh': [cx0, cy0, cw, ch], 'capped_to_max_mpx': capped, 'max_mpx': MAX_MPX,
            'canvas_rule': 'canvas px = grid px / meta scale; manual crop, no --auto-crop',
            'x_tif_sha256': hashlib.sha256(open(os.path.join(md, 'x.tif'), 'rb').read()).hexdigest()}
    json.dump(crop, open(os.path.join(work, 'crop.json'), 'w'), indent=1)
    print(' '.join(str(v) for v in crop['crop_xywh']))


def cmd_tiles(work, pred, outdir, tag, source):
    import tifffile, cv2
    sys.path.insert(0, os.path.join(REPO, 'src'))
    from hercules.display.builder import png_bytes
    crop = json.load(open(os.path.join(work, 'crop.json')))
    cx0, cy0, cw, ch = crop['crop_xywh']
    s = crop['meta_scale']
    p = np.squeeze(tifffile.imread(pred))
    info = {'pred_dtype': str(p.dtype), 'pred_shape': list(p.shape)}
    if p.dtype == np.uint8:
        u8 = p
    elif p.dtype == np.uint16:
        u8 = (p // 257).astype(np.uint8)
    else:
        pf = np.nan_to_num(p.astype(np.float32))
        mx = float(pf.max()) if pf.size else 0.0
        u8 = np.clip(pf * (255.0 if mx <= 1.0 + 1e-6 else 1.0), 0, 255).astype(np.uint8)
    H, W = u8.shape
    info['size_matches_crop'] = [H, W] == [ch, cw]
    gv = np.load(os.path.join(work, 'grid_valid.npy'))
    gy = np.clip(np.floor((cy0 + np.arange(H) + 0.5) * s).astype(int), 0, gv.shape[0] - 1)
    gx = np.clip(np.floor((cx0 + np.arange(W) + 0.5) * s).astype(int), 0, gv.shape[1] - 1)
    valid = gv[gy][:, gx]
    u8 = np.where(valid, u8, 0).astype(np.uint8)
    src_px_mm = 1000.0 / VOX_UM
    T = int(round(20.0 * src_px_mm))
    os.makedirs(outdir, exist_ok=True)
    rows, kept = [], 0
    for r in range(-(-H // T)):
        for c in range(-(-W // T)):
            t = np.zeros((T, T), np.uint8); m = np.zeros((T, T), bool)
            a = u8[r * T:(r + 1) * T, c * T:(c + 1) * T]; b = valid[r * T:(r + 1) * T, c * T:(c + 1) * T]
            t[:a.shape[0], :a.shape[1]] = a; m[:b.shape[0], :b.shape[1]] = b
            vf = float(m.mean())
            ent = {'segment': crop['segment'], 'direction': tag, 'r': r, 'c': c, 'valid_fraction': round(vf, 4),
                   'px_per_mm': round(OUT_SIDE / 20.0, 3), 'src_px_per_mm': round(src_px_mm, 4), 'tile_src_px': T,
                   'source': source, 'canvas_x0': cx0 + c * T, 'canvas_y0': cy0 + r * T}
            if vf >= 0.5:
                png = png_bytes(cv2.resize(t, (OUT_SIDE, OUT_SIDE), interpolation=cv2.INTER_AREA))
                fn = f'{tag}_r{r:02d}_c{c:02d}.png'
                open(os.path.join(outdir, fn), 'wb').write(png)
                ent.update(file=fn, png_sha256=hashlib.sha256(png).hexdigest())
                kept += 1
            rows.append(ent)
    mf = os.path.join(outdir, 'manifest.json')
    M = json.load(open(mf)) if os.path.exists(mf) else {
        'provenance': PROV, 'scroll': SCROLL, 'segment': crop['segment'], 'source': source, 'decl': 'DECL-FL-1',
        'display_spec': 'u8 = clip(p*255) truncated, 0 outside mesh-valid, 2x2 cm tiles, cv2.INTER_AREA -> 1068 px (53.4 px/mm), PNG (hercules.display.builder.png_bytes); keep valid_fraction >= 0.5',
        'chain': 'C2-NT: vc_render_tifxyz -n 31 --flip-normals (villa 41701aa) -> vesuvius.ink_detection.inference.infer ink_9um step-075000 (sha256 e635558a...9cab), --direction both, no TTA, CPU',
        'crop': crop, 'runs': {}}
    M['runs'][tag] = {'generated_utc': utc(), 'pred_file': os.path.basename(pred),
                      'pred_sha256': hashlib.sha256(open(pred, 'rb').read()).hexdigest(), **info,
                      'tiles_total': len(rows), 'tiles_kept': kept, 'tiles': rows}
    json.dump(M, open(mf, 'w'), indent=1)
    print(tag, 'kept', kept, 'of', len(rows))


def cmd_fetch(meshkey, md):
    s3 = s3c(); os.makedirs(md, exist_ok=True)
    for k, sz, _ in ls_all(s3, meshkey):
        f = os.path.join(md, k.split('/')[-1])
        if '/' not in k[len(meshkey):] and not (os.path.exists(f) and os.path.getsize(f) == sz):
            s3.download_file(B, k, f)


if __name__ == '__main__':
    c, a = sys.argv[1], sys.argv[2:]
    {'listing': cmd_listing, 'seeds': cmd_seeds, 'gate': cmd_gate, 'prep': cmd_prep, 'tiles': cmd_tiles, 'fetch': cmd_fetch}[c](*a)
