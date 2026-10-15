# Provenance: Project HERCULES | owner the owner | [id removed]
"""REF renders of READCAL-2 bank windows on the 9 um canvas, and their K_D2 / ladder / MS displays.
The builder never opens, views or describes an image; it writes arrays, PNGs and hashes only.

Per window (segment, y0, x0) on the organizer 9.362 um canvas:
  ref_org   exact float area mean of the organizer 2.399 um reference map (c9 = (c2 + 10) N9/N2 - 10 per axis, the
            D1 J builder mapping) over the window + 512 px margin; valid = mesh-valid (nearest vertex) and covered.
  ref_A     state A = hercules.pipeline.window.run_window (margin 256, step 20 vox, z_ascending, convention_sign +1,
            the PROBE-3 / SEAL-J-D1 settings) with the PHerc0139 CT mask-centroid centre curve (centre0139.py), the
            reference resampled bilinearly onto the 2136 px levelled window (resample_to_levelled); valid = finite and
            the resampled validity >= 0.5. Invalid pixels are shown as 0. State B = A mirrored left-right.
Displays (--displays): picker = state A sigma 0 at K_D2 (1/2 INTER_AREA, 1068 px); ladder = sigma in LADDER_MM of
  state A (and B with --states AB); ms = overview + 4 quadrants of state A sigma 0 (and each ladder sigma with
  --ms-ladder). One flat folder of <uuid>.png; the key (uuid -> window, state, sigma, part, scale, y0, x0) goes to
  --key (default /work/rc2/private/refwin_key.json, never committed; the scorer holds it); a committed manifest
  lists only (uuid, sha256). Voxel size from the volume metadata.json.
Usage: python build_ref_windows.py --list logs/sib/readcal2/candidates.json --which picker_tiling|blank_candidates
       [--ids SEG:Y0:X0 ...] [--displays picker ladder ms] [--states A|AB] [--seed 20260925] [--out DIR]"""
from __future__ import annotations

import argparse
import functools
import hashlib
import json
import os
import sys

import numpy as np
import tifffile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'src'))
import cand as C  # noqa: E402
import geom as G  # noqa: E402
import rc2lib as R  # noqa: E402
from hercules.geometry.level_mesh import CentreCurve  # noqa: E402
from hercules.pipeline.window import Window, resample_to_levelled, run_window  # noqa: E402

MARGIN_ORG = 512


@functools.lru_cache(maxsize=1)
def _ink(path):
    return tifffile.imread(path)


def ref_crop_exact(scroll, key, y0, x0, h, w):
    """Float32 organizer-canvas reference over rows y0..y0+h, cols x0..x0+w (clipped to the canvas) + coverage."""
    m, _ = C.mesh9(scroll, key)
    H9, W9 = G.canvas_shape(m)
    ya, yb, xa, xb = max(0, y0), min(H9, y0 + h), max(0, x0), min(W9, x0 + w)
    ref2 = _ink(C.ink_tif(scroll, key))
    Ay = G.area_matrix(H9, ref2.shape[0])[ya:yb].astype(np.float32)
    Ax = G.area_matrix(W9, ref2.shape[1])[xa:xb].astype(np.float32)
    rows = np.unique(Ay.indices)
    tmp = Ay[:, rows] @ ref2[rows].astype(np.float32)
    out = (Ax @ tmp.T).T.astype(np.float32)
    cov = (np.asarray(Ay.sum(1)).ravel() > 0.999)[:, None] & (np.asarray(Ax.sum(1)).ravel() > 0.999)[None, :]
    mv = G.mesh_valid_canvas(m)[ya:yb, xa:xb]
    return out, cov & mv, (ya, xa), m


def centre_curve():
    z = np.load('/work/rc2/centre0139.npz')
    return CentreCurve(z=z['z'], x=z['x'], y=z['y'])


