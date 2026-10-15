#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""fl-pilot helpers (First Letters screen, eligible 9 um volumes). Numbers, hashes and file lists only:
no tile, map or CT image is opened, displayed or described.
  inventory OUT.json            anonymous S3 listing of every eligible volume folder (segments/tifxyz, representations,
                                renders, ink predictions) with sizes
  select INV.json OUT.json      up to 3 volumes with organizer tifxyz (MAY first, then JULY), 2 largest segments each
  prep SCROLL SEG MESHKEY WORK  download the tifxyz, write crop.json (mesh-valid bbox on the render canvas, capped)
  tiles WORK PRED.tif OUTDIR TAG   2x2 cm tiles, u8, INTER_AREA -> 1068 px, PNG, keep valid_fraction >= 0.5
"""
import hashlib, json, os, sys, time
import boto3
from botocore import UNSIGNED
from botocore.config import Config

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
B = 'vesuvius-challenge-open-data'
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
MAX_MPX = float(os.environ.get('FLP_MAX_MPX', '40'))   # CPU budget cap per segment render (canvas megapixels)
OUT_SIDE = 1068
s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED, retries={'max_attempts': 8, 'mode': 'adaptive'}))


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def ls(prefix, delim=True, max_pages=None):
    kw = dict(Bucket=B, Prefix=prefix)
    if delim:
        kw['Delimiter'] = '/'
    P, O, pages, trunc = [], [], 0, False
    while True:
        r = s3.list_objects_v2(**kw)
        P += [c['Prefix'] for c in r.get('CommonPrefixes', [])]
        O += [(o['Key'], o['Size'], o['LastModified'].strftime('%Y-%m-%dT%H:%M:%SZ')) for o in r.get('Contents', [])]
        pages += 1
        if not r.get('IsTruncated'):
            break
        if max_pages and pages >= max_pages:
            trunc = True
            break
        kw['ContinuationToken'] = r['NextContinuationToken']
    return P, O, trunc


def du(prefix, max_pages=40):
    _, O, trunc = ls(prefix, delim=False, max_pages=max_pages)
    return {'objects': len(O), 'bytes': sum(o[1] for o in O), 'complete': not trunc,
            'last_modified_max': max((o[2] for o in O), default=None)}


def walk(prefix, depth, out):
    """Tree to `depth` levels; zarr / normal-grid / tifxyz / tifs leaves are summarised with du()."""
    P, O, _ = ls(prefix)
    for k, sz, lm in O:
        out.append({'key': k, 'kind': 'object', 'bytes': sz, 'last_modified': lm})
    for p in P:
        name = p.rstrip('/').split('/')[-1]
        leaf = name.endswith(('.zarr', '.tifxyz', '.tifs', '.normal-grids')) or 'normal-grids' in name
        if leaf or depth <= 1:
            kind = ('tifxyz' if name.endswith('.tifxyz') else 'zarr' if name.endswith('.zarr')
                    else 'normal_grids' if 'normal-grids' in name else 'tifs' if name.endswith('.tifs') else 'dir')
            ent = {'key': p, 'kind': kind}
            if kind == 'normal_grids':
                ent['size'] = 'see eligible_products.json normal_grid_bytes (790k objects, not re-listed)'
            else:
                ent.update(du(p))
            if kind == 'tifxyz':
                ent['files'] = [o[0].split('/')[-1] for o in ls(p)[1]]
            out.append(ent)
            if not leaf and depth <= 1 and kind == 'dir':
                pass
        else:
            walk(p, depth - 1, out)


def classify(key):
    k = key.lower()
    if '.tifxyz' in k or '/mesh/' in k:
        return 'segment_mesh'
    if 'surface-m7' in k or 'normal-grid' in k or 'surface' in k and 'prediction' in k:
        return 'surface_prediction'
    if 'ink' in k:
        return 'ink_prediction'
    if 'surface-volumes' in k or 'render' in k or '/layers' in k:
        return 'render'
    if '/volumes/' in k:
        return 'volume'
    return 'other'


def cmd_inventory(out):
    cat = json.load(open(os.path.join(REPO, 'data/catalogue/eligible_products.json')))
    vols = []
    for v in cat['volumes']:
        sc = v['scroll']
        ents = []
        P, O, _ = ls(sc + '/')
        for k, sz, lm in O:
            ents.append({'key': k, 'kind': 'object', 'bytes': sz, 'last_modified': lm})
        for p in P:
            top = p.rstrip('/').split('/')[-1]
            if top == 'volumes':
                for q in ls(p)[0]:
                    ents.append({'key': q, 'kind': 'zarr', 'size': 'volume zarr (sizes in eligible_products.json levels)'})
            else:
                walk(p, 4, ents)
        for e in ents:
            e['category'] = classify(e['key'])
        tif = [e for e in ents if e['kind'] == 'tifxyz']
        vols.append({'scroll': sc, 'volume_id': v['volume_id'], 'protocol': v['protocol'],
                     'voxel_um': v['expected_voxel_um'], 'volume_zarr': v['volume_zarr'],
                     'n_tifxyz': len(tif), 'n_tifxyz_organized': sum('/segments/raw/' not in e['key'] for e in tif),
                     'category_bytes': {c: sum(e.get('bytes', 0) or 0 for e in ents if e['category'] == c)
                                        for c in sorted({e['category'] for e in ents})},
                     'entries': ents})
        print(sc, len(ents), 'tifxyz', len(tif), flush=True)
    res = {'provenance': PROV, 'generated_utc': utc(), 'bucket': B, 'n_volumes': len(vols),
           'note': 'eligible_products.json lists %d volumes (brief says 22); all listed volumes inventoried' % len(vols),
           'volumes_with_tifxyz': [v['scroll'] for v in vols if v['n_tifxyz']], 'volumes': vols}
    json.dump(res, open(out, 'w'), indent=1)


def seg_area(meshkey):
    """(area_cm2 from meta.json if present, meta) ."""
    try:
        m = json.loads(s3.get_object(Bucket=B, Key=meshkey + 'meta.json')['Body'].read())
    except Exception:
        m = {}
    a = m.get('area_cm2') or (m.get('area_vx2') and None)
    return a, m


def cmd_select(inv, out):
    I = json.load(open(inv))
    order = sorted(I['volumes'], key=lambda v: (v['protocol'] != 'MAY', -v['n_tifxyz_organized'], -v['n_tifxyz']))
    sel = []
    for v in order:
        tif = [e for e in v['entries'] if e['kind'] == 'tifxyz']
        org = [e for e in tif if '/segments/raw/' not in e['key']]
        cand = org or tif
        if not cand or len(sel) >= 3:
            continue
        rows = []
        for e in cand:
            a, m = seg_area(e['key'])
            rows.append({'mesh_key': e['key'], 'segment': e['key'].split('/segments/')[1].split('/')[0] if '/segments/' in e['key'] else e['key'],
                         'area_cm2_meta': a, 'mesh_bytes': e.get('bytes'), 'organized': '/segments/raw/' not in e['key'],
                         'meta_scale': m.get('scale')})
        rows.sort(key=lambda r: (-(r['area_cm2_meta'] or 0), -(r['mesh_bytes'] or 0)))
        sel.append({'scroll': v['scroll'], 'protocol': v['protocol'], 'voxel_um': v['voxel_um'],
                    'volume_zarr': v['volume_zarr'], 'rank_rule': 'meta.json area_cm2 desc, then mesh bytes desc',
                    'candidates': rows, 'segments': rows[:2]})
    json.dump({'provenance': PROV, 'generated_utc': utc(), 'selection': sel}, open(out, 'w'), indent=1)
    for s in sel:
        for r in s['segments']:
            print(s['scroll'], r['segment'], r['mesh_key'], s['voxel_um'], s['volume_zarr'])


def cmd_prep(scroll, seg, meshkey, work):
    import numpy as np, tifffile
    md = os.path.join(work, 'mesh', meshkey.rstrip('/').split('/')[-1])
    os.makedirs(md, exist_ok=True)
    for k, sz, _ in ls(meshkey)[1]:
        f = os.path.join(md, k.split('/')[-1])
        if not (os.path.exists(f) and os.path.getsize(f) == sz):
            s3.download_file(B, k, f)
    meta = json.load(open(os.path.join(md, 'meta.json')))
    sc = meta['scale']
    s = float(sc[0] if isinstance(sc, list) else sc)
    x = tifffile.imread(os.path.join(md, 'x.tif'))
    valid = x != -1
    if os.path.exists(os.path.join(md, 'mask.tif')):
        mk = tifffile.imread(os.path.join(md, 'mask.tif'))
        if mk.shape[:2] == valid.shape:
            valid &= (mk[..., 0] if mk.ndim == 3 else mk) > 0
    ys, xs = np.nonzero(valid)
    gy0, gy1, gx0, gx1 = int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1
    cx0, cy0 = int(np.floor(gx0 / s)), int(np.floor(gy0 / s))
    cw, ch = int(np.ceil(gx1 / s)) - cx0, int(np.ceil(gy1 / s)) - cy0
    capped = False
    if cw * ch > MAX_MPX * 1e6:   # centred window on the valid bbox, same aspect
        f = (MAX_MPX * 1e6 / (cw * ch)) ** 0.5
        nw, nh = int(cw * f), int(ch * f)
        cx0 += (cw - nw) // 2; cy0 += (ch - nh) // 2; cw, ch = nw, nh; capped = True
    np.save(os.path.join(work, 'grid_valid.npy'), valid)
    crop = {'scroll': scroll, 'segment': seg, 'mesh_key': meshkey, 'mesh_dir': md, 'meta_scale': s,
            'grid_shape': list(valid.shape), 'grid_valid_points': int(valid.sum()),
            'grid_valid_bbox_yx': [gy0, gy1, gx0, gx1], 'crop_xywh': [cx0, cy0, cw, ch], 'capped_to_max_mpx': capped,
            'max_mpx': MAX_MPX, 'canvas_rule': 'canvas px = grid px / meta scale; manual crop, no --auto-crop',
            'x_tif_sha256': hashlib.sha256(open(os.path.join(md, 'x.tif'), 'rb').read()).hexdigest()}
    json.dump(crop, open(os.path.join(work, 'crop.json'), 'w'), indent=1)
    print(' '.join(str(v) for v in crop['crop_xywh']))


def cmd_tiles(work, pred, outdir, tag, voxel_um):
    import numpy as np, tifffile, cv2
    sys.path.insert(0, os.path.join(REPO, 'src'))
    from hercules.display.builder import png_bytes
    crop = json.load(open(os.path.join(work, 'crop.json')))
    cx0, cy0, cw, ch = crop['crop_xywh']
    s = crop['meta_scale']
    p = tifffile.imread(pred)
    p = np.squeeze(p)
    info = {'pred_dtype': str(p.dtype), 'pred_shape': list(p.shape)}
    if p.dtype == np.uint8:
        u8 = p
    elif p.dtype == np.uint16:
        u8 = (p // 257).astype(np.uint8)
    else:
        pf = p.astype(np.float32)
        mx = float(np.nanmax(pf)) if pf.size else 0.0
        u8 = np.clip(np.nan_to_num(pf) * (255.0 if mx <= 1.0 + 1e-6 else 1.0), 0, 255).astype(np.uint8)
    H, W = u8.shape
    info['size_matches_crop'] = [H, W] == [ch, cw]
    # mesh-valid mask on the canvas: nearest grid point of canvas pixel centre (gy = (cy0+y+0.5)*s)
    gv = np.load(os.path.join(work, 'grid_valid.npy'))
    gy = np.clip(np.floor((cy0 + np.arange(H) + 0.5) * s).astype(int), 0, gv.shape[0] - 1)
    gx = np.clip(np.floor((cx0 + np.arange(W) + 0.5) * s).astype(int), 0, gv.shape[1] - 1)
    valid = gv[gy][:, gx]
    u8 = np.where(valid, u8, 0).astype(np.uint8)
    px_mm = 1000.0 / voxel_um
    T = int(round(20.0 * px_mm))
    os.makedirs(outdir, exist_ok=True)
    rows, kept = [], 0
    for r in range(H // T + (H % T > 0)):
        for c in range(W // T + (W % T > 0)):
            t = np.zeros((T, T), np.uint8); m = np.zeros((T, T), bool)
            a = u8[r * T:(r + 1) * T, c * T:(c + 1) * T]; b = valid[r * T:(r + 1) * T, c * T:(c + 1) * T]
            t[:a.shape[0], :a.shape[1]] = a; m[:b.shape[0], :b.shape[1]] = b
            vf = float(m.mean())
            ent = {'segment': crop['segment'], 'direction': tag, 'r': r, 'c': c, 'valid_fraction': round(vf, 4),
                   'px_per_mm': round(px_mm, 4), 'tile_src_px': T, 'canvas_x0': cx0 + c * T, 'canvas_y0': cy0 + r * T}
            if vf >= 0.5:
                png = png_bytes(cv2.resize(t, (OUT_SIDE, OUT_SIDE), interpolation=cv2.INTER_AREA))
                fn = f'{tag}_r{r:02d}_c{c:02d}.png'
                open(os.path.join(outdir, fn), 'wb').write(png)
                ent.update(file=fn, png_sha256=hashlib.sha256(png).hexdigest(), display_px_per_mm=round(OUT_SIDE / 20.0, 3))
                kept += 1
            rows.append(ent)
    mf = os.path.join(outdir, 'manifest.json')
    M = json.load(open(mf)) if os.path.exists(mf) else {'provenance': PROV, 'scroll': crop['scroll'], 'segment': crop['segment'],
        'display_spec': 'P4: u8 = clip(p*255) truncated, 0 outside mesh-valid, 2x2 cm tiles, cv2.INTER_AREA -> 1068 px, PNG (hercules.display.builder.png_bytes); keep valid_fraction >= 0.5',
        'chain': 'C2-NT: vc_render_tifxyz -n 31 --flip-normals (villa 41701aa) -> vesuvius.ink_detection.inference.infer ink_9um step-075000 (sha256 e635558a...9cab), --direction both, no TTA, CPU',
        'crop': crop, 'runs': {}}
    M['runs'][tag] = {'generated_utc': utc(), 'pred_file': os.path.basename(pred),
                      'pred_sha256': hashlib.sha256(open(pred, 'rb').read()).hexdigest(), **info,
                      'tiles_total': len(rows), 'tiles_kept': kept, 'tiles': rows}
    json.dump(M, open(mf, 'w'), indent=1)
    print(tag, 'kept', kept, 'of', len(rows))


if __name__ == '__main__':
    c, a = sys.argv[1], sys.argv[2:]
    {'inventory': cmd_inventory, 'select': cmd_select, 'prep': cmd_prep,
     'tiles': lambda w, p, o, t, v: cmd_tiles(w, p, o, t, float(v))}[c](*a)
