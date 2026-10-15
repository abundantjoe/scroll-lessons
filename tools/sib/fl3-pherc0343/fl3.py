#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
# Adapted from tools/sib/fl-pherc0175b/flb.py (branch ...-sib-fl-pherc0175b, commit 0d02bb5) for PASS 3.
"""fl3-pherc0343 helpers (DECL-FL-1 First Letters screen, extra PASS 3, PHerc0343). Numbers, hashes and file lists only:
no tile, map or CT image is opened, displayed or described.
  listing OUT.json                 anonymous S3 listing of PHerc0343/ (organizer tifxyz segments, surface prediction)
  select LIST.json OUT.json        organizer route: tifxyz segments ranked 10-15 by area (PASS 3)
  seeds OUT.json                   auto route: GrowPatch seed candidates in the INNER third of the radius (surface-m7 level 5
                                   for the plan, level 0 to snap each seed onto a voxel >= 128)
  exclude SEEDS.json K SEGROOT     exit 0 if candidate K lies >= 2 mm from every kept segment, else 3
  geom SEGDIR SELFCROSS.json VOX OUT.json   geometry gate record: grid area, meta area, edge-length distortion,
                                   self-crossing census (transverse contacts)
  prep SEGDIR WORK                 crop.json (mesh-valid bbox on the render canvas, capped) + grid_valid.npy
  tiles WORK PRED.tif OUTDIR TAG VOX SOURCE   2x2 cm tiles, u8, INTER_AREA -> 1068 px, PNG, keep valid >= 0.5
"""
import hashlib, json, os, sys, time
import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
B = 'vesuvius-challenge-open-data'
HTTP = 'https://%s.s3.amazonaws.com/' % B
SC = 'PHerc0343'
SURF = SC + '/representations/predictions/surfaces/20250521140437-surface-20260413222639-surface-m7-L0-th0.2'
PASS = 3
RANK_LO, RANK_HI = 10, 15  # 1-based, inclusive
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
MAX_MPX = float(os.environ.get('FLB_MAX_MPX', '40'))
OUT_SIDE = 1068


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def s3c():
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    return boto3.client('s3', config=Config(signature_version=UNSIGNED, retries={'max_attempts': 8, 'mode': 'adaptive'}))


def ls(s3, prefix, delim=True):
    kw = dict(Bucket=B, Prefix=prefix)
    if delim:
        kw['Delimiter'] = '/'
    P, O = [], []
    while True:
        r = s3.list_objects_v2(**kw)
        P += [c['Prefix'] for c in r.get('CommonPrefixes', [])]
        O += [(o['Key'], o['Size'], o['LastModified'].strftime('%Y-%m-%dT%H:%M:%SZ')) for o in r.get('Contents', [])]
        if not r.get('IsTruncated'):
            return P, O
        kw['ContinuationToken'] = r['NextContinuationToken']


def cmd_listing(out):
    s3 = s3c()
    tree, segs = [], []

    def walk(p, depth):
        P, O = ls(s3, p)
        for k, sz, lm in O:
            tree.append({'key': k, 'bytes': sz, 'last_modified': lm})
        for q in P:
            name = q.rstrip('/').split('/')[-1]
            files = None
            if name.endswith(('.zarr', '.normal-grids')) or depth <= 0:
                tree.append({'key': q, 'kind': 'dir (not descended)'})
                continue
            _, fo = ls(s3, q)
            names = [k.split('/')[-1] for k, _, _ in fo]
            if 'x.tif' in names and 'meta.json' in names:
                files = names
                segs.append({'mesh_key': q, 'files': names, 'bytes': sum(s for _, s, _ in fo),
                             'organized': '/segments/raw/' not in q})
                tree.append({'key': q, 'kind': 'tifxyz', 'files': files})
                continue
            tree.append({'key': q, 'kind': 'dir'})
            walk(q, depth - 1)
    walk(SC + '/', 5)
    res = {'provenance': PROV, 'generated_utc': utc(), 'bucket': B, 'scroll': SC,
           'n_tifxyz': len(segs), 'tifxyz': segs,
           'surface_prediction_zarr': [e['key'] for e in tree if e['key'].endswith('surface-m7-L0-th0.2.zarr/')],
           'route': 'organizer' if segs else 'auto', 'tree': tree}
    json.dump(res, open(out, 'w'), indent=1)
    print(res['route'], len(segs))


