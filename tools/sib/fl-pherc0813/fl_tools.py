#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""First Letters screen helpers for PHerc0813 (RULES.md DECL-FL-1). Numbers only: no image is opened for viewing,
displayed or described; arrays are reduced to scalars, and tiles are written as PNG bytes summarised by sha256.

  fl_tools.py geom <seg.tifxyz> <out.json>        area (cm^2) + mesh-distortion metrics of a tifxyz grid
  fl_tools.py tiles <seg.tifxyz> <render.zarr> <pred.tif> <outdir> <segname> <source>
"""
import hashlib, json, os, sys
import numpy as np
import cv2, tifffile, zarr

VOX_UM = 9.362                 # PHerc0813 20250821151723, samplePixelSize 0.009362 mm
T = int(round(20000 / VOX_UM))  # 2 cm at 1 canvas px = 1 voxel -> 2136 px
OUT = 1068                      # INTER_AREA target (53.4 px/mm, DECL-FL-1 item 1)
VALID_MIN = 0.50


def load_grid(seg):
    x, y, z = (tifffile.imread(os.path.join(seg, f'{a}.tif')).astype(np.float64) for a in 'xyz')
    valid = (z > 0) & np.isfinite(x) & np.isfinite(y) & np.isfinite(z) & (x != -1)
    mp = os.path.join(seg, 'mask.tif')
    if os.path.exists(mp):
        m = tifffile.imread(mp)
        if m.ndim == 3:
            m = m[..., 0]
        if m.shape == valid.shape:
            valid &= m > 0
    meta = json.load(open(os.path.join(seg, 'meta.json')))
    return np.stack([x, y, z], -1), valid, meta


def geom(seg, out):
    P, V, meta = load_grid(seg)
    q = V[:-1, :-1] & V[1:, :-1] & V[:-1, 1:] & V[1:, 1:]
    a, b, c, d = P[:-1, :-1], P[:-1, 1:], P[1:, :-1], P[1:, 1:]
    tri = lambda u, v, w: 0.5 * np.linalg.norm(np.cross(v - u, w - u), axis=-1)
    area_vox2 = (tri(a, b, d) + tri(a, d, c))[q].sum()
    eu = np.linalg.norm(P[:, 1:] - P[:, :-1], axis=-1)[V[:, 1:] & V[:, :-1]]
    ev = np.linalg.norm(P[1:] - P[:-1], axis=-1)[V[1:] & V[:-1]]
    step = 1.0 / float(meta.get('scale', [0.05, 0.05])[0])
    e = np.concatenate([eu, ev]) / step
    r = dict(segment=os.path.basename(seg.rstrip('/')), grid_shape=list(V.shape), valid_points=int(V.sum()),
             valid_quads=int(q.sum()), area_cm2=float(area_vox2 * (VOX_UM * 1e-4) ** 2),
             meta_area_cm2=meta.get('area_cm2'), meta_scale=meta.get('scale'), nominal_step_vox=step,
             edge_ratio_mean=float(e.mean()) if e.size else None,
             edge_ratio_p05=float(np.percentile(e, 5)) if e.size else None,
             edge_ratio_p95=float(np.percentile(e, 95)) if e.size else None,
             edge_ratio_max=float(e.max()) if e.size else None,
             note='edge_ratio = grid edge length / nominal step (1.0 = isometric; canvas px = voxel only where ~1)')
    json.dump(r, open(out, 'w'), indent=1)
    print(json.dumps(r))


def tiles(seg, render_zarr, pred_tif, outdir, segname, source):
    _, V, _ = load_grid(seg)
    rz = zarr.open(render_zarr, mode='r')
    rz = rz['0'] if hasattr(rz, 'keys') and '0' in rz else rz
    H, W = rz.shape[-2:]
    p = tifffile.imread(pred_tif)
    p = np.squeeze(p)
    assert p.shape == (H, W), f'prediction {p.shape} != render canvas {(H, W)}'
    if p.dtype == np.uint8:
        u8, conv = p, 'u8 as written by infer'
    else:
        pf = p.astype(np.float64)
        s = 255.0 if np.nanmax(pf) <= 1.0 else 1.0
        u8, conv = np.clip(np.nan_to_num(pf) * s, 0, 255).astype(np.uint8), f'clip(p*{s:g}) truncated'
    valid = cv2.resize(V.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
    u8 = np.where(valid, u8, 0).astype(np.uint8)
    os.makedirs(outdir, exist_ok=True)
    rows = []
    for r in range((H + T - 1) // T):
        for c in range((W + T - 1) // T):
            vt = np.zeros((T, T), bool); it = np.zeros((T, T), np.uint8)
            vs = valid[r * T:(r + 1) * T, c * T:(c + 1) * T]; vt[:vs.shape[0], :vs.shape[1]] = vs
            is_ = u8[r * T:(r + 1) * T, c * T:(c + 1) * T]; it[:is_.shape[0], :is_.shape[1]] = is_
            vf = float(vt.mean())
            if vf < VALID_MIN:
                continue
            small = cv2.resize(it, (OUT, OUT), interpolation=cv2.INTER_AREA)
            ok, buf = cv2.imencode('.png', small)
            assert ok
            b = buf.tobytes(); name = f'r{r:02d}_c{c:02d}.png'
            open(os.path.join(outdir, name), 'wb').write(b)
            iv = it[vt]
            rows.append(dict(segment=segname, r=r, c=c, file=name, png_sha256=hashlib.sha256(b).hexdigest(),
                             valid_fraction=round(vf, 6), px_per_mm=OUT / 20.0, source=source,
                             ink_score=round(float((iv >= 128).mean()), 6)))
    man = dict(segment=segname, source=source, voxel_um=VOX_UM, tile_px_full=T, tile_px_out=OUT,
               canvas_hw=[int(H), int(W)], pred_sha256=hashlib.sha256(open(pred_tif, 'rb').read()).hexdigest(),
               pred_dtype=str(p.dtype), pred_to_u8=conv, valid_rule='tifxyz valid grid (z>0, mask.tif) INTER_NEAREST to canvas',
               valid_min=VALID_MIN, ink_score='fraction of valid px >= 128 (DECL-FL-1 item 2)',
               n_tiles=len(rows), tiles=rows)
    json.dump(man, open(os.path.join(outdir, 'manifest.json'), 'w'), indent=1)
    print(f'tiles: {len(rows)} kept, canvas {H}x{W}')


if __name__ == '__main__':
    {'geom': geom, 'tiles': tiles}[sys.argv[1]](*sys.argv[2:])
