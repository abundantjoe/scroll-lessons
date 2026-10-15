#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""fl-pherc0483a helpers (RULES.md DECL-FL-1, First Letters screen of PHerc0483A). Numbers, hashes and file lists
only: no tile, map or CT image is opened, displayed or described. Adapted from tools/sib/fl-pilot/flp.py.
  inventory OUT.json              anonymous S3 listing of PHerc0483A/ (segments, representations) with sizes
  seeds OUT.json                  4 GrowPatch seeds over mid radius, from the organizer surface-m7 prediction
                                  (level 5 for geometry, snapped to the nearest surface voxel at level 0)
  params SEEDS.json K OUT.json    vc_grow_seg_from_seed params for seed K
  gate SEGDIR SELFCROSS.json OUT.json   keep/reject verdict: 0 transverse self-intersections and area >= 16 cm^2
  prep SEGDIR WORK SOURCE         write crop.json (mesh-valid bbox on the render canvas, capped)
  tiles WORK PRED.tif OUTDIR TAG VOXEL_UM   2x2 cm tiles, u8, INTER_AREA -> 1068 px, PNG, keep valid >= 0.5
"""
import hashlib, json, os, sys, time
import boto3
from botocore import UNSIGNED
from botocore.config import Config

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
B = 'vesuvius-challenge-open-data'
SC = 'PHerc0483A'
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
PRED = SC + '/representations/predictions/surfaces/20250521140913-surface-20260413222639-surface-m7-L0-th0.2'
HTTPS = f'https://{B}.s3.amazonaws.com/'
VOXEL_UM = 8.64
MIN_AREA_CM2 = 16.0
GENERATIONS = int(os.environ.get('FL_GENERATIONS', '300'))
MAX_MPX = float(os.environ.get('FL_MAX_MPX', '60'))   # CPU budget cap per segment render (canvas megapixels)
OUT_SIDE = 1068
# Seed layout, fixed before any growth: z fraction of the prediction's z extent, polar angle (deg), r = 0.5 * R_outer
SEED_LAYOUT = [(0.30, 0.0), (0.45, 90.0), (0.55, 180.0), (0.70, 270.0)]
s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED, retries={'max_attempts': 8, 'mode': 'adaptive'}))


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def ls(prefix, delim=True):
    kw = dict(Bucket=B, Prefix=prefix)
    if delim:
        kw['Delimiter'] = '/'
    P, O = [], []
    while True:
        r = s3.list_objects_v2(**kw)
        P += [c['Prefix'] for c in r.get('CommonPrefixes', [])]
        O += [(o['Key'], o['Size']) for o in r.get('Contents', [])]
        if not r.get('IsTruncated'):
            return P, O
        kw['ContinuationToken'] = r['NextContinuationToken']


def cmd_inventory(out):
    top, objs = ls(SC + '/')
    tree = {'top_prefixes': top, 'top_objects': objs}
    segs = []
    for p in top:
        name = p.rstrip('/').split('/')[-1]
        if name in ('segments', 'paths'):
            # every tifxyz dir (has x.tif) below segments/
            _, O = ls(p, delim=False)
            dirs = {}
            for k, sz in O:
                d, f = k.rsplit('/', 1)
                dirs.setdefault(d, {})[f] = sz
            for d, files in sorted(dirs.items()):
                if {'x.tif', 'y.tif', 'z.tif'} <= set(files):
                    segs.append({'dir': d + '/', 'files': files, 'bytes': sum(files.values())})
    for p in top:
        if p.rstrip('/').endswith('representations'):
            tree['representations'] = []
            stack = [p]
            while stack:
                q = stack.pop()
                P, O = ls(q)
                tree['representations'] += [k for k, _ in O]
                for c in P:
                    if c.rstrip('/').endswith(('.zarr', '.normal-grids')):
                        tree['representations'].append(c)
                    else:
                        stack.append(c)
    res = {'provenance': PROV, 'generated_utc': utc(), 'bucket': B, 'scroll': SC, 'listing': tree,
           'organizer_tifxyz_segments': segs, 'n_organizer_tifxyz': len(segs),
           'decision': 'organizer' if segs else 'auto-grow (no organizer tifxyz segment in the bucket)'}
    json.dump(res, open(out, 'w'), indent=1)
    print('organizer tifxyz:', len(segs))


def seg_area_from_meta(key):
    try:
        return json.loads(s3.get_object(Bucket=B, Key=key + 'meta.json')['Body'].read()).get('area_cm2')
    except Exception:
        return None


def cmd_select(inv, out):
    I = json.load(open(inv))
    rows = []
    for s in I['organizer_tifxyz_segments']:
        rows.append({'mesh_key': s['dir'], 'segment': s['dir'].rstrip('/').split('/')[-1],
                     'area_cm2_meta': seg_area_from_meta(s['dir']), 'mesh_bytes': s['bytes']})
    rows.sort(key=lambda r: (-(r['area_cm2_meta'] or 0), -r['mesh_bytes']))
    json.dump({'provenance': PROV, 'generated_utc': utc(), 'rank_rule': 'meta.json area_cm2 desc, then tifxyz bytes desc',
               'candidates': rows, 'segments': rows[:3]}, open(out, 'w'), indent=1)


def download_mesh(key, md):
    os.makedirs(md, exist_ok=True)
    for k, sz in ls(key)[1]:
        f = os.path.join(md, k.split('/')[-1])
        if not (os.path.exists(f) and os.path.getsize(f) == sz):
            s3.download_file(B, k, f)


def cmd_seeds(out):
    import numpy as np, zarr, s3fs
    fs = s3fs.S3FileSystem(anon=True)
    g = zarr.open(s3fs.S3Map(f'{B}/{PRED}.zarr', s3=fs), mode='r')
    a5 = g['5'][:] > 0
    f5 = g['0'].shape[0] / a5.shape[0]
    n = a5.reshape(a5.shape[0], -1).sum(1)
    zs = np.nonzero(n > 50)[0]
    z0, z1 = int(zs.min()), int(zs.max())
    L0 = g['0']
    seeds = []
    for k, (zf, ang) in enumerate(SEED_LAYOUT):
        z = int(round(z0 + zf * (z1 - z0)))
        ys, xs = np.nonzero(a5[z])
        cy, cx = float(ys.mean()), float(xs.mean())
        R = float(np.percentile(np.hypot(ys - cy, xs - cx), 99))
        r = 0.5 * R
        ty, tx = cy + r * np.sin(np.radians(ang)), cx + r * np.cos(np.radians(ang))
        # nearest level-5 surface pixel in this slice
        i = int(np.argmin(np.hypot(ys - ty, xs - tx)))
        py, px = ys[i], xs[i]
        # level-0 snap: nearest voxel == 255 to the level-5 pixel centre inside a 96^3 block
        c0 = np.array([(z + 0.5) * f5, (py + 0.5) * f5, (px + 0.5) * f5])
        h = 48
        lo = np.maximum(c0.astype(int) - h, 0)
        hi = np.minimum(c0.astype(int) + h, np.array(L0.shape))
        blk = L0[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
        vz, vy, vx = np.nonzero(blk >= 128)
        snap = None
        if len(vz):
            d = np.sqrt((vz + lo[0] - c0[0]) ** 2 + (vy + lo[1] - c0[1]) ** 2 + (vx + lo[2] - c0[2]) ** 2)
            j = int(np.argmin(d))
            snap = [int(vx[j] + lo[2]), int(vy[j] + lo[1]), int(vz[j] + lo[0])]
        seeds.append({'k': k, 'z_frac': zf, 'angle_deg': ang, 'l5_z': z, 'l5_centre_yx': [round(cy, 2), round(cx, 2)],
                      'l5_R_outer_p99': round(R, 2), 'r_frac': 0.5, 'l5_target_yx': [round(ty, 2), round(tx, 2)],
                      'l5_snap_yx': [int(py), int(px)], 'l5_snap_offset_px': round(float(np.hypot(py - ty, px - tx)), 2),
                      'seed_xyz_l0': snap, 'l0_snap_dist_vox': None if snap is None else round(float(d[j]), 2),
                      'l0_block_surface_voxels': int(len(vz)),
                      'radius_mm': round(float(np.hypot((py + .5) * f5 - (cy + .5) * f5, (px + .5) * f5 - (cx + .5) * f5)) * VOXEL_UM / 1000, 2),
                      'R_outer_mm': round(R * f5 * VOXEL_UM / 1000, 2)})
        print(k, snap, flush=True)
    json.dump({'provenance': PROV, 'generated_utc': utc(), 'prediction': f's3://{B}/{PRED}.zarr',
               'rule': 'z at fixed fractions of the level-5 z extent with > 50 surface px; polar angle fixed per seed; '
                       'centre = level-5 slice centroid of surface px; R_outer = p99 radius; target r = 0.5 R_outer; '
                       'snap to the nearest level-5 surface px, then to the nearest level-0 voxel >= 128 in a 96^3 block',
               'level5_factor': f5, 'level5_z_extent': [z0, z1], 'layout': SEED_LAYOUT, 'seeds': seeds},
              open(out, 'w'), indent=1)


def cmd_params(seeds, k, out):
    k = int(k)
    p = {'mode': 'seed', 'step_size': 20, 'min_area_cm': MIN_AREA_CM2, 'generations': GENERATIONS, 'thread_limit': 3,
         'voxelsize': VOXEL_UM, 'normal_grid_path': os.environ['FL_NG_DIR'], 'cache_root': os.environ['FL_CACHE']}
    json.dump(p, open(out, 'w'), indent=1)
    s = json.load(open(seeds))['seeds'][k]['seed_xyz_l0']
    print(*(s if s else ['NONE']))


def _count_transverse(rep):
    """Sum of transverse contacts in a vc_tifxyz_selfcross report (robust to layout)."""
    tot = 0
    for d in rep.get('census', []):
        if 'transverse' in d and isinstance(d['transverse'], (int, float)):
            tot += int(d['transverse'])
        elif isinstance(d.get('counts'), dict):
            tot += int(d['counts'].get('transverse', 0))
        else:
            tot += sum(1 for c in d.get('transverse_contacts', []) if str(c.get('verdict', 'TRANSVERSE')).upper().startswith('TRANS'))
    return tot


def cmd_gate(segdir, selfcross, rc, out):
    meta = json.load(open(os.path.join(segdir, 'meta.json')))
    area = meta.get('area_cm2')
    rc = int(rc)
    rep = json.load(open(selfcross)) if os.path.exists(selfcross) else {}
    ntr = _count_transverse(rep) if rep else None
    ok_x = rc == 0 and ntr == 0
    ok_a = area is not None and float(area) >= MIN_AREA_CM2
    v = {'segment': os.path.basename(segdir.rstrip('/')), 'area_cm2': area, 'selfcross_rc': rc,
         'transverse_self_intersections': ntr, 'keep': bool(ok_x and ok_a),
         'rule': '0 non-adjacent transverse self-intersections (vc_tifxyz_selfcross --fail-on-crossing rc 0 and report count 0) '
                 f'and meta area_cm2 >= {MIN_AREA_CM2}',
         'x_tif_sha256': sha(os.path.join(segdir, 'x.tif')), 'generated_utc': utc()}
    json.dump(v, open(out, 'w'), indent=1)
    print('KEEP' if v['keep'] else 'REJECT', area, ntr)


def cmd_prep(segdir, work, source):
    import numpy as np, tifffile
    meta = json.load(open(os.path.join(segdir, 'meta.json')))
    sc = meta['scale']
    s = float(sc[0] if isinstance(sc, list) else sc)
    x = tifffile.imread(os.path.join(segdir, 'x.tif'))
    valid = x != -1
    if os.path.exists(os.path.join(segdir, 'mask.tif')):
        mk = tifffile.imread(os.path.join(segdir, 'mask.tif'))
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
    os.makedirs(work, exist_ok=True)
    np.save(os.path.join(work, 'grid_valid.npy'), valid)
    crop = {'scroll': SC, 'segment': os.path.basename(segdir.rstrip('/')), 'source': source, 'mesh_dir': segdir,
            'meta_scale': s, 'area_cm2_meta': meta.get('area_cm2'), 'grid_shape': list(valid.shape),
            'grid_valid_points': int(valid.sum()), 'grid_valid_bbox_yx': [gy0, gy1, gx0, gx1],
            'crop_xywh': [cx0, cy0, cw, ch], 'capped_to_max_mpx': capped, 'max_mpx': MAX_MPX,
            'canvas_rule': 'canvas px = grid px / meta scale; manual crop, no --auto-crop',
            'x_tif_sha256': sha(os.path.join(segdir, 'x.tif'))}
    json.dump(crop, open(os.path.join(work, 'crop.json'), 'w'), indent=1)
    print(' '.join(str(v) for v in crop['crop_xywh']))


def cmd_tiles(work, pred, outdir, tag, voxel_um):
    import numpy as np, tifffile, cv2
    sys.path.insert(0, os.path.join(REPO, 'src'))
    from hercules.display.builder import png_bytes
    voxel_um = float(voxel_um)
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
    px_mm = 1000.0 / voxel_um
    T = int(round(20.0 * px_mm))
    tdir = os.path.join(outdir, 'tiles')
    os.makedirs(tdir, exist_ok=True)
    rows, kept = [], 0
    for r in range(H // T + (H % T > 0)):
        for c in range(W // T + (W % T > 0)):
            t = np.zeros((T, T), np.uint8); m = np.zeros((T, T), bool)
            a = u8[r * T:(r + 1) * T, c * T:(c + 1) * T]; b = valid[r * T:(r + 1) * T, c * T:(c + 1) * T]
            t[:a.shape[0], :a.shape[1]] = a; m[:b.shape[0], :b.shape[1]] = b
            vf = float(m.mean())
            ent = {'segment': crop['segment'], 'source': crop['source'], 'direction': tag, 'r': r, 'c': c,
                   'valid_fraction': round(vf, 4), 'px_per_mm': round(OUT_SIDE / 20.0, 3),
                   'src_px_per_mm': round(px_mm, 4), 'tile_src_px': T,
                   'canvas_x0': cx0 + c * T, 'canvas_y0': cy0 + r * T}
            if vf >= 0.5:
                png = png_bytes(cv2.resize(t, (OUT_SIDE, OUT_SIDE), interpolation=cv2.INTER_AREA))
                fn = f'{tag}_r{r:02d}_c{c:02d}.png'
                open(os.path.join(tdir, fn), 'wb').write(png)
                ent.update(file=f'tiles/{fn}', png_sha256=hashlib.sha256(png).hexdigest())
                kept += 1
            rows.append(ent)
    mf = os.path.join(outdir, 'manifest.json')
    M = json.load(open(mf)) if os.path.exists(mf) else {
        'provenance': PROV, 'decl': 'RULES.md DECL-FL-1', 'scroll': SC, 'segment': crop['segment'], 'source': crop['source'],
        'display_spec': 'u8 = clip(p*255) truncated (uint8 prediction used as is), 0 outside mesh-valid, 2x2 cm tiles, '
                        'cv2.INTER_AREA -> 1068 px (53.4 px/mm), PNG (hercules.display.builder.png_bytes); keep valid_fraction >= 0.5',
        'chain': 'C2-NT: vc_render_tifxyz -n 31 --flip-normals (villa 41701aa) -> vesuvius.ink_detection.inference.infer '
                 'ink_9um step-075000 (sha256 e635558a...9cab), --direction both, no TTA, CPU',
        'crop': crop, 'runs': {}}
    M['runs'][tag] = {'generated_utc': utc(), 'pred_file': os.path.basename(pred), 'pred_sha256': sha(pred), **info,
                      'tiles_total': len(rows), 'tiles_kept': kept, 'tiles': rows}
    json.dump(M, open(mf, 'w'), indent=1)
    print(tag, 'kept', kept, 'of', len(rows))


if __name__ == '__main__':
    c, a = sys.argv[1], sys.argv[2:]
    {'inventory': cmd_inventory, 'select': cmd_select, 'seeds': cmd_seeds, 'params': cmd_params, 'gate': cmd_gate,
     'prep': cmd_prep, 'tiles': cmd_tiles, 'download': download_mesh}[c](*a)