def cmd_select(lst, out):
    s3 = s3c()
    L = json.load(open(lst))
    rows = []
    for e in L['tifxyz']:
        try:
            m = json.loads(s3.get_object(Bucket=B, Key=e['mesh_key'] + 'meta.json')['Body'].read())
        except Exception:
            m = {}
        rows.append({'mesh_key': e['mesh_key'], 'segment': e['mesh_key'].rstrip('/').split('/')[-1],
                     'area_cm2_meta': m.get('area_cm2'), 'mesh_bytes': e['bytes'], 'organized': e['organized']})
    rows.sort(key=lambda r: (not r['organized'], -(r['area_cm2_meta'] or 0), -(r['mesh_bytes'] or 0)))
    for i, r in enumerate(rows):
        r['rank'] = i + 1
    chosen = rows[RANK_LO - 1:RANK_HI]
    json.dump({'provenance': PROV, 'generated_utc': utc(), 'pass': PASS,
               'rank_rule': 'organized first, meta area_cm2 desc, bytes desc; PASS 3 takes ranks %d-%d' % (RANK_LO, RANK_HI),
               'candidates': rows, 'segments': chosen}, open(out, 'w'), indent=1)
    for r in chosen:
        print(r['segment'], r['mesh_key'])


def fetch_mesh(mesh_key, dst):
    s3 = s3c()
    os.makedirs(dst, exist_ok=True)
    for k, sz, _ in ls(s3, mesh_key)[1]:
        f = os.path.join(dst, k.split('/')[-1])
        if not (os.path.exists(f) and os.path.getsize(f) == sz):
            s3.download_file(B, k, f)


# ---------------------------------------------------------------- zarr v2 (blosc) reader over anonymous HTTPS
def zarr_meta(level):
    import requests
    return requests.get(HTTP + SURF + '.zarr/%d/.zarray' % level, timeout=60).json()


def zarr_chunk(level, cz, cy, cx, meta):
    import requests, numcodecs
    url = HTTP + SURF + '.zarr/%d/%d/%d/%d' % (level, cz, cy, cx)
    for i in range(6):
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 404:
                return np.zeros(meta['chunks'], np.uint8)
            r.raise_for_status()
            return np.frombuffer(numcodecs.get_codec(meta['compressor']).decode(r.content), np.uint8).reshape(meta['chunks'])
        except Exception:
            time.sleep(2 ** i)
    raise RuntimeError('chunk fetch failed ' + url)


