#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
Procedural scroll phantom at a chosen voxel size (default 69.12 um = PHerc0268 level 3) with a KNOWN axis, for the
umbilicus pipeline's unit test (DECL-UMB-1 bar M9). Nothing in it is learned or copied from any scan.
Contents: an Archimedean spiral sheet (pitch, thickness, air gaps) wound about a curved axis x(z), y(z) with an optional
kink (C0 break) at z_kink; a crushed zone [z_crush0, z_crush1] where the section is squeezed to aspect ratio `squash`
(elliptical windings, so normal lines are NOT concurrent there: the evolute test); random holes; bright debris grains;
concentric ring artefacts about an OFF-axis centre; Gaussian noise; everything outside a cylinder is masked to 0 like the
organizers' '-masked' volumes. Writes <out>.npy (uint8, z,y,x) and <out>.json (truth: axis per z, zones, parameters).
usage: phantom.py <out_prefix> [--shape 400 400 400] [--pitch_um 450] [--thick_um 150] [--seed 0]
"""
import argparse, json, numpy as np

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--shape', type=int, nargs=3, default=[400, 400, 400]); ap.add_argument('--vox_um', type=float, default=69.12)
    ap.add_argument('--pitch_um', type=float, default=450); ap.add_argument('--thick_um', type=float, default=150); ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--squash', type=float, default=0.5, help='aspect ratio (b/a) in the crushed zone'); ap.add_argument('--kink_vox', type=float, default=12.0, help='lateral C0 jump of the axis at z_kink, voxels')
    ap.add_argument('--flat', type=float, default=0.0, help='if > 0: a flattened roll (aspect = flat everywhere, with folds), i.e. the PHerc0268 geometry'); ap.add_argument('--axis', default='z', choices=['z', 'y'], help='roll axis of the written volume')
    a = ap.parse_args(); Z, Y, X = a.shape; rng = np.random.default_rng(a.seed); v = a.vox_um
    pitch, thick = a.pitch_um / v, a.thick_um / v                       # in voxels
    z = np.arange(Z); zk = int(0.62 * Z); zc0, zc1 = int(0.35 * Z), int(0.55 * Z)
    # true axis: smooth bend + a C0 kink at zk (shear plane)
    ax = X / 2 + 18 * np.sin(2 * np.pi * z / Z) + np.where(z >= zk, a.kink_vox, 0.0)
    ay = Y / 2 + 12 * np.cos(2 * np.pi * z / (0.7 * Z)) + np.where(z >= zk, -0.6 * a.kink_vox, 0.0)
    R_out = 0.42 * min(X, Y) if a.flat <= 0 else 0.42 * min(X, Y / a.flat); vol = np.zeros((Z, Y, X), np.float32)
    yy, xx = np.mgrid[0:Y, 0:X].astype(np.float32)
    for k in range(Z):
        dx, dy = xx - ax[k], yy - ay[k]
        # crushed zone: elliptical sections (squash along y), smooth ramp in/out over 10 slices
        s = 1.0
        if zc0 - 10 <= k <= zc1 + 10:
            t = min(1.0, (k - (zc0 - 10)) / 10.0) if k < zc0 else (min(1.0, ((zc1 + 10) - k) / 10.0) if k > zc1 else 1.0); s = 1 - (1 - a.squash) * t
        if a.flat > 0:                                                        # flattened roll: strong squash everywhere plus gentle folds of the stack (wavy strata)
            s = a.flat; dy = dy - 6.0 * np.sin(2 * np.pi * dx / 140.0 + 0.3 * k / 17.0) * np.clip(np.abs(dx) / 60.0, 0, 1)
        r = np.hypot(dx, dy / s); th = np.arctan2(dy / s, dx)
        # Archimedean spiral: sheet where (r - pitch*theta/2pi) mod pitch < thick ; one turn per pitch
        phase = (r - pitch * th / (2 * np.pi)) % pitch
        tloc = thick * np.sqrt(np.cos(th) ** 2 + np.sin(th) ** 2 / (s * s)) if s < 1 else thick   # keep the PHYSICAL sheet thickness after the squash (only the gaps compress)
        sheet = (phase < tloc) & (r > 1.5 * pitch) & (r < R_out)
        img = np.where(sheet, 0.72, 0.30).astype(np.float32)            # papyrus vs air/ash contrast (uint8 scale 0..1)
        img[r >= R_out] = 0.0                                             # masked outside the roll
        vol[k] = img
    # holes in the sheet (5% of sheet voxels in random 3-voxel blobs), debris grains (bright, 2-4 voxel), rings about an off-axis centre
    holes = rng.random(vol.shape) < 0.004; vol[holes & (vol > 0.5)] = 0.30
    ng = 60; gz, gy, gx = rng.integers(0, Z, ng), rng.integers(0, Y, ng), rng.integers(0, X, ng)
    for i in range(ng):
        if vol[gz[i], gy[i], gx[i]] > 0: vol[max(0, gz[i] - 1):gz[i] + 2, max(0, gy[i] - 2):gy[i] + 2, max(0, gx[i] - 2):gx[i] + 2] = 1.0
    rc = (X / 2 + 30, Y / 2 - 25); rr = np.hypot(xx - rc[0], yy - rc[1]); rings = 0.04 * np.sin(2 * np.pi * rr / 6.3)
    vol += rings[None] * (vol > 0); vol += rng.normal(0, 0.05, vol.shape).astype(np.float32) * (vol > 0)
    out = np.clip(vol * 255, 0, 255).astype(np.uint8)
    if a.axis == 'y': out = np.ascontiguousarray(out.transpose(1, 0, 2))      # written as (z, y, x) with the roll axis along y: section k becomes y = k, its rows z, its columns x
    np.save(a.out + '.npy', out)
    json.dump({'vox_um': v, 'shape': [Z, Y, X], 'axis': a.axis, 'flat': a.flat, 'axis_x': ax.round(3).tolist(), 'axis_y': ay.round(3).tolist(), 'z_kink': zk, 'kink_vox': a.kink_vox, 'crush_zone': [zc0, zc1], 'squash': a.squash,
               'pitch_vox': pitch, 'thick_vox': thick, 'R_out_vox': R_out, 'ring_centre_xy': list(rc), 'n_debris': ng, 'seed': a.seed}, open(a.out + '.json', 'w'))
    print('phantom', out.shape, 'pitch', round(pitch, 2), 'thick', round(thick, 2), 'kink at', zk, 'crush', zc0, zc1)

if __name__ == '__main__': main()
