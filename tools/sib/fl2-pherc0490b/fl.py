#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""First Letters screen (RULES.md DECL-FL-1), worker fl2-pherc0490b (PASS 2; copied from the pass-1 worker fl-pherc0490b, commit 20b8231): numeric helpers for pipeline.sh.
Numbers, hashes and file lists only: no tile, prediction or CT image is opened for viewing or described.

  fl.py list      OUT.json                  anonymous S3 listing of PHerc0490B/ (segments/ tifxyz + meta area)
  fl.py growrec   SEGDIR SELFCROSS.json OUT.json   record one auto-grown segment (area, self-intersections, keep)
  fl.py tiles     SEG SEGDIR RENDER.zarr PRED_FWD.tif PRED_REV.tif OUTDIR SOURCE
                  2 x 2 cm tiles, u8, INTER_AREA to 1068 px, PNG, valid >= 50 %, manifest.json

Tile geometry: the render canvas (vc_render_tifxyz --scale 1, no crop, no --auto-crop) is the tifxyz grid
upsampled by 1/meta.scale (checked: canvas/grid ratio equal on both axes, integral). Mesh-valid = no coordinate
== -1 and all finite, mapped to canvas pixels by gy = (y * gh) // H (rule of tools/sib/ckpt-screen-b/p4o_tiles.py).
Tile side T = 20 mm / 8.64 um = 2314.8 canvas px; edges at round(k * T) from the mesh-valid bbox origin. Pixels
outside mesh-valid are 0 in the tile. valid_fraction = mesh-valid share of the tile's canvas pixels.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'src'))

HTTP = 'https://vesuvius-challenge-open-data.s3.amazonaws.com'
SCROLL = 'PHerc0490B'
VOXEL_UM = 8.64
TILE_MM = 20.0
OUT_SIDE = 1068
MIN_VALID = 0.50
MIN_AREA_CM2 = 16.0


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def s3_list(prefix, delimiter='/'):
    """Anonymous ListObjectsV2 (all pages). Returns (common prefixes, [(key, size)])."""
    prefixes, keys, token = [], [], None
    while True:
        q = f'{HTTP}/?list-type=2&prefix={prefix}' + (f'&delimiter={delimiter}' if delimiter else '')
        if token:
            q += '&continuation-token=' + urllib.parse.quote(token)
        root = ET.fromstring(urllib.request.urlopen(q, timeout=60).read())
        ns = {'s': root.tag.split('}')[0].strip('{')}
        prefixes += [e.text for e in root.findall('s:CommonPrefixes/s:Prefix', ns)]
        keys += [(c.find('s:Key', ns).text, int(c.find('s:Size', ns).text)) for c in root.findall('s:Contents', ns)]
        if root.find('s:IsTruncated', ns).text != 'true':
            return prefixes, keys
        token = root.find('s:NextContinuationToken', ns).text


def cmd_list(out):
    import urllib.parse  # noqa: F401  (used by s3_list for continuation tokens)
    top, _ = s3_list(f'{SCROLL}/')
    segs = []
    if f'{SCROLL}/segments/' in top:
        _, keys = s3_list(f'{SCROLL}/segments/', delimiter=None)
        for k, _s in keys:
            if k.endswith('.tifxyz/meta.json') or (k.endswith('/meta.json') and '/x.tif' not in k):
                d = k[:-len('meta.json')]
                if not any(kk == d + 'x.tif' for kk, _ in keys):
                    continue
                try:
                    meta = json.loads(urllib.request.urlopen(f'{HTTP}/{k}', timeout=60).read())
                except Exception as e:  # recorded, never silently dropped
                    meta = {'error': repr(e)}
                segs.append(dict(tifxyz=d, meta_key=k, area_cm2=meta.get('area_cm2'), meta=meta))
    segs.sort(key=lambda s: -(s['area_cm2'] or 0))
    rec = dict(tool='fl.py list', utc=utc(), bucket='s3://vesuvius-challenge-open-data (anonymous HTTPS)',
               scroll_prefixes=top, organizer_tifxyz_count=len(segs), organizer_tifxyz=segs,
               decision=('organizer: 3 largest by meta area_cm2' if segs else
                         'auto: no organizer tifxyz; grow up to 4 with vc_grow_seg_from_seed on surface-m7'))
    json.dump(rec, open(out, 'w'), indent=1)
    print(rec['decision'])


def load_grid(segdir):
    import numpy as np
    import tifffile
    P = np.stack([tifffile.imread(os.path.join(segdir, f'{a}.tif')) for a in 'xyz'], -1)
    valid = ~((P[..., 0] == -1) | (P[..., 1] == -1) | (P[..., 2] == -1)) & np.isfinite(P).all(-1)
    return valid