def zarr_read(level, z0, z1, y0, y1, x0, x1):
    m = zarr_meta(level)
    c = m['chunks']; S = m['shape']
    z0, y0, x0 = max(z0, 0), max(y0, 0), max(x0, 0)
    z1, y1, x1 = min(z1, S[0]), min(y1, S[1]), min(x1, S[2])
    out = np.zeros((z1 - z0, y1 - y0, x1 - x0), np.uint8)
    for cz in range(z0 // c[0], (z1 - 1) // c[0] + 1):
        for cy in range(y0 // c[1], (y1 - 1) // c[1] + 1):
            for cx in range(x0 // c[2], (x1 - 1) // c[2] + 1):
                a = zarr_chunk(level, cz, cy, cx, m)
                gz, gy, gx = cz * c[0], cy * c[1], cx * c[2]
                sz = slice(max(z0, gz), min(z1, gz + c[0])); sy = slice(max(y0, gy), min(y1, gy + c[1]))
                sx = slice(max(x0, gx), min(x1, gx + c[2]))
                out[sz.start - z0:sz.stop - z0, sy.start - y0:sy.stop - y0, sx.start - x0:sx.stop - x0] = \
                    a[sz.start - gz:sz.stop - gz, sy.start - gy:sy.stop - gy, sx.start - gx:sx.stop - gx]
    return out, (z0, y0, x0), S


def cmd_seeds(out):
    """Seed plan. Level 5 (x32) surface voxels (>= 128): per z band, the xy centroid of surface voxels is the
    provisional scroll axis (no umbilicus is published for this volume) and R99 = p99 radius. PASS 3 inner third =
    r / R99 in [0.10, 1/3] (the 0.10 floor keeps seeds off the provisional axis, where the angle is ill-defined). Targets: z fractions {0.5, 0.3, 0.7} x angles {0, 90, 180, 270} deg, ordered so the
    first four are spread in both z and angle. Each target snaps to the nearest level-5 inner-third surface voxel,
    then to the nearest level-0 voxel >= 128 within 48 voxels of its x32 position."""
    L5 = 5; f = 2 ** L5
    v, _, S5 = zarr_read(L5, 0, 10 ** 6, 0, 10 ** 6, 0, 10 ** 6)
    zz, yy, xx = np.nonzero(v >= 128)
    nb = 10
    edges = np.linspace(0, S5[0], nb + 1).astype(int)
    band = np.clip(np.searchsorted(edges, zz, side='right') - 1, 0, nb - 1)
    cy = np.array([yy[band == b].mean() if (band == b).any() else np.nan for b in range(nb)])
    cx = np.array([xx[band == b].mean() if (band == b).any() else np.nan for b in range(nb)])
    r = np.hypot(yy - cy[band], xx - cx[band])
    R99 = np.array([np.percentile(r[band == b], 99) if (band == b).sum() > 50 else np.nan for b in range(nb)])
    rf = r / R99[band]
    ang = np.degrees(np.arctan2(yy - cy[band], xx - cx[band])) % 360
    mid = (rf >= 0.10) & (rf <= 1.0 / 3.0)  # inner third (name kept from the source helper)
    order = [(0.5, 0), (0.3, 90), (0.7, 180), (0.5, 270), (0.3, 270), (0.7, 0), (0.5, 90), (0.3, 180),
             (0.7, 90), (0.5, 180), (0.3, 0), (0.7, 270)]
    cands = []
    for zf, a in order:
        zt = zf * S5[0]
        sel = mid & (np.abs(zz - zt) <= 4)
        if not sel.any():
            cands.append({'target': [zf, a], 'status': 'no inner-third surface voxel at level 5'}); continue
        da = np.abs((ang[sel] - a + 180) % 360 - 180)
        i = np.flatnonzero(sel)[int(np.argmin(da + 0.5 * np.abs(zz[sel] - zt)))]
        p0 = np.array([zz[i], yy[i], xx[i]]) * f + f // 2
        blk, o, _ = zarr_read(0, p0[0] - 48, p0[0] + 49, p0[1] - 48, p0[1] + 49, p0[2] - 48, p0[2] + 49)
        nz = np.argwhere(blk >= 128)
        ent = {'target': [zf, a], 'level5_zyx': [int(zz[i]), int(yy[i]), int(xx[i])], 'radius_frac': round(float(rf[i]), 3),
               'angle_deg': round(float(ang[i]), 1), 'angle_err_deg': round(float(np.abs((ang[i] - a + 180) % 360 - 180)), 1)}
        if not len(nz):
            ent['status'] = 'no level-0 voxel >= 128 within 48 vx'; cands.append(ent); continue
        q = nz[np.argmin(((nz + np.array(o)) - p0) ** 2 @ np.ones(3))] + np.array(o)
        ent.update(status='ok', seed_xyz=[int(q[2]), int(q[1]), int(q[0])], seed_value=int(blk[tuple(q - np.array(o))]),
                   snap_dist_vx=round(float(np.linalg.norm(q - p0)), 2))
        cands.append(ent)
    for k, c in enumerate(cands):
        c['k'] = k
    json.dump({'provenance': PROV, 'generated_utc': utc(), 'surface_zarr': SURF + '.zarr', 'level0_shape_zyx': zarr_meta(0)['shape'],
               'level5_shape_zyx': S5, 'level5_surface_voxels': int(len(zz)),
               'axis_estimate_level5': {'z_band_edges': edges.tolist(), 'cy': np.round(cy, 2).tolist(), 'cx': np.round(cx, 2).tolist(),
                                        'R99': np.round(R99, 2).tolist(),
                                        'note': 'centroid of surface voxels per z band; provisional axis, no umbilicus published'},
               'rule': cmd_seeds.__doc__, 'candidates': cands}, open(out, 'w'), indent=1)
    for c in cands:
        print(c['k'], c['status'], c.get('seed_xyz'))


def load_xyz(d):
    import tifffile
    P = np.stack([tifffile.imread(os.path.join(d, n + '.tif')).astype(np.float64) for n in 'xyz'], -1)
    valid = (P[..., 0] != -1) & np.isfinite(P).all(-1)
    return P, valid


def cmd_exclude(seeds, k, segroot):
    """Candidate k is skipped if its seed lies within 2 mm (231 vx at 8.64 um) of any kept segment point."""
    c = json.load(open(seeds))['candidates'][int(k)]
    if c.get('status') != 'ok':
        sys.exit(4)
    s = np.array(c['seed_xyz'], float)
    for d in sorted(os.listdir(segroot)) if os.path.isdir(segroot) else []:
        md = os.path.join(segroot, d, 'mesh')
        if os.path.exists(os.path.join(md, 'x.tif')):
            P, v = load_xyz(md)
            dm = float(np.sqrt(((P[v] - s) ** 2).sum(-1)).min())
            if dm < 2000.0 / 8.64:
                print('near', d, round(dm, 1)); sys.exit(3)
    sys.exit(0)


def cmd_geom(segdir, selfcross, vox, out):
    vox = float(vox)
    meta = json.load(open(os.path.join(segdir, 'meta.json')))
    P, v = load_xyz(segdir)
    sc = meta.get('scale'); s = float(sc[0] if isinstance(sc, list) else sc)
    step = 1.0 / s
    q = v[:-1, :-1] & v[1:, :-1] & v[:-1, 1:] & v[1:, 1:]
    a = P[:-1, :-1]; b = P[:-1, 1:]; c = P[1:, :-1]; d = P[1:, 1:]
    A = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=-1) + 0.5 * np.linalg.norm(np.cross(b - d, c - d), axis=-1)
    area_cm2 = float(A[q].sum()) * (vox * 1e-4) ** 2
    eh = np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1)[v[:, 1:] & v[:, :-1]] / step
    ev = np.linalg.norm(P[1:] - P[:-1], axis=-1)[v[1:] & v[:-1]] / step
    e = np.concatenate([eh, ev])
    pct = lambda x: {p: round(float(np.percentile(x, p)), 4) for p in (1, 5, 50, 95, 99)} if len(x) else {}
    R = json.load(open(selfcross)) if os.path.exists(selfcross) else None
    trans = None if R is None else int(sum(dd.get('transverse', 0) for dd in R.get('census', [])))
    g = {'provenance': PROV, 'generated_utc': utc(), 'segment_dir': os.path.basename(segdir.rstrip('/')),
         'meta_area_cm2': meta.get('area_cm2'), 'grid_area_cm2': round(area_cm2, 4), 'grid_shape': list(v.shape),
         'valid_points': int(v.sum()), 'meta_scale': s, 'step_vx': step, 'voxel_um': vox,
         'edge_ratio_percentiles': pct(e), 'edge_ratio_note': 'grid edge length / nominal step (1.0 = no stretch)',
         'edge_ratio_frac_outside_0.5_2.0': round(float(((e < 0.5) | (e > 2.0)).mean()), 5) if len(e) else None,
         'bbox_xyz_min': P[v].min(0).round(1).tolist(), 'bbox_xyz_max': P[v].max(0).round(1).tolist(),
         'selfcross_transverse': trans,
         'selfcross_census': None if R is None else [{k: dd.get(k) for k in ('diagonal', 'triangles', 'transverse', 'coplanar', 'grazing', 'quads_dropped_for_edge_length')} for dd in R.get('census', [])],
         'x_tif_sha256': hashlib.sha256(open(os.path.join(segdir, 'x.tif'), 'rb').read()).hexdigest()}
    area_gate = min(x for x in (g['meta_area_cm2'], g['grid_area_cm2']) if x is not None)
    g['gate'] = {'area_cm2_used': area_gate, 'area_ok': area_gate >= 16.0, 'selfcross_ok': trans == 0,
                 'rule': 'keep iff 0 transverse self-crossings AND min(meta, grid) area >= 16 cm^2'}
    g['keep'] = bool(g['gate']['area_ok'] and g['gate']['selfcross_ok'])
    json.dump(g, open(out, 'w'), indent=1)
    print('keep' if g['keep'] else 'reject', area_gate, trans)


def cmd_prep(md, work):
    import tifffile
    meta = json.load(open(os.path.join(md, 'meta.json')))
    sc = meta['scale']; s = float(sc[0] if isinstance(sc, list) else sc)
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
    if cw * ch > MAX_MPX * 1e6:
        f = (MAX_MPX * 1e6 / (cw * ch)) ** 0.5
        nw, nh = int(cw * f), int(ch * f)
        cx0 += (cw - nw) // 2; cy0 += (ch - nh) // 2; cw, ch = nw, nh; capped = True
    os.makedirs(work, exist_ok=True)
    np.save(os.path.join(work, 'grid_valid.npy'), valid)
    crop = {'segment': os.path.basename(os.path.dirname(md.rstrip('/'))) if md.rstrip('/').endswith('mesh') else os.path.basename(md.rstrip('/')),
            'mesh_dir': md, 'meta_scale': s, 'grid_shape': list(valid.shape), 'grid_valid_points': int(valid.sum()),
            'grid_valid_bbox_yx': [gy0, gy1, gx0, gx1], 'crop_xywh': [cx0, cy0, cw, ch], 'capped_to_max_mpx': capped,
            'max_mpx': MAX_MPX, 'canvas_rule': 'canvas px = grid px / meta scale; manual crop, no --auto-crop',
            'x_tif_sha256': hashlib.sha256(open(os.path.join(md, 'x.tif'), 'rb').read()).hexdigest()}
    json.dump(crop, open(os.path.join(work, 'crop.json'), 'w'), indent=1)
    print(*crop['crop_xywh'])


def cmd_tiles(work, pred, outdir, tag, voxel_um, source):
    import tifffile, cv2
    voxel_um = float(voxel_um)
    sys.path.insert(0, os.path.join(REPO, 'src'))
    from hercules.display.builder import png_bytes
    crop = json.load(open(os.path.join(work, 'crop.json')))
    cx0, cy0, cw, ch = crop['crop_xywh']; s = crop['meta_scale']
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
    os.makedirs(outdir, exist_ok=True)
    rows, kept = [], 0
    for r in range(H // T + (H % T > 0)):
        for c in range(W // T + (W % T > 0)):
            t = np.zeros((T, T), np.uint8); m = np.zeros((T, T), bool)
            a = u8[r * T:(r + 1) * T, c * T:(c + 1) * T]; b = valid[r * T:(r + 1) * T, c * T:(c + 1) * T]
            t[:a.shape[0], :a.shape[1]] = a; m[:b.shape[0], :b.shape[1]] = b
            vf = float(m.mean())
            ent = {'segment': crop['segment'], 'source': source, 'pass': PASS, 'direction': tag, 'r': r, 'c': c,
                   'valid_fraction': round(vf, 4), 'px_per_mm': round(OUT_SIDE / 20.0, 3), 'src_px_per_mm': round(px_mm, 4),
                   'tile_src_px': T, 'canvas_x0': cx0 + c * T, 'canvas_y0': cy0 + r * T}
            if vf >= 0.5:
                png = png_bytes(cv2.resize(t, (OUT_SIDE, OUT_SIDE), interpolation=cv2.INTER_AREA))
                fn = f'{tag}_r{r:02d}_c{c:02d}.png'
                open(os.path.join(outdir, fn), 'wb').write(png)
                ent.update(file=fn, png_sha256=hashlib.sha256(png).hexdigest())
                kept += 1
            rows.append(ent)
    mf = os.path.join(outdir, 'manifest.json')
    M = json.load(open(mf)) if os.path.exists(mf) else {
        'provenance': PROV, 'decl': 'DECL-FL-1', 'scroll': SC, 'pass': PASS, 'segment': crop['segment'], 'source': source,
        'display_spec': 'u8 = clip(p*255) truncated, 0 outside mesh-valid, 2x2 cm tiles, cv2.INTER_AREA -> 1068 px (53.4 px/mm), PNG (hercules.display.builder.png_bytes); keep valid_fraction >= 0.5',
        'chain': 'C2-NT: vc_render_tifxyz -n 31 --flip-normals (villa 41701aa) -> vesuvius.ink_detection.inference.infer ink_9um step-075000 (sha256 e635558a...9cab), --direction both, no TTA, CPU',
        'crop': crop, 'runs': {}}
    M['runs'][tag] = {'generated_utc': utc(), 'pred_file': os.path.basename(pred),
                      'pred_sha256': hashlib.sha256(open(pred, 'rb').read()).hexdigest(), **info,
                      'tiles_total': len(rows), 'tiles_kept': kept, 'tiles': rows}
    json.dump(M, open(mf, 'w'), indent=1)
    print(tag, 'kept', kept, 'of', len(rows))


if __name__ == '__main__':
    c, a = sys.argv[1], sys.argv[2:]
    {'listing': cmd_listing, 'select': cmd_select, 'seeds': cmd_seeds, 'exclude': cmd_exclude, 'geom': cmd_geom,
     'prep': cmd_prep, 'tiles': cmd_tiles, 'fetch_mesh': fetch_mesh}[c](*a)
