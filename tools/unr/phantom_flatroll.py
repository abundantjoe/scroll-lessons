#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UMB-2 bar B6 (+ A1 item 3): a FLATTENED-ROLL phantom at the scan's native 8.64 um geometry, written as a y-slab of xz
sections (the frame of DECL-UMB-2: sections are xz planes indexed by y, windings stacked along z, hairpin columns at the x
edges). Geometry only; nothing here is an ink or letter claim.

Model: winding k (0 = innermost) is a stadium: two straight arms at z = zc +- r_k between the two end centres (x_cL, zc) and
(x_cR, zc) and two semicircular ends of radius r_k = r_in + k * pitch about those centres (concentric nested U-turns, the
only non-crossing nesting with one pitch of spacing: the innermost apex is the deepest, at depth R_max - r_in from each edge,
and the outer U-turns are wide arcs). Width = x_cR - x_cL + 2 R_max (set by --width_mm); thickness = 2 R_max.
Seams: the windings are grouped into lobes (lobe thickness 1-4 mm); each lobe's end arcs on each side are shifted by a random
(dz, dx) of up to --seam_shift pitches, and a dark gap (the delamination) is cut between lobes along each column; the nesting is
monotone within a lobe only. Along y the section drifts slowly (zc(y), x_c(y)): the truth is per section. Debris specks,
per-column stripes (as the raw scans show), Gaussian noise, blur 1.2 vox; outside the outer winding is 0 (mask).
usage: phantom_flatroll.py <out.npy> <truth.json> [--n_sec 16] [--n_wind 42] [--pitch_um 450] [--sheet_um 150] [--width_mm 50]
       [--r_in_um 2000] [--seam_mm 2.5] [--seam_shift 1.5] [--noise 0.12] [--seed 0] [--png preview.png]