def cmd_growrec(segdir, selfcross, out):
    meta = json.load(open(os.path.join(segdir, 'meta.json')))
    sc = json.load(open(selfcross))
    area = meta.get('area_cm2')
    transverse = sc.get('clean_of_transverse_self_intersection')
    diags = [{k: d.get(k) for k in ('diagonal', 'triangles', 'transverse', 'coplanar', 'grazing')}
             for d in sc.get('diagonals', sc.get('census', []))]
    n_trans = sum(int(d['transverse'] or 0) for d in diags) if diags else None
    keep = bool(transverse is True and n_trans == 0 and area is not None and float(area) >= MIN_AREA_CM2)
    counts = dict(transverse_total=n_trans, per_diagonal=diags)
    valid = load_grid(segdir)
    rec = dict(tool='fl.py growrec', utc=utc(), segment=os.path.basename(segdir.rstrip('/')), area_cm2=area,
               min_area_cm2=MIN_AREA_CM2, clean_of_transverse_self_intersection=transverse,
               selfcross_counts=counts, selfcross_report_sha256=sha256_file(selfcross),
               grid_shape=list(valid.shape), grid_valid_fraction=float(valid.mean()), meta=meta,
               tif_sha256={a: sha256_file(os.path.join(segdir, f'{a}.tif')) for a in 'xyz'}, keep=keep)
    json.dump(rec, open(out, 'w'), indent=1)
    print('KEEP' if keep else 'REJECT')