def build_window(scroll, key, y0, x0, centre):
    ref, valid, (oy, ox), mesh = ref_crop_exact(scroll, key, y0 - MARGIN_ORG, x0 - MARGIN_ORG, R.WINDOW_PX + 2 * MARGIN_ORG,
                                                R.WINDOW_PX + 2 * MARGIN_ORG)
    wy, wx = y0 - oy, x0 - ox
    ref_org = ref[wy:wy + R.WINDOW_PX, wx:wx + R.WINDOW_PX]
    val_org = valid[wy:wy + R.WINDOW_PX, wx:wx + R.WINDOW_PX]
    res = run_window(mesh, Window(y0, x0, R.WINDOW_PX, R.WINDOW_PX), centre, margin_px=256, step_vox=20.0,
                     z_ascending=True, convention_sign=1, render_valid_stats=False)
    src = np.where(valid, ref, np.nan)
    refA = resample_to_levelled(src, res.maps, (R.WINDOW_PX, R.WINDOW_PX), org_origin=(oy, ox))
    vA = resample_to_levelled(valid.astype(np.float64), res.maps, (R.WINDOW_PX, R.WINDOW_PX), org_origin=(oy, ox))
    valA = np.isfinite(refA) & (np.nan_to_num(vA) >= 0.5)
    st = res.stats
    info = {'segment': key, 'y0': y0, 'x0': x0, 'org_valid_frac': float(val_org.mean()),
            'A_valid_frac': float(valA.mean()), 'level_angle_deg': st['angle_deg'], 'level_spread_deg': st['spread_deg'],
            'flip_u_mirror': st.get('flip_u_mirror'), 'flip_v': st.get('flip_v'),
            'normal_sign_ambiguous': st.get('ambiguous'), 'map_singular_values': st['map_singular_values'],
            'ref_org_sha256': hashlib.sha256(np.ascontiguousarray(ref_org).tobytes()).hexdigest(),
            'ref_A_sha256': hashlib.sha256(np.ascontiguousarray(np.nan_to_num(refA)).tobytes()).hexdigest()}
    return ref_org, val_org, np.nan_to_num(refA), valA, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--list', default=os.path.join(REPO, 'logs/sib/readcal2/candidates.json'))
    ap.add_argument('--which', default='picker_tiling')
    ap.add_argument('--ids', nargs='*', default=None)
    ap.add_argument('--displays', nargs='*', default=['picker'])
    ap.add_argument('--states', default='A')
    ap.add_argument('--ms-ladder', action='store_true')
    ap.add_argument('--seed', type=int, default=20260925)
    ap.add_argument('--out', default='/work/rc2/refwin/img')
    ap.add_argument('--key', default='/work/rc2/private/refwin_key.json')
    ap.add_argument('--arrays', default='/work/rc2/refwin/arrays')
    ap.add_argument('--manifest', default=os.path.join(REPO, 'logs/sib/readcal2/refwin_manifest.json'))
    a = ap.parse_args()
    L = json.load(open(a.list))
    wins = [(r['scroll'], r['segment'], r['y0'], r['x0']) for r in L[a.which]]
    if a.ids:
        want = {tuple(i.split(':')) for i in a.ids}
        wins = [w for w in wins if (w[1], str(w[2]), str(w[3])) in want]
    vox = C.voxel_um('PHerc0139')
    centre = centre_curve()
    os.makedirs(a.out, exist_ok=True)
    os.makedirs(os.path.dirname(a.key), exist_ok=True)
    os.makedirs(a.arrays, exist_ok=True)
    names = R.UuidStream(a.seed, 'refwin|' + a.which)
    key, man, infos = {}, {}, []
    for (scroll, seg, y0, x0) in wins:
        if scroll != 'PHerc0139':
            infos.append({'segment': seg, 'y0': y0, 'x0': x0, 'status': 'skipped: 0814 centre curve not built'})
            continue
        wid = f'{seg}_y{y0}_x{x0}'
        ref_org, val_org, refA, valA, info = build_window(scroll, seg, y0, x0, centre)
        np.savez_compressed(f'{a.arrays}/{wid}.npz', ref_org=ref_org, val_org=val_org, ref_A=refA, val_A=valA)
        infos.append(info)
        states = {'A': (refA, valA)}
        if a.states == 'AB':
            states['B'] = (refA[:, ::-1].copy(), valA[:, ::-1].copy())
        todo = []
        for st, (rf, vl) in states.items():
            if 'picker' in a.displays and st == 'A':
                todo.append(('picker', st, 0.0, 'OV', R.ref_ladder_images(rf, vl, vox, (0.0,))[0.0], 2.0, 0, 0))
            if 'ladder' in a.displays:
                for s, img in R.ref_ladder_images(rf, vl, vox).items():
                    todo.append(('ladder', st, s, 'OV', img, 2.0, 0, 0))
            if 'ms' in a.displays:
                sig = R.LADDER_MM if a.ms_ladder else (0.0,)
                for s in sig:
                    full = R.to_u8(R.blur_valid(rf, vl, s, vox))
                    for part, img, scale, py0, px0 in R.ms_images(full):
                        todo.append(('ms', st, s, part, img, scale, py0, px0))
        for kind, st, s, part, img, scale, py0, px0 in todo:
            u = names.next()
            png = R.png_bytes(img)
            with open(f'{a.out}/{u}.png', 'wb') as f:
                f.write(png)
            key[u] = {'window': wid, 'kind': kind, 'state': st, 'sigma_mm': s, 'part': part, 'scale': scale,
                      'y0': py0, 'x0': px0}
            man[u] = R.sha256(png)
    fd = os.open(a.key, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump({'provenance': R.PROV, 'images': key}, f, indent=1)
    t = json.dumps({'provenance': R.PROV, 'which': a.which, 'seed': a.seed, 'voxel_um': vox, 'displays': a.displays,
                    'states': a.states, 'n_images': len(man), 'images_sha256': man, 'windows': infos}, indent=1) + '\n'
    open(a.manifest, 'w').write(t)
    print(json.dumps({'n_windows': len(infos), 'n_images': len(man)}))


if __name__ == '__main__':
    main()
