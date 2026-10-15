#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UMB-1-A2 (topological estimator): the axis of a folded, flattened stack is the singularity of the layer-orientation
(director) field, found from LOCAL orientation differences along closed loops, with no long lever arm. Per section (from
st_axis.py's fields.npz: axial angle theta, coherence, admissible mask at a stride), the doubled field q = coh e^{2i theta}
is smoothed; the director index of a loop of radius R about a grid point is (1 / 4 pi) sum of wrapped increments of
arg(q) along the loop. A point core gives +1, a slit core gives two +1/2 ends; folds, cracks and debris give +-1/2 pairs
that cancel once R exceeds their size. Multi-radius: the core must hold at R = 4 and 8 mm (shift <= 0.5 mm); the index
map at R = 2 mm localises it. Output <out>/topo.json: per section the core (x, y) [section coordinates], slit ends if two
half-defects, index values per radius, stability, confidence.
usage: topo_axis.py <out_dir of st_axis.py> [--vox_um 69.12] [--radii_mm 2 4 8]
"""
import argparse, json, os, numpy as np
from scipy import ndimage as ndi

def index_map(theta, coh, adm, stride_vox, R_vox, nsamp=64, sigma_frac=0.25):
    """Director index of loops of radius R (voxels) about every grid point; NaN where the loop leaves the admissible region."""
    valid = coh > 1e-6                                                       # inside the mask (the tensor is exactly zero outside); the admissible gate is not used for topology
    qr, qi = coh * np.cos(2 * theta) * valid, coh * np.sin(2 * theta) * valid; sg = max(1.0, R_vox / stride_vox * sigma_frac)
    qr, qi = ndi.gaussian_filter(qr, sg), ndi.gaussian_filter(qi, sg); wgt = ndi.gaussian_filter(valid.astype(np.float32), sg)
    H, W = theta.shape; r = R_vox / stride_vox; ang = np.linspace(0, 2 * np.pi, nsamp, endpoint=False); yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    A = np.zeros((nsamp, H, W), np.float32); inside = np.ones((H, W), bool)
    for k, a in enumerate(ang):
        sy, sx = yy + r * np.sin(a), xx + r * np.cos(a); cr = ndi.map_coordinates(qr, [sy, sx], order=1, mode='constant', cval=0.0); ci = ndi.map_coordinates(qi, [sy, sx], order=1, mode='constant', cval=0.0)
        wk = ndi.map_coordinates(wgt, [sy, sx], order=1, mode='constant', cval=0.0); inside &= wk > 0.5; A[k] = np.arctan2(ci, cr)
    d = np.diff(np.concatenate([A, A[:1]], 0), axis=0); d = (d + np.pi) % (2 * np.pi) - np.pi; idx = d.sum(0) / (4 * np.pi)
    idx[~inside] = np.nan; return idx

def loop_index(theta, coh, R_vox, stride_vox, centre, a_vox, b_vox, phi, nsamp=128, sigma_frac=0.25):
    """Director index along ONE ellipse (semi-axes a, b voxels, orientation phi) about centre (x, y voxels); NaN if it leaves the field."""
    valid = coh > 1e-6; qr, qi = coh * np.cos(2 * theta) * valid, coh * np.sin(2 * theta) * valid; sg = max(1.0, R_vox / stride_vox * sigma_frac)
    qr, qi = ndi.gaussian_filter(qr, sg), ndi.gaussian_filter(qi, sg); wgt = ndi.gaussian_filter(valid.astype(np.float32), sg)
    t = np.linspace(0, 2 * np.pi, nsamp, endpoint=False); ex, ey = a_vox * np.cos(t), b_vox * np.sin(t); c, s_ = np.cos(phi), np.sin(phi)
    sx, sy = (centre[0] + c * ex - s_ * ey) / stride_vox, (centre[1] + s_ * ex + c * ey) / stride_vox
    cr, ci = ndi.map_coordinates(qr, [sy, sx], order=1), ndi.map_coordinates(qi, [sy, sx], order=1); wk = ndi.map_coordinates(wgt, [sy, sx], order=1)
    if (wk <= 0.5).any(): return np.nan
    A = np.arctan2(ci, cr); d = np.diff(np.concatenate([A, A[:1]])); d = (d + np.pi) % (2 * np.pi) - np.pi; return float(d.sum() / (4 * np.pi))

def refine_hole(img, valid, core, ends, stride_vox, mm, max_area_mm2=60.0):
    """Barycentre of the innermost gap: flood-fill the non-sheet class from the core inside a window; accept a compact hole."""
    if img is None: return None
    H, W = img.shape; cx, cy = core[0] / stride_vox, core[1] / stride_vox; r = int(round(12 * mm / stride_vox)); x0, x1, y0, y1 = max(0, int(cx) - r), min(W, int(cx) + r), max(0, int(cy) - r), min(H, int(cy) + r)
    win = img[y0:y1, x0:x1]; v = valid[y0:y1, x0:x1]
    if v.sum() < 50: return None
    thr = np.percentile(win[v], 50); gap = (win < thr) & v; lab, n = ndi.label(gap); ly, lx = int(cy) - y0, int(cx) - x0
    if not (0 <= ly < gap.shape[0] and 0 <= lx < gap.shape[1]): return None
    k = lab[ly, lx]
    if k == 0:                                                                # the core sits on a sheet: take the nearest gap component within 1 mm
        yy, xx = np.nonzero(gap); 
        if len(xx) == 0: return None
        j = np.argmin((yy - ly) ** 2 + (xx - lx) ** 2)
        if np.hypot(yy[j] - ly, xx[j] - lx) * stride_vox > 1.0 * mm: return None
        k = lab[yy[j], xx[j]]
    yy, xx = np.nonzero(lab == k); area = len(xx) * (stride_vox / mm) ** 2
    if area > max_area_mm2 or area < 0.05: return None
    return {'centre': [float((xx.mean() + x0) * stride_vox), float((yy.mean() + y0) * stride_vox)], 'area_mm2': round(float(area), 3), 'extent_x_mm': round(float(np.ptp(xx) * stride_vox / mm), 3), 'extent_y_mm': round(float(np.ptp(yy) * stride_vox / mm), 3)}

def plateaus(idx, lo, hi, min_cells=3):
    """Connected components of lo < idx <= hi: (centroid_x, centroid_y in grid cells, n_cells, mean index)."""
    m = np.isfinite(idx) & (idx > lo) & (idx <= hi); lab, n = ndi.label(m, structure=np.ones((3, 3))); out = []
    for k in range(1, n + 1):
        yy, xx = np.nonzero(lab == k)
        if len(xx) < min_cells: continue
        out.append((float(xx.mean()), float(yy.mean()), int(len(xx)), float(idx[lab == k].mean())))
    return sorted(out, key=lambda t: -t[2])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--vox_um', type=float, default=69.12); ap.add_argument('--radii_mm', type=float, nargs='+', default=[1, 2, 4, 8]); ap.add_argument('--slit_max_mm', type=float, default=30.0)
    a = ap.parse_args(); F = np.load(os.path.join(a.out, 'fields.npz')); TH, CO, AD, zmid, stride = F['theta'], F['coh'], F['adm'], F['z_mid'], int(F['stride']); mm = 1000.0 / a.vox_um; g = stride / mm   # mm per grid cell
    IM = F['img'] if 'img' in F.files else None
    S = json.load(open(os.path.join(a.out, 'slabs.json'))); recs = []; radii = sorted(a.radii_mm)
    for i in range(len(zmid)):
        th, co, ad = TH[i], CO[i], AD[i].astype(bool); rec = {'z_mid': float(zmid[i])}
        if (co > 1e-6).sum() < 200: rec['status'] = 'no field'; recs.append(rec); continue
        maps = {R: index_map(th, co, ad, stride, R * mm) for R in radii}
        rec['index_max_per_R'] = {str(R): (round(float(np.nanmax(maps[R])), 3) if np.isfinite(maps[R]).any() else None) for R in radii}
        # the core at the smallest radius that shows a +1 plateau (point) or two +1/2 plateaus (slit); its location = plateau centroid
        core, kind, slit, R_used = None, None, None, None
        for R in radii:
            P = plateaus(maps[R], 0.75, 1.6); Hh = plateaus(maps[R], 0.35, 0.75)
            if P: core = np.array(P[0][:2]) * stride; kind = 'point'; R_used = R; break
            if len(Hh) >= 2 and np.hypot(Hh[0][0] - Hh[1][0], Hh[0][1] - Hh[1][1]) * g <= a.slit_max_mm:
                e1, e2 = np.array(Hh[0][:2]) * stride, np.array(Hh[1][:2]) * stride; core = (e1 + e2) / 2; kind = 'slit'; slit = [e1.round(2).tolist(), e2.round(2).tolist()]; R_used = R; break
        if core is None: rec['status'] = 'no defect'; recs.append(rec); print(json.dumps(rec), flush=True); continue
        # stability: the plateau centroid at every other radius (nearest plateau to the core), as a shift in mm; total index enclosed at the largest radius
        stab = {}
        for R in radii:
            cands = plateaus(maps[R], 0.75, 1.6) + ([] if kind == 'point' else plateaus(maps[R], 0.35, 0.75))
            if kind == 'slit' and cands:
                hh = plateaus(maps[R], 0.35, 0.75)
                if len(hh) >= 2: cands = [((hh[0][0] + hh[1][0]) / 2, (hh[0][1] + hh[1][1]) / 2, hh[0][2] + hh[1][2], (hh[0][3] + hh[1][3]))]
            d = [(np.hypot(c[0] * stride - core[0], c[1] * stride - core[1]) / mm, c[3]) for c in cands]
            stab[str(R)] = min(d, key=lambda t: t[0]) if d else None
        Rl = radii[-1]; cy_, cx_ = int(round(core[1] / stride)), int(round(core[0] / stride)); tot = maps[Rl][cy_, cx_] if (0 <= cy_ < th.shape[0] and 0 <= cx_ < th.shape[1]) else np.nan
        if not np.isfinite(tot):                                               # the largest loop leaves the mask: use the largest radius whose map is finite at the core
            for R in reversed(radii):
                v = maps[R][cy_, cx_]
                if np.isfinite(v): tot, Rl = v, R; break
        ell = None
        if kind == 'slit':                                                     # a slit: the +1 charge is split; test it with an ellipse enclosing both ends (fits a thin stack)
            e1, e2 = np.array(slit[0]), np.array(slit[1]); dd = np.hypot(*(e2 - e1)); phi_s = float(np.arctan2(e2[1] - e1[1], e2[0] - e1[0])); R1 = radii[0] * mm
            vals = [loop_index(th, co, R1, stride, core, dd / 2 + f * R1, f * R1, phi_s) for f in (1.0, 1.5, 2.0)]; fin = [v for v in vals if np.isfinite(v)]
            ell = {'index_per_factor': [None if not np.isfinite(v) else round(v, 3) for v in vals]}
            if fin: tot, Rl = float(np.median(fin)), 'ellipse'
        hole = refine_hole(IM[i] if IM is not None else None, co > 1e-6, core, slit, stride, mm) if kind == 'slit' else None   # the gap barycentre helps only for a slit core (a point core is best located by its plateau)
        if hole is not None:
            hole['shift_from_topo_mm'] = round(float(np.hypot(hole['centre'][0] - core[0], hole['centre'][1] - core[1]) / mm), 3); sl_len = float(np.hypot(slit[1][0] - slit[0][0], slit[1][1] - slit[0][1]) / mm)
            hole['accepted'] = bool(0.3 * sl_len <= max(hole['extent_x_mm'], hole['extent_y_mm']) <= 1.5 * sl_len and hole['shift_from_topo_mm'] <= 1.5)   # the gap must be commensurate with the slit and near the topological core
            if hole['accepted']: core_topo = core.copy(); core = np.array(hole['centre'])
            else: hole = None
        shifts = [stab[str(R)][0] for R in radii if R != R_used and stab[str(R)] is not None]; missing = sum(1 for R in radii if R != R_used and stab[str(R)] is None)
        shift = max(shifts) if shifts else 9.9
        conf = float(np.clip(tot if np.isfinite(tot) else 0, 0, 1)) * (1.0 if shift <= 0.5 else 0.5 if shift <= 1.0 else 0.0) * (1.0 if missing <= 1 else 0.5)
        rec.update({'status': 'ok', 'kind': kind, 'core': [round(float(core[0]), 2), round(float(core[1]), 2)], 'core_topo': [round(float(core_topo[0]), 2), round(float(core_topo[1]), 2)] if hole is not None else None, 'hole': hole, 'ellipse_index': ell, 'R_used_mm': R_used, 'index_total_R': Rl, 'index_total': (round(float(tot), 3) if np.isfinite(tot) else None), 'slit_ends': slit,
                    'stability_mm': {k: (round(v[0], 3), round(v[1], 3)) if v else None for k, v in stab.items()}, 'max_shift_mm': round(float(shift), 3), 'radii_missing': missing, 'confidence': round(conf, 3)})
        recs.append(rec); print(json.dumps({k: rec.get(k) for k in ['z_mid', 'status', 'kind', 'core', 'R_used_mm', 'index_total', 'max_shift_mm', 'confidence']}), flush=True)
    json.dump({'src': S.get('src'), 'axis': S.get('axis'), 'vox_um': a.vox_um, 'radii_mm': radii, 'sections': recs}, open(os.path.join(a.out, 'topo.json'), 'w'), indent=1)

if __name__ == '__main__': main()