truth.json per section y: zc (vox), apex_left/right (z, x), slit = [x_left_apex, x_right_apex], x_edges; lobes, shifts, params."""
import argparse, json, numpy as np
from scipy import ndimage as ndi
VOX = 8.64

def section(Z, X, zc, xcL, xcR, radii, sheet, lobes, shifts, rng, p, zz=None, xx=None):
    """One xz section rasterised per winding on bounding boxes (arms: row bands per column; arcs: the end's bounding slab)."""
    img = np.zeros((Z, X), np.float32); half = sheet / 2; hw = int(np.ceil(half)); mm = p['mm']
    xa = np.arange(int(np.floor(xcL)), int(np.ceil(xcR)) + 1); xa = xa[(xa >= 0) & (xa < X)]
    wL = np.clip((xa - xcL) / (3.0 * mm), 0, 1); wR = np.clip((xcR - xa) / (3.0 * mm), 0, 1)
    def arc(xc, dz, dx, r, val, side):
        z0, z1 = max(0, int(zc + dz - r - hw - 2)), min(Z, int(zc + dz + r + hw + 3))
        x0, x1 = (max(0, int(xc + dx - r - hw - 2)), min(X, int(np.ceil(xc)) + 1)) if side == 'L' else (max(0, int(np.floor(xc))), min(X, int(xc + dx + r + hw + 3)))
        if z1 <= z0 or x1 <= x0: return
        zs, xs = np.ogrid[z0:z1, x0:x1]; d = np.abs(np.hypot(zs - (zc + dz), xs - (xc + dx)) - r)
        sel = d < half if val is not None else d < p['gap_half']; sel &= (xs < xc) if side == 'L' else (xs > xc)
        sub = img[z0:z1, x0:x1]; sub[sel] = val if val is not None else 0.0
    for k, r in enumerate(radii):
        (dzL, dxL), (dzR, dxR) = shifts[lobes[k]]; val = 0.8 + 0.2 * rng.random(); dz_arm = dzL * (1 - wL) + dzR * (1 - wR)
        for zrow in (zc - r + dz_arm, zc + r + dz_arm):
            zi = np.rint(zrow).astype(int)
            for o in range(-hw, hw + 1):
                zo = zi + o; ok = (zo >= 0) & (zo < Z) & (np.abs(zo - zrow) < half); img[zo[ok], xa[ok]] = val
        arc(xcL, dzL, dxL, r, val, 'L'); arc(xcR, dzR, dxR, r, val, 'R')
    for b in range(1, len(shifts)):                                                                   # delamination gaps between lobes, through the arcs only
        kb = lobes.index(b); rb = radii[kb] - p['pitch'] / 2; arc(xcL, shifts[b][0][0], shifts[b][0][1], rb, None, 'L'); arc(xcR, shifts[b][1][0], shifts[b][1][1], rb, None, 'R')
    r0, rN = radii[0], radii[-1]; (dzL, dxL), (dzR, dxR) = shifts[lobes[0]]
    apexL = (zc + dzL, xcL + dxL - r0); apexR = (zc + dzR, xcR + dxR + r0)
    zs, xs = np.ogrid[0:Z, 0:X]
    outer = ((xs >= xcL) & (xs <= xcR) & (np.abs(zs - zc) <= rN + half)) | (np.hypot(zs - zc, xs - xcL) <= rN + half) | (np.hypot(zs - zc, xs - xcR) <= rN + half)
    return img, apexL, apexR, outer

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('truth'); ap.add_argument('--n_sec', type=int, default=16); ap.add_argument('--n_wind', type=int, default=42); ap.add_argument('--pitch_um', type=float, default=450); ap.add_argument('--sheet_um', type=float, default=150)
    ap.add_argument('--width_mm', type=float, default=50.0); ap.add_argument('--r_in_um', type=float, default=2000); ap.add_argument('--seam_mm', type=float, default=2.5); ap.add_argument('--seam_shift', type=float, default=1.5); ap.add_argument('--noise', type=float, default=0.12); ap.add_argument('--debris', type=int, default=300); ap.add_argument('--stripe', type=float, default=0.06); ap.add_argument('--seed', type=int, default=0); ap.add_argument('--png', default=None); ap.add_argument('--margin_mm', type=float, default=1.5)
    a = ap.parse_args(); rng = np.random.default_rng(a.seed); mm = 1000.0 / VOX; pitch, sheet, r_in = a.pitch_um / VOX, a.sheet_um / VOX, a.r_in_um / VOX
    radii = [r_in + k * pitch for k in range(a.n_wind)]; Rmax = radii[-1]; thick = 2 * Rmax; width = a.width_mm * mm; L_arm = width - 2 * Rmax
    assert L_arm > 4 * pitch, f'width {a.width_mm} mm too small for 2 R_max = {2 * Rmax / mm:.1f} mm'
    m = int(a.margin_mm * mm); Z = int(thick + 2 * m + 4 * pitch); X = int(width + 2 * m + 2 * pitch); zc0 = Z / 2; xcL0 = m + pitch + Rmax; xcR0 = xcL0 + L_arm
    lobes = []; b = 0; acc = 0.0
    for k in range(a.n_wind):
        lobes.append(b); acc += pitch
        if acc >= a.seam_mm * mm * (0.5 + rng.random()): b += 1; acc = 0.0
    n_lobes = max(lobes) + 1; shifts = [((0.0, 0.0), (0.0, 0.0))] + [((rng.uniform(-1, 1) * a.seam_shift * pitch, rng.uniform(-0.5, 0.5) * a.seam_shift * pitch), (rng.uniform(-1, 1) * a.seam_shift * pitch, rng.uniform(-0.5, 0.5) * a.seam_shift * pitch)) for _ in range(n_lobes - 1)]
    p = {'mm': mm, 'pitch': pitch, 'gap_half': 1.0 * sheet}
    V = np.zeros((Z, a.n_sec, X), np.uint8); truth = {'vox_um': VOX, 'pitch_vox': pitch, 'sheet_vox': sheet, 'n_wind': a.n_wind, 'radii_vox': radii, 'width_vox': width, 'thickness_vox': thick, 'n_lobes': n_lobes, 'lobes': lobes, 'shifts_vox': shifts, 'shape_zyx': [Z, a.n_sec, X], 'sections': []}
    stripes = 1.0 + a.stripe * rng.standard_normal(X).astype(np.float32)
    for y in range(a.n_sec):
        zc = zc0 + 0.3 * pitch * np.sin(2 * np.pi * y / 40.0); xcL = xcL0 + 0.2 * pitch * np.cos(2 * np.pi * y / 50.0); xcR = xcR0 + 0.2 * pitch * np.cos(2 * np.pi * y / 50.0)
        img, apexL, apexR, outer = section(Z, X, zc, xcL, xcR, radii, sheet, lobes, shifts, rng, p)
        for _ in range(a.debris):
            zd, xd = rng.integers(0, Z), rng.integers(0, X)
            if outer[zd, xd]: img[max(0, zd - 2):zd + 3, max(0, xd - 2):xd + 3] = 1.0
        img = ndi.gaussian_filter(img, 1.2) * stripes[None, :] + a.noise * rng.standard_normal((Z, X)).astype(np.float32)
        img = np.clip(0.15 + 0.7 * img, 0, 1); img[~outer] = 0.0; V[:, y, :] = np.clip(img * 255, 1, 255).astype(np.uint8) * outer; del img, outer
        truth['sections'].append({'y': y, 'zc': float(0.5 * (apexL[0] + apexR[0])), 'zc_ideal': float(zc), 'apex_left': [float(apexL[0]), float(apexL[1])], 'apex_right': [float(apexR[0]), float(apexR[1])], 'slit': [float(apexL[1]), float(apexR[1])], 'x_edges': [float(xcL - Rmax), float(xcR + Rmax)]})
    truth['axis_y'] = {s['y']: s['zc'] for s in truth['sections']}
    np.save(a.out, V); json.dump(truth, open(a.truth, 'w'), indent=1)
    print(json.dumps({'shape_zyx': [Z, a.n_sec, X], 'MB': round(V.nbytes / 1e6), 'n_lobes': n_lobes, 'innermost_depth_mm': round((Rmax - r_in) / mm, 2), 'outer_radius_mm': round(Rmax / mm, 2), 'width_mm': round(width / mm, 1), 'thickness_mm': round(thick / mm, 1)}))
    if a.png:
        from PIL import Image; s4 = V[::4, a.n_sec // 2, ::4]; Image.fromarray(s4).save(a.png)

if __name__ == '__main__': main()
