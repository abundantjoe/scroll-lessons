#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""First Letters PASS 3 helpers for PHerc0826 (RULES.md DECL-FL-1; tools/fl/BRIEF_PASS.md @ dcb6a6b).
geom and tiles are adapted from tools/sib/fl-pherc0813/fl_tools.py (branch sib-fl-pherc0813 @ 325973f; the same
9.362 um scan geometry); seeds is new. Numbers only: no image is opened for viewing, displayed or described; arrays
are reduced to scalars, and tiles are written as PNG bytes summarised by sha256.

  fl3_tools.py seeds <surface.zarr url> <umbilicus.json url> <out.json> [n=4]
  fl3_tools.py geom <seg.tifxyz> <out.json>        area (cm^2) + mesh-distortion metrics of a tifxyz grid
  fl3_tools.py tiles <seg.tifxyz> <render.zarr> <pred_dir> <outdir> <segname> <source>
"""
import hashlib, json, os, sys
import numpy as np
import cv2, tifffile, zarr

VOX_UM = 9.362                 # PHerc0826 20250821151701-9.362um-1.2m-113keV (volume name)
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


def tiles(seg, render_zarr, pred_dir, outdir, segname, source):
    """Tiles every prediction in pred_dir: pred.tif = forward, pred_reverse.tif = reverse (infer --direction both).
    One manifest.json for the segment; each row carries its direction."""
    _, V, _ = load_grid(seg)
    rz = zarr.open(render_zarr, mode='r')
    rz = rz['0'] if hasattr(rz, 'keys') and '0' in rz else rz
    H, W = rz.shape[-2:]
    valid = cv2.resize(V.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
    os.makedirs(outdir, exist_ok=True)
    rows, preds = [], []
    for fn in sorted(os.listdir(pred_dir)):
        if not fn.endswith('.tif'):
            continue
        direction = 'reverse' if fn.endswith('_reverse.tif') else 'forward'
        pred_tif = os.path.join(pred_dir, fn)
        p = np.squeeze(tifffile.imread(pred_tif))
        assert p.shape == (H, W), f'prediction {p.shape} != render canvas {(H, W)}'
        if p.dtype == np.uint8:
            u8, conv = p, 'u8 as written by infer'
        else:
            pf = p.astype(np.float64)
            s = 255.0 if np.nanmax(pf) <= 1.0 else 1.0
            u8, conv = np.clip(np.nan_to_num(pf) * s, 0, 255).astype(np.uint8), f'clip(p*{s:g}) truncated'
        u8 = np.where(valid, u8, 0).astype(np.uint8)
        preds.append(dict(file=fn, direction=direction, sha256=hashlib.sha256(open(pred_tif, 'rb').read()).hexdigest(),
                          dtype=str(p.dtype), to_u8=conv))
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
                b = buf.tobytes(); name = f'r{r:02d}_c{c:02d}_{direction}.png'
                open(os.path.join(outdir, name), 'wb').write(b)
                iv = it[vt]
                rows.append({'segment': segname, 'r': r, 'c': c, 'direction': direction, 'file': name,
                             'png_sha256': hashlib.sha256(b).hexdigest(), 'valid_fraction': round(vf, 6),
                             'px_per_mm': OUT / 20.0, 'source': source, 'pass': 3,
                             'ink_score': round(float((iv >= 128).mean()), 6)})
    assert preds, f'no prediction tif in {pred_dir}'
    man = dict(segment=segname, source=source, scroll='PHerc0826', **{'pass': 3}, voxel_um=VOX_UM, tile_px_full=T,
               tile_px_out=OUT, canvas_hw=[int(H), int(W)], predictions=preds,
               valid_rule='tifxyz valid grid (z>0, mask.tif) INTER_NEAREST to canvas', valid_min=VALID_MIN,
               ink_score='fraction of valid px >= 128 (DECL-FL-1 item 2)', n_tiles=len(rows), tiles=rows)
    json.dump(man, open(os.path.join(outdir, 'manifest.json'), 'w'), indent=1)
    print(f'tiles: {len(rows)} kept over {len(preds)} directions, canvas {H}x{W}')

def seeds(surf_url, umb_url, out, n=4):
    """PASS 3 auto-grow seeds in the INNER third of the scroll radius (BRIEF_PASS item 2). Rule, fixed here:
    - umbilicus centre (x, y) at each z = linear interpolation of the organizer umbilicus control points over z;
    - surface-m7 prediction at pyramid level 4 (16x), voxels >= 64 (downsampling lowers values; L0 is checked >= 128);
    - R(z) = p99 of the radial distance of those voxels in the level-4 slice (>= 200 voxels needed), in L0 units;
    - candidates: r <= R(z) / 3, z within the central 80 % of the surface z extent;
    - draw with default_rng(20260930); accept if >= 1500 L0 voxels (14 mm) from every accepted seed;
    - refine on L0: in a 64^3 L0 block centred on the candidate, the voxel >= 128 nearest the centre, else reject."""
    import requests
    n = int(n)
    u = requests.get(umb_url, timeout=60).json()
    cp = sorted(u["control_points"], key=lambda p: p["z"])
    uz = np.array([p["z"] for p in cp], float)
    ux = np.array([p["x"] for p in cp], float)
    uy = np.array([p["y"] for p in cp], float)
    import fsspec
    store = fsspec.get_mapper(surf_url)
    z4 = zarr.open(store, mode="r", path="4")
    z0 = zarr.open(store, mode="r", path="0")
    f = 16
    a = z4[:]
    zs, ys, xs = np.nonzero(a >= 64)
    rec = {"rule": seeds.__doc__, "umbilicus_url": umb_url, "surface_url": surf_url, "level4_shape": list(a.shape),
           "level4_vox_ge64": int(zs.size)}
    del a
    Z0, Y0, X0 = zs * f + f / 2, ys * f + f / 2, xs * f + f / 2
    r = np.hypot(X0 - np.interp(Z0, uz, ux), Y0 - np.interp(Z0, uz, uy))
    R = np.full(z4.shape[0], np.nan)
    order = np.argsort(zs)
    zs_s, r_s = zs[order], r[order]
    bounds = np.searchsorted(zs_s, np.arange(z4.shape[0] + 1))
    for k in range(z4.shape[0]):
        seg = r_s[bounds[k]:bounds[k + 1]]
        if seg.size >= 200:
            R[k] = np.percentile(seg, 99)
    zv = np.nonzero(np.isfinite(R))[0]
    zlo, zhi = zv.min(), zv.max()
    zlo2, zhi2 = zlo + 0.1 * (zhi - zlo), zhi - 0.1 * (zhi - zlo)
    Rz = R[zs]
    cand = np.nonzero(np.isfinite(Rz) & (r <= Rz / 3) & (zs >= zlo2) & (zs <= zhi2))[0]
    rec.update({"z_extent_L4": [int(zlo), int(zhi)], "z_central80_L4": [float(zlo2), float(zhi2)],
                "R_L0_median": float(np.nanmedian(R)), "n_candidates_L4": int(cand.size)})
    rng = np.random.default_rng(20260930)
    acc, tried = [], 0
    for i in rng.permutation(cand)[:5000]:
        if len(acc) >= n:
            break
        tried += 1
        p = np.array([X0[i], Y0[i], Z0[i]])
        if any(np.linalg.norm(p - np.array([s["x"], s["y"], s["z"]])) < 1500 for s in acc):
            continue
        cz, cy, cx = int(Z0[i]), int(Y0[i]), int(X0[i])
        b = z0[max(0, cz - 32):cz + 32, max(0, cy - 32):cy + 32, max(0, cx - 32):cx + 32]
        hz, hy, hx = np.nonzero(b >= 128)
        if hz.size == 0:
            continue
        oz, oy, ox = max(0, cz - 32), max(0, cy - 32), max(0, cx - 32)
        d = (hz + oz - cz) ** 2 + (hy + oy - cy) ** 2 + (hx + ox - cx) ** 2
        j = int(np.argmin(d))
        sx, sy, sz = int(hx[j] + ox), int(hy[j] + oy), int(hz[j] + oz)
        rr = float(np.hypot(sx - np.interp(sz, uz, ux), sy - np.interp(sz, uz, uy)))
        acc.append({"x": sx, "y": sy, "z": sz, "value_L0": int(b[hz[j], hy[j], hx[j]]), "r_L0": rr,
                    "R_z_L0": float(R[int(sz // f)]) if int(sz // f) < R.size else None,
                    "r_over_R": rr / float(R[int(sz // f)]) if int(sz // f) < R.size and np.isfinite(R[int(sz // f)]) else None})
    rec.update({"candidates_tried": tried, "seeds": acc})
    json.dump(rec, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in rec.items() if k != "rule"}))


if __name__ == '__main__':
    {'geom': geom, 'tiles': tiles, 'seeds': seeds}[sys.argv[1]](*sys.argv[2:])
