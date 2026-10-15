#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UMB-1 item 3: score the PHerc0268 axis against every declared bar and write validation.json (pass/fail per bar,
numbers, zone coverage, overall verdict). Inputs: <out>/slabs.json, <out>/umbilicus.json, <out>/fields.npz; level-4 CT
(mask) and the organizers' lasagna nx/ny at level 4 (.npy, independent product, M6); the old centroid axis (M5 comparison).
usage: validate.py <out_dir> --ct_l4 ct_L4.npy --nx las_nx_L4.npy --ny las_ny_L4.npy [--old_axis logs/fl4/seeds_inner_PHerc0268.json] [--vox_um 69.12]
"""
import argparse, json, os, numpy as np
from scipy import ndimage as ndi
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from st_axis import ray_crossings

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--ct_l4', required=True); ap.add_argument('--nx', required=True); ap.add_argument('--ny', required=True); ap.add_argument('--old_axis', default=None); ap.add_argument('--vox_um', type=float, default=69.12); ap.add_argument('--min_conf', type=float, default=0.5)
    a = ap.parse_args(); mm = 1000.0 / a.vox_um; S = json.load(open(os.path.join(a.out, 'slabs.json'))); U = json.load(open(os.path.join(a.out, 'umbilicus.json'))); F = np.load(os.path.join(a.out, 'fields.npz'))
    slabs = [r for r in S['slabs'] if r.get('status') == 'ok']; clean = [r for r in slabs if (r.get('confidence') or 0) >= a.min_conf]; V = {}
    def bar(name, value, ok, note=''): V[name] = {'value': value, 'pass': bool(ok), 'note': note}
    zr = [r['z_mid'] for r in slabs if r['mask_area_vox'] > 0]; n_mask_slabs = sum(1 for r in S['slabs'] if r.get('mask_area_vox', 0) >= 2000)
    cov_frac = len(clean) / max(n_mask_slabs, 1); bar('coverage_clean_frac', round(cov_frac, 4), cov_frac >= 0.5, f'{len(clean)} clean of {n_mask_slabs} slabs with mask')
    if clean:
        q = lambda k: np.array([r[k] for r in clean if r.get(k) is not None], float)
        bar('M2_median_resid_mm_clean_max', round(float(q('median_resid_mm').max()), 4), q('median_resid_mm').max() <= 0.35)
        bar('M1_sector_coverage_clean_min', round(float(q('sector_coverage_0p5mm').min()), 4), q('sector_coverage_0p5mm').min() >= 0.75)
        sh = q('split_half_mm'); bar('M4_split_half_median_mm', round(float(np.median(sh)), 4), np.median(sh) <= 0.15); bar('M4_split_half_p95_mm', round(float(np.percentile(sh, 95)), 4), np.percentile(sh, 95) <= 0.4)
        pt = [r for r in clean if r.get('model') == 'point']
        if pt:
            cd = np.array([r['conditioning'] for r in pt]); sp = np.array([r['multistart_spread_mm'] for r in pt]); bar('conditioning_clean_min', round(float(cd.min()), 4), cd.min() >= 0.3); bar('basin_spread_clean_max_mm', round(float(sp.max()), 4), sp.max() <= 0.2)
        rc = [r['ray_crossings'] for r in clean if r.get('ray_crossings')]; adj = np.array([x['adjacent_diff_le1_frac'] for x in rc]); spr = np.array([x['spread_rel'] for x in rc if x['spread_rel'] is not None])
        bar('M5_adjacent_ray_le1_frac_clean_min', round(float(adj.min()), 3), (adj >= 0.9).all(), 'level-3 slab means, our axis'); bar('M5_spread_rel_clean_max', round(float(spr.max()), 3), (spr <= 0.10).all())
        # M7a decoy: image-centre proximity while the mask centroid is far
        dic = np.array([r['dist_to_image_centre_mm'] for r in clean]); dmc = np.array([np.hypot(r['centre'][0] - r['mask_centroid'][0], r['centre'][1] - r['mask_centroid'][1]) / mm for r in clean]); z_cl = np.array([r['z_mid'] for r in clean])
        sus = (dic < 0.3) & (dmc > 2.0); run_mm = 0.0
        if sus.any():
            zs = np.sort(z_cl[sus]); runs = np.split(zs, np.nonzero(np.diff(zs) > 1.5 * S['slab'])[0] + 1); run_mm = max((r_[-1] - r_[0] + S['slab']) / mm for r_ in runs)
        bar('M7a_rotation_centre_decoy_run_mm', round(float(run_mm), 2), run_mm <= 10.0, 'longest z-run of axis within 0.3 mm of the image centre while the mask centroid is > 2 mm away')
    # M7b z-stationarity of the normal-angle field: correlation between slabs 10 mm apart (ring artefacts would give ~1)
    th, adm, zmid = F['theta'], F['adm'], F['z_mid']; step = int(round(10 * mm / S['slab'])); cors = []
    for i in range(len(zmid) - step):
        m = adm[i] & adm[i + step]
        if m.sum() < 2000: continue
        d = np.cos(2 * (th[i][m] - th[i + step][m])); cors.append(float(d.mean()))          # axial angles: cos(2 delta) in [-1,1]
    if cors: bar('M7b_angle_field_z_stationarity_median', round(float(np.median(cors)), 3), np.median(cors) < 0.3, f'{len(cors)} slab pairs 10 mm apart')
    # M8 from the spline stage
    bar('M8_smoothing_sensitivity_mm', U.get('smoothing_sensitivity_mm'), (U.get('smoothing_sensitivity_mm') or 0) <= 0.2)
    bad_breaks = [c for c in U.get('break_candidates', []) if c.get('accepted') and not (c['jump_mm'] >= 1.0)]; bar('M8_breaks_coincide_with_jumps', len(U.get('breaks', [])), len(bad_breaks) == 0, f"{len(U.get('breaks', []))} accepted breaks")
    # M6 organizers' lasagna normals (level 4, independent product) vs the radial direction to our axis, per clean slab
    ct4 = np.load(a.ct_l4, mmap_mode='r'); nx4 = np.load(a.nx, mmap_mode='r'); ny4 = np.load(a.ny, mmap_mode='r'); Z4, Y4, X4 = ct4.shape; yy, xx = np.mgrid[0:Y4, 0:X4]; m6 = []
    X_, Y_ = np.array(U['x']), np.array(U['y']); conf = np.array(U['confidence'])
    for r in clean:
        z4 = int(round(r['z_mid'] / 2)); 
        if not (0 <= z4 < Z4): continue
        u = np.asarray(nx4[z4]).astype(np.float32) / 127.5 - 1; w = np.asarray(ny4[z4]).astype(np.float32) / 127.5 - 1; nrm = np.hypot(u, w); msk = ndi.binary_erosion(np.asarray(ct4[z4]) > 0, iterations=7)
        cx, cy = r['centre'][0] / 2, r['centre'][1] / 2; rx, ry = xx - cx, yy - cy; rn = np.hypot(rx, ry) + 1e-9; sel = msk & (nrm > 0.5) & (rn > 2 * mm / 2)
        if sel.sum() < 1000: continue
        ang = np.degrees(np.arccos(np.clip(np.abs(u * rx + w * ry) / (nrm * rn), 0, 1)))[sel]; m6.append({'z_mid': r['z_mid'], 'median_angle_deg': round(float(np.median(ang)), 2), 'frac_gt30': round(float((ang > 30).mean()), 3), 'n': int(sel.sum())})
    if m6:
        med = np.array([x['median_angle_deg'] for x in m6]); bar('M6_lasagna_median_angle_deg_clean_median', round(float(np.median(med)), 2), np.median(med) <= 15.0, f'per-slab medians: max {med.max():.1f}'); V['M6_per_slab'] = m6
    # old centroid axis: agreement in the clean zone and the same M5 test on level-4 slab means for both axes
    if a.old_axis and os.path.exists(a.old_axis):
        cps = json.load(open(a.old_axis))['axis_points']; zs = np.array([p['z'] for p in cps]); o = np.argsort(zs); ox = np.array([p['x'] for p in cps])[o] / 8; oy = np.array([p['y'] for p in cps])[o] / 8; zs = zs[o] / 8   # level 0 -> level 3
        dd = []; m5 = {'ours': [], 'old': []}
        for r in clean:
            zm = r['z_mid']
            if zm < zs.min() or zm > zs.max(): continue
            oxz, oyz = np.interp(zm, zs, ox), np.interp(zm, zs, oy); dd.append(float(np.hypot(r['centre'][0] - oxz, r['centre'][1] - oyz)) / mm)
            z4 = int(round(zm / 2)); img = np.asarray(ct4[max(0, z4 - 4):z4 + 4]).astype(np.float32).mean(0) / 255; mk = ndi.binary_erosion(img > 0, iterations=7)
            for key, (cx, cy) in [('ours', (r['centre'][0] / 2, r['centre'][1] / 2)), ('old', (oxz / 2, oyz / 2))]:
                cnt = ray_crossings(img, mk, (cx, cy)); nz = [c for c in cnt if c > 0]
                if nz: m5[key].append({'adj_le1': float(np.mean([abs(cnt[i] - cnt[(i + 1) % len(cnt)]) <= 1 for i in range(len(cnt))])), 'spread_rel': (max(nz) - min(nz)) / max(np.mean(nz), 1)})
        if dd: bar('old_axis_agreement_clean_median_mm', round(float(np.median(dd)), 3), np.median(dd) <= 1.5, f'max {max(dd):.2f} mm (reported)')
        V['M5_level4_comparison'] = {k: {'adj_le1_median': round(float(np.median([x['adj_le1'] for x in v])), 3), 'spread_rel_median': round(float(np.median([x['spread_rel'] for x in v])), 3), 'n': len(v)} for k, v in m5.items() if v}
    hard = [k for k, v in V.items() if isinstance(v, dict) and 'pass' in v and not v['pass'] and not k.startswith('old_axis') and not k.startswith('M6')]
    V['verdict'] = {'clean_slabs': len(clean), 'mask_slabs': n_mask_slabs, 'failed_bars': hard, 'PASS_clean_zone': len(hard) == 0 and cov_frac >= 0.5}
    json.dump(V, open(os.path.join(a.out, 'validation.json'), 'w'), indent=1); print(json.dumps({k: (v if not isinstance(v, list) else f'{len(v)} rows') for k, v in V.items()}, indent=0)[:4000])

if __name__ == '__main__': main()
