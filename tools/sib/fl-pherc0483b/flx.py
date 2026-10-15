#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""fl-pherc0483b helpers (DECL-FL-1 First Letters screen, PHerc0483B). Numbers, hashes and file lists only:
no tile, map or CT image is opened, displayed or described. Tile/prep code follows tools/sib/fl-pilot/flp.py
(branch claude/gifted-bell-gavnl5-sib-fl-pilot @ f65025e) so both screens share one display spec.
  listing OUT.json                  anonymous S3 listing of PHerc0483B/ (tifxyz present? surface prediction?)
  seeds OUT.json N                  N seeds at mid radius on the organizer surface prediction (surface-m7, th0.2):
                                    scroll axis + radius from level 4 (16x, nearest-downsampled), snapped to a
                                    level-0 voxel >= 128 (the value GrowPatch's own seed search requires)
  gate SEGDIR SELFCROSS.json OUT.json   area (meta area_cm2 + own quad-area recount) and self-intersection gate
  prep SEG MESHDIR WORK             crop.json (mesh-valid bbox on the render canvas, capped) + grid_valid.npy
  tiles WORK PRED.tif OUTDIR TAG VOX SOURCE   2x2 cm tiles, u8, INTER_AREA -> 1068 px, PNG, keep valid >= 0.5
"""
import hashlib, json, math, os, sys, time
import numpy as np
import requests

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
HTTP = 'https://vesuvius-challenge-open-data.s3.amazonaws.com'
SC = 'PHerc0483B'
SURF = SC + '/representations/predictions/surfaces/20251124083638-surface-20260413222639-surface-m7-L0-th0.2.zarr'
MAX_MPX = float(os.environ.get('FLX_MAX_MPX', '40'))
MIN_AREA_CM2 = 16.0
OUT_SIDE = 1068
S = requests.Session()
S.verify = os.environ.get('REQUESTS_CA_BUNDLE', True)


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def get(url, ok404=False):
    for i in range(6):
        try:
            r = S.get(url, timeout=120)
            if r.status_code == 404 and ok404:
                return None
            r.raise_for_status()
            return r.content
        except Exception:
            if i == 5:
                raise
            time.sleep(2 ** i)


def ls(prefix):
    """Delimited listing: (prefixes, [(key, size)])."""
    import re
    P, O, tok = [], [], None
    while True:
        u = f'{HTTP}/?list-type=2&delimiter=/&prefix={prefix}' + (f'&continuation-token={requests.utils.quote(tok)}' if tok else '')
        x = get(u).decode()
        P += [p for p in re.findall(r'<CommonPrefixes><Prefix>([^<]*)</Prefix>', x)]
        O += [(k, int(s)) for k, s in re.findall(r'<Key>([^<]*)</Key>.*?<Size>(\d+)</Size>', x)]
        m = re.search(r'<NextContinuationToken>([^<]*)<', x)
        if not m:
            return P, O
        tok = m.group(1)


def cmd_listing(out):
    ents, tif, stack = [], [], [SC + '/']
    while stack:
        p = stack.pop()
        P, O = ls(p)
        ents += [{'key': k, 'bytes': s} for k, s in O]
        for q in P:
            n = q.rstrip('/').split('/')[-1]
            if n.endswith('.tifxyz') or '/segments/' in q and q.count('/') == 3:
                tif.append(q)
            if n.endswith(('.zarr', '.normal-grids')) or n.isdigit():
                ents.append({'key': q, 'kind': 'store (not recursed)'})
            else:
                stack.append(q)
    seg_dirs = sorted({e['key'].rsplit('/', 1)[0] + '/' for e in ents if e['key'].endswith('/x.tif')})
    res = {'provenance': PROV, 'generated_utc': utc(), 'root': f's3://vesuvius-challenge-open-data/{SC}/ (anonymous)',
           'tifxyz_segments': seg_dirs, 'n_tifxyz': len(seg_dirs),
           'surface_prediction': SURF + '/' if any(e['key'].startswith(SURF) for e in ents) else None,
           'entries': sorted(ents, key=lambda e: e['key'])}
    json.dump(res, open(out, 'w'), indent=1)
    print('tifxyz', len(seg_dirs), 'surface', res['surface_prediction'])


def read_level(level):
    import numcodecs
    za = json.loads(get(f'{HTTP}/{SURF}/{level}/.zarray'))
    shp, ch = za['shape'], za['chunks']
    codec = numcodecs.get_codec(za['compressor']) if za['compressor'] else None
    a = np.zeros(shp, np.uint8)
    n = [math.ceil(s / c) for s, c in zip(shp, ch)]
    for iz in range(n[0]):
        for iy in range(n[1]):
            for ix in range(n[2]):
                b = get(f'{HTTP}/{SURF}/{level}/{iz}/{iy}/{ix}', ok404=True)
                if b is None:
                    continue
                c = np.frombuffer(codec.decode(b) if codec else b, np.uint8).reshape(ch)
                z0, y0, x0 = iz * ch[0], iy * ch[1], ix * ch[2]
                sz = a[z0:z0 + ch[0], y0:y0 + ch[1], x0:x0 + ch[2]].shape
                a[z0:z0 + sz[0], y0:y0 + sz[1], x0:x0 + sz[2]] = c[:sz[0], :sz[1], :sz[2]]
    return a, za


def l0_chunk(iz, iy, ix, za0):
    import numcodecs
    b = get(f'{HTTP}/{SURF}/0/{iz}/{iy}/{ix}', ok404=True)
    if b is None:
        return None
    codec = numcodecs.get_codec(za0['compressor']) if za0['compressor'] else None
    return np.frombuffer(codec.decode(b) if codec else b, np.uint8).reshape(za0['chunks'])


def cmd_seeds(out, n):
    n = int(n)
    L, F = 4, 16
    a, za = read_level(L)
    za0 = json.loads(get(f'{HTTP}/{SURF}/0/.zarray'))
    surf = a >= 128
    per_z = surf.reshape(surf.shape[0], -1).sum(1)
    zs = np.nonzero(per_z >= max(50, 0.05 * per_z.max()))[0]
    z_lo, z_hi = int(zs.min()), int(zs.max())
    # seed plan: two heights x two opposite angles, the pairs rotated 90 deg (spread over the mid-radius shell)
    plan = [(0.40, 45.0), (0.40, 225.0), (0.60, 135.0), (0.60, 315.0), (0.30, 90.0), (0.70, 270.0), (0.50, 0.0), (0.50, 180.0)][:n]
    seeds = []
    for k, (zf, ang) in enumerate(plan):
        z = int(round(z_lo + zf * (z_hi - z_lo)))
        # axis: centroid of surface voxels in a +-4 slice slab; radius: p98 of their distance to it
        slab = surf[max(0, z - 4):z + 5]
        _, yy, xx = np.nonzero(slab)
        cy, cx = float(yy.mean()), float(xx.mean())
        rr = np.hypot(yy - cy, xx - cx)
        r98 = float(np.percentile(rr, 98))
        rmid = 0.5 * r98
        ty, tx = cy + rmid * math.sin(math.radians(ang)), cx + rmid * math.cos(math.radians(ang))
        ys, xs = np.nonzero(surf[z])
        d = np.hypot(ys - ty, xs - tx)
        order = np.argsort(d)[:40]
        rec = {'k': k, 'name': f'auto{k:02d}', 'z_frac': zf, 'angle_deg': ang, 'level': L, 'level_factor': F,
               'z_L4': z, 'axis_yx_L4': [round(cy, 2), round(cx, 2)], 'r98_L4': round(r98, 2), 'rmid_L4': round(rmid, 2),
               'target_yx_L4': [round(ty, 2), round(tx, 2)], 'seed_xyz_L0': None}
        for j in order:
            y4, x4 = int(ys[j]), int(xs[j])
            c0 = np.array([z * F + F // 2, y4 * F + F // 2, x4 * F + F // 2])
            idx = [int(c0[i] // za0['chunks'][i]) for i in range(3)]
            ch = l0_chunk(*idx, za0)
            if ch is None:
                continue
            pz, py, px = np.nonzero(ch >= 128)
            if not len(pz):
                continue
            g = np.stack([pz, py, px], 1) + np.array(idx) * np.array(za0['chunks'])
            dd = np.linalg.norm(g - c0, axis=1)
            b = int(np.argmin(dd))
            if dd[b] > 2 * F:
                continue
            gz, gy, gx = (int(v) for v in g[b])
            rec.update(seed_xyz_L0=[gx, gy, gz], seed_value=int(ch[gz % za0['chunks'][0], gy % za0['chunks'][1], gx % za0['chunks'][2]]),
                       snap_dist_L0=round(float(dd[b]), 2), l4_candidate_rank=int(np.where(order == j)[0][0]),
                       radius_L0=round(float(math.hypot(gy - cy * F, gx - cx * F)), 1), r98_L0=round(r98 * F, 1),
                       radius_frac=round(float(math.hypot(gy - cy * F, gx - cx * F)) / (r98 * F), 3))
            break
        seeds.append(rec)
        print(rec['name'], rec['seed_xyz_L0'], rec.get('radius_frac'), flush=True)
    res = {'provenance': PROV, 'generated_utc': utc(), 'surface_prediction': f's3://vesuvius-challenge-open-data/{SURF}/',
           'rule': 'axis = centroid of level-4 surface voxels (>=128) in a 9-slice slab; mid radius = 0.5 x p98 radius; '
                   'target at (z_frac of the surface z-range, angle); nearest level-4 surface voxel, snapped to the nearest '
                   'level-0 voxel >= 128 within 32 vx (GrowPatch seed search uses v >= 128)',
           'surface_z_range_L4': [z_lo, z_hi], 'level4_shape': za['shape'],
           'level4_sha256': hashlib.sha256(a.tobytes()).hexdigest(), 'seeds': seeds}
    json.dump(res, open(out, 'w'), indent=1)


def quad_area_cm2(sd, vox_um):
    import tifffile
    x, y, z = (tifffile.imread(os.path.join(sd, f'{c}.tif')).astype(np.float64) for c in 'xyz')
    P = np.stack([x, y, z], -1)
    v = (x != -1) & np.isfinite(x)
    q = v[:-1, :-1] & v[1:, :-1] & v[:-1, 1:] & v[1:, 1:]
    a, b, c, d = P[:-1, :-1], P[:-1, 1:], P[1:, 1:], P[1:, :-1]
    A = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=-1) + 0.5 * np.linalg.norm(np.cross(c - a, d - a), axis=-1)
    return float(A[q].sum() * (vox_um * 1e-4) ** 2), int(q.sum()), list(x.shape)


def cmd_gate(sd, sx, out, vox_um='8.64'):
    meta = json.load(open(os.path.join(sd, 'meta.json')))
    own, nq, shp = quad_area_cm2(sd, float(vox_um))
    R = json.load(open(sx)) if os.path.exists(sx) and os.path.getsize(sx) else None
    tr = co = gr = None
    if R:
        tr = sum(d.get('transverse', 0) for d in R.get('census', []))
        co = sum(d.get('coplanar', 0) for d in R.get('census', []))
        gr = sum(d.get('grazing', 0) for d in R.get('census', []))
    area = meta.get('area_cm2')
    reasons = []
    if R is None:
        reasons.append('no selfcross report')
    elif tr or co:
        reasons.append(f'self-intersections transverse={tr} coplanar={co}')
    if (area or 0) < MIN_AREA_CM2 or own < MIN_AREA_CM2:
        reasons.append(f'area meta={area} own={own:.3f} < {MIN_AREA_CM2}')
    g = {'provenance': PROV, 'generated_utc': utc(), 'segment_dir': sd, 'grid_shape': shp, 'valid_quads': nq,
         'area_cm2_meta': area, 'area_cm2_quad_recount': round(own, 4), 'meta_scale': meta.get('scale'),
         'max_gen': meta.get('max_gen'), 'selfcross': {'transverse': tr, 'coplanar': co, 'grazing': gr,
         'tool': 'vc_tifxyz_selfcross (villa 41701aa), defaults: exclude 1, maxedge 60, cell 40'},
         'rule': 'keep iff transverse == 0 and coplanar == 0 and area_cm2 (meta and quad recount) >= 16',
         'keep': not reasons, 'reject_reasons': reasons}
    json.dump(g, open(out, 'w'), indent=1)
    print('keep' if g['keep'] else 'reject', reasons, 'area', area, round(own, 3))


def cmd_prep(seg, md, work):
    import tifffile
    meta = json.load(open(os.path.join(md, 'meta.json')))
    sc = meta['scale']
    s = float(sc[0] if isinstance(sc, list) else sc)
    x = tifffile.imread(os.path.join(md, 'x.tif'))
    valid = (x != -1) & np.isfinite(x)
    if os.path.exists(os.path.join(md, 'mask.tif')):
        mk = tifffile.imread(os.path.join(md, 'mask.tif'))
        if mk.shape[:2] == valid.shape:
            valid &= (mk[..., 0] if mk.ndim == 3 else mk) > 0
    ys, xs = np.nonzero(valid)
    gy0, gy1, gx0, gx1 = int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1
    cx0, cy0 = int(np.floor(gx0 / s)), int(np.floor(gy0 / s))
    cw, ch = int(np.ceil(gx1 / s)) - cx0, int(np.ceil(gy1 / s)) - cy0
    capped = False
    if cw * ch > MAX_MPX * 1e6:
        f = (MAX_MPX * 1e6 / (cw * ch)) ** 0.5
        nw, nh = int(cw * f), int(ch * f)
        cx0 += (cw - nw) // 2; cy0 += (ch - nh) // 2; cw, ch = nw, nh; capped = True
    os.makedirs(work, exist_ok=True)
    np.save(os.path.join(work, 'grid_valid.npy'), valid)
    crop = {'scroll': SC, 'segment': seg, 'mesh_dir': md, 'meta_scale': s, 'grid_shape': list(valid.shape),
            'grid_valid_points': int(valid.sum()), 'grid_valid_bbox_yx': [gy0, gy1, gx0, gx1],
            'crop_xywh': [cx0, cy0, cw, ch], 'capped_to_max_mpx': capped, 'max_mpx': MAX_MPX,
            'canvas_rule': 'canvas px = grid px / meta scale; manual crop, no --auto-crop',
            'x_tif_sha256': hashlib.sha256(open(os.path.join(md, 'x.tif'), 'rb').read()).hexdigest()}
    json.dump(crop, open(os.path.join(work, 'crop.json'), 'w'), indent=1)
    print(' '.join(str(v) for v in crop['crop_xywh']))


def cmd_tiles(work, pred, outdir, tag, voxel_um, source):
    import tifffile, cv2
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
        pf = p.astype(np.float32)
        mx = float(np.nanmax(pf)) if pf.size else 0.0
        u8 = np.clip(np.nan_to_num(pf) * (255.0 if mx <= 1.0 + 1e-6 else 1.0), 0, 255).astype(np.uint8)
    H, W = u8.shape
    info['size_matches_crop'] = [H, W] == [ch, cw]
    gv = np.load(os.path.join(work, 'grid_valid.npy'))
    gy = np.clip(np.floor((cy0 + np.arange(H) + 0.5) * s).astype(int), 0, gv.shape[0] - 1)
    gx = np.clip(np.floor((cx0 + np.arange(W) + 0.5) * s).astype(int), 0, gv.shape[1] - 1)
    valid = gv[gy][:, gx]
    u8 = np.where(valid, u8, 0).astype(np.uint8)
    src_px_mm = 1000.0 / voxel_um
    T = int(round(20.0 * src_px_mm))
    os.makedirs(outdir, exist_ok=True)
    rows, kept = [], 0
    for r in range(H // T + (H % T > 0)):
        for c in range(W // T + (W % T > 0)):
            t = np.zeros((T, T), np.uint8); m = np.zeros((T, T), bool)
            a = u8[r * T:(r + 1) * T, c * T:(c + 1) * T]; b = valid[r * T:(r + 1) * T, c * T:(c + 1) * T]
            t[:a.shape[0], :a.shape[1]] = a; m[:b.shape[0], :b.shape[1]] = b
            vf = float(m.mean())
            ent = {'segment': crop['segment'], 'source': source, 'direction': tag, 'r': r, 'c': c,
                   'valid_fraction': round(vf, 4), 'px_per_mm': round(OUT_SIDE / 20.0, 3),
                   'src_px_per_mm': round(src_px_mm, 4), 'tile_src_px': T,
                   'canvas_x0': cx0 + c * T, 'canvas_y0': cy0 + r * T}
            if vf >= 0.5:
                png = png_bytes(cv2.resize(t, (OUT_SIDE, OUT_SIDE), interpolation=cv2.INTER_AREA))
                fn = f'{tag}_r{r:02d}_c{c:02d}.png'
                open(os.path.join(outdir, fn), 'wb').write(png)
                ent.update(file=fn, png_sha256=hashlib.sha256(png).hexdigest())
                kept += 1
            rows.append(ent)
    mf = os.path.join(outdir, 'manifest.json')
    M = json.load(open(mf)) if os.path.exists(mf) else {
        'provenance': PROV, 'scroll': SC, 'segment': crop['segment'], 'source': source,
        'display_spec': 'DECL-FL-1: u8 prediction (clip(p*255) if float), 0 outside mesh-valid, 2x2 cm tiles, '
                        'cv2.INTER_AREA -> 1068 px (53.4 px/mm), PNG (hercules.display.builder.png_bytes); keep valid_fraction >= 0.5',
        'chain': 'C2-NT: vc_render_tifxyz -n 31 --flip-normals (villa 41701aa) -> vesuvius.ink_detection.inference.infer '
                 'ink_9um step-075000 (sha256 e635558a...9cab), --direction both, no TTA, CPU',
        'crop': crop, 'runs': {}}
    M['runs'][tag] = {'generated_utc': utc(), 'pred_file': os.path.basename(pred),
                      'pred_sha256': hashlib.sha256(open(pred, 'rb').read()).hexdigest(), **info,
                      'tiles_total': len(rows), 'tiles_kept': kept, 'tiles': rows}
    json.dump(M, open(mf, 'w'), indent=1)
    print(tag, 'kept', kept, 'of', len(rows))


if __name__ == '__main__':
    c, a = sys.argv[1], sys.argv[2:]
    {'listing': cmd_listing, 'seeds': cmd_seeds, 'gate': cmd_gate, 'prep': cmd_prep, 'tiles': cmd_tiles}[c](*a)