def cmd_tiles(seg, segdir, render, pred_fwd, pred_rev, outdir, source):
    import cv2
    import numpy as np
    import tifffile
    import zarr
    from hercules.display.builder import png_bytes

    valid = load_grid(segdir)
    gh, gw = valid.shape
    arr = zarr.open(os.path.join(render, '0'), mode='r')
    nz, H, W = arr.shape
    scale = json.load(open(os.path.join(segdir, 'meta.json'))).get('scale')
    fy, fx = H / gh, W / gw
    assert nz == 31 and abs(fy - fx) < 1e-9 and abs(fy - round(fy)) < 1e-9, (arr.shape, valid.shape)
    preds = {}
    for name, p in (('forward', pred_fwd), ('reverse', pred_rev)):
        a = tifffile.imread(p)
        assert a.shape == (H, W) and a.dtype == np.uint8, (name, a.shape, a.dtype, (H, W))
        preds[name] = a
    gy = np.clip((np.arange(H) * gh) // H, 0, gh - 1)
    gx = np.clip((np.arange(W) * gw) // W, 0, gw - 1)
    mask = valid[np.ix_(gy, gx)]
    ys, xs = np.nonzero(mask.any(1))[0], np.nonzero(mask.any(0))[0]
    y0, y1, x0, x1 = int(ys[0]), int(ys[-1]) + 1, int(xs[0]), int(xs[-1]) + 1
    T = TILE_MM * 1000.0 / VOXEL_UM
    nr, nc = int(np.ceil((y1 - y0) / T)), int(np.ceil((x1 - x0) / T))
    os.makedirs(outdir, exist_ok=True)
    tiles, n_total = [], 0
    for r in range(nr):
        for c in range(nc):
            ty0, ty1 = y0 + int(round(r * T)), y0 + int(round((r + 1) * T))
            tx0, tx1 = x0 + int(round(c * T)), x0 + int(round((c + 1) * T))
            n_total += 1
            m = np.zeros((ty1 - ty0, tx1 - tx0), bool)
            sub = mask[ty0:min(ty1, H), tx0:min(tx1, W)]
            m[:sub.shape[0], :sub.shape[1]] = sub
            vf = float(m.mean())
            if vf < MIN_VALID:
                continue
            for d, a in preds.items():
                t = np.zeros(m.shape, np.uint8)
                s = a[ty0:min(ty1, H), tx0:min(tx1, W)]
                t[:s.shape[0], :s.shape[1]] = s
                t[~m] = 0
                o = cv2.resize(t, (OUT_SIDE, OUT_SIDE), interpolation=cv2.INTER_AREA)
                b = png_bytes(o)
                fn = f'r{r:02d}_c{c:02d}_{d}.png'
                open(os.path.join(outdir, fn), 'wb').write(b)
                tiles.append(dict(segment=seg, r=r, c=c, direction=d, file=fn, pass_=int(os.environ.get('FL_PASS', '2')),
                                  png_sha256=hashlib.sha256(b).hexdigest(), valid_fraction=round(vf, 6),
                                  px_per_mm=round(OUT_SIDE / ((ty1 - ty0) * VOXEL_UM / 1000.0), 4),
                                  px_per_mm_x=round(OUT_SIDE / ((tx1 - tx0) * VOXEL_UM / 1000.0), 4),
                                  canvas_yx=[ty0, tx0, ty1 - ty0, tx1 - tx0], source=source))
    man = dict(tool='fl.py tiles', decl='RULES.md DECL-FL-1 item 1', utc=utc(), scroll=SCROLL, segment=seg, pass_=int(os.environ.get('FL_PASS', '2')),
               source=source, voxel_um=VOXEL_UM, tile_mm=TILE_MM, tile_canvas_px=T, out_side_px=OUT_SIDE,
               resize='cv2.INTER_AREA', min_valid_fraction=MIN_VALID, canvas_hw=[H, W], grid_hw=[gh, gw],
               canvas_per_grid=fy, meta_scale=scale, valid_bbox_yx=[y0, y1, x0, x1], grid_rc=[nr, nc],
               n_candidate_tiles=n_total, n_kept_tiles=len({(t['r'], t['c']) for t in tiles}),
               canvas_valid_fraction=float(mask.mean()),
               inputs=dict(pred_forward_sha256=sha256_file(pred_fwd), pred_reverse_sha256=sha256_file(pred_rev)),
               masking='pixels outside mesh-valid set to 0 before resize', tiles=tiles)
    s_ = json.dumps(man, indent=1).replace('"pass_":', '"pass":')
    open(os.path.join(outdir, 'manifest.json'), 'w').write(s_)
    print(f'{seg}: kept {man["n_kept_tiles"]} of {n_total} tile positions x 2 directions')


def cmd_seeds(out, n='4'):
    """PASS 2 seeds: OUTER third of the scroll radius (BRIEF_PASS.md item 2).
    Level 4 (16x) of the organizer surface-m7 prediction: per z slab (middle 60 % of the occupied z range),
    centre = centroid of voxels >= 128, radius R = 99th percentile of their radial distance. Seed band
    r in [0.70 R, 0.95 R] (inside the outer third, away from the rim), at the mid-height slab (+-4 L4 slices);
    one seed per angular quadrant: the voxel >= 200 (else >= 128) nearest to r = 0.83 R at the quadrant's centre angle,
    then refined at level 0 to the highest-prediction voxel within a 48^3 block. Numbers only."""
    import numpy as np
    import zarr, fsspec
    url = f's3://vesuvius-challenge-open-data/{SCROLL}/representations/predictions/surfaces/20250521151215-surface-20260413222639-surface-m7-L0-th0.2.zarr'
    m4 = zarr.open(fsspec.get_mapper(url + '/4', anon=True), mode='r')
    p = m4[:]
    zs = np.nonzero((p >= 128).any((1, 2)))[0]
    z0, z1 = int(zs[0] + 0.2 * (zs[-1] - zs[0])), int(zs[0] + 0.8 * (zs[-1] - zs[0]))
    zc = (z0 + z1) // 2
    slab = p[zc - 4:zc + 5].max(0)
    yy, xx = np.nonzero(slab >= 128)
    cy, cx = yy.mean(), xx.mean()
    rr = np.hypot(yy - cy, xx - cx); R = float(np.percentile(rr, 99))
    ang = (np.degrees(np.arctan2(yy - cy, xx - cx)) + 360) % 360
    band = (rr >= 0.70 * R) & (rr <= 0.95 * R)
    m0 = zarr.open(fsspec.get_mapper(url + '/0', anon=True), mode='r')
    seeds = []
    for q in range(int(n)):
        sel = band & (ang >= q * 360 / int(n)) & (ang < (q + 1) * 360 / int(n))
        if not sel.any():
            seeds.append(dict(quadrant=q, seed=None, reason='no surface voxel in band')); continue
        # target: r = 0.83 R at the quadrant's centre angle; nearest strong (>= 200) voxel in the band/quadrant
        strong = sel & (slab[yy, xx] >= 200)
        cand = np.nonzero(strong if strong.any() else sel)[0]
        ta = np.radians((q + 0.5) * 360 / int(n)); ty, tx = cy + 0.83 * R * np.sin(ta), cx + 0.83 * R * np.cos(ta)
        i = int(cand[np.argmin(np.hypot(yy[cand] - ty, xx[cand] - tx))])
        Y, X, Z = int(yy[i]) * 16 + 8, int(xx[i]) * 16 + 8, zc * 16 + 8
        blk = m0[Z - 24:Z + 24, Y - 24:Y + 24, X - 24:X + 24]
        dz, dy, dx = np.unravel_index(int(np.argmax(blk)), blk.shape)
        if int(blk.max()) < 128:
            seeds.append(dict(quadrant=q, seed=None, reason=f'level-0 refinement found no voxel >= 128 (max {int(blk.max())})')); continue
        s = [X - 24 + int(dx), Y - 24 + int(dy), Z - 24 + int(dz)]
        seeds.append(dict(quadrant=q, seed_xyz=s, value_l0=int(blk.max()), r_over_R=round(float(rr[i] / R), 4),
                          angle_deg=round(float(ang[i]), 1)))
    rec = dict(tool='fl.py seeds', utc=utc(), rule='PASS 2 outer third (BRIEF_PASS.md item 2)', level=4,
               z_range_l4=[z0, z1], z_mid_l4=zc, centre_yx_l4=[round(float(cy), 2), round(float(cx), 2)],
               radius_l4=round(R, 2), band_r_over_R=[0.70, 0.95], target_r_over_R=0.83, seeds=seeds)
    json.dump(rec, open(out, 'w'), indent=1)
    print(json.dumps(seeds))


if __name__ == '__main__':
    import urllib.parse  # noqa: F401
    c, a = sys.argv[1], sys.argv[2:]
    {'list': cmd_list, 'growrec': cmd_growrec, 'tiles': cmd_tiles, 'seeds': cmd_seeds}[c](*a)
