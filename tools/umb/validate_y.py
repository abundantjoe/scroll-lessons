#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UMB-1 / A1 bars in the y frame (sections = xz planes, estimator = topological core). Reads <out>/slabs.json (fields
pass, point cross-check), topo.json, umbilicus.json (spline from topo), slit_crossings.json (M5b), fields.npz (M7b).
Bars that need a product not decodable in this frame (M6 lasagna in-plane xy normals, the old xy-centroid axis) are
reported as 'not computable in this frame', never approximated. Writes <out>/validation.json.
usage: validate_y.py <out_dir> [--vox_um 69.12] [--min_conf 0.5]
"""
import argparse, json, os, numpy as np

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--vox_um', type=float, default=69.12); ap.add_argument('--min_conf', type=float, default=0.5)
    a = ap.parse_args(); mm = 1000.0 / a.vox_um; O = a.out; S = json.load(open(os.path.join(O, 'slabs.json'))); T = json.load(open(os.path.join(O, 'topo.json')))['sections']; U = json.load(open(os.path.join(O, 'umbilicus.json'))); F = np.load(os.path.join(O, 'fields.npz'))
    X = json.load(open(os.path.join(O, 'slit_crossings.json'))) if os.path.exists(os.path.join(O, 'slit_crossings.json')) else []
    V = {}; bar = lambda name, value, ok, note='': V.__setitem__(name, {'value': value, 'pass': (None if ok is None else bool(ok)), 'note': note})
    byz = {r['z_mid']: r for r in S['slabs']}; mask_slabs = [r for r in S['slabs'] if r.get('mask_area_vox', 0) >= 2000]; ok = [t for t in T if t.get('status') == 'ok']; clean = [t for t in ok if (t.get('confidence') or 0) >= a.min_conf]
    cov = len(clean) / max(len(mask_slabs), 1); bar('coverage_clean_frac', round(cov, 4), cov >= 0.5, f'{len(clean)} clean of {len(mask_slabs)} slabs with mask; {len(ok)} with a defect found')
    kinds = {}; 
    for t in ok: kinds[t['kind']] = kinds.get(t['kind'], 0) + 1
    V['kinds'] = kinds
    if clean:
        q = lambda k: np.array([t[k] for t in clean if t.get(k) is not None], float)
        bar('topo_index_total_clean_min', round(float(q('index_total').min()), 3), q('index_total').min() >= 0.75, 'director index enclosed about the core (ellipse for slits)')
        bar('M4_split_half_proxy_max_shift_mm_p95', round(float(np.percentile(q('max_shift_mm'), 95)), 3), np.percentile(q('max_shift_mm'), 95) <= 0.4, 'core shift across loop radii (stability), the frame\'s split-half analogue')
        hfl = np.array([byz[t['z_mid']].get('half_first_last_mm') for t in clean if byz.get(t['z_mid'], {}).get('half_first_last_mm') is not None], float)
        if len(hfl): bar('M4_first_last_half_median_mm', round(float(np.median(hfl)), 3), np.median(hfl) <= 0.15, 'point cross-check centres of the first vs last 8 sections (point model: cross-check only)')
        # M2 / M1 in this frame come from the point cross-check, which is ill-conditioned in a flattened stack: reported, not scored
        res = np.array([byz[t['z_mid']].get('median_resid_mm') for t in clean if byz.get(t['z_mid'], {}).get('median_resid_mm') is not None], float)
        if len(res): V['point_model_resid_mm_clean_median'] = {'value': round(float(np.median(res)), 3), 'pass': None, 'note': 'concurrency point model is ill-conditioned for a flattened stack (parallel normals); cross-check only'}
        # M7a decoy: image centre
        dic = np.array([np.hypot(t['core'][0] - S['image_centre'][0], t['core'][1] - S['image_centre'][1]) / mm for t in clean]); dmc = np.array([np.hypot(t['core'][0] - byz[t['z_mid']]['mask_centroid'][0], t['core'][1] - byz[t['z_mid']]['mask_centroid'][1]) / mm for t in clean if 'mask_centroid' in byz.get(t['z_mid'], {})])
        sus = (dic < 0.3) & (dmc > 2.0) if len(dmc) == len(dic) else np.zeros(len(dic), bool); run_mm = 0.0
        if sus.any():
            zs = np.sort(np.array([t['z_mid'] for t in clean])[sus]); runs = np.split(zs, np.nonzero(np.diff(zs) > 1.5 * S['slab'])[0] + 1); run_mm = max((r_[-1] - r_[0] + S['slab']) / mm for r_ in runs)
        bar('M7a_rotation_centre_decoy_run_mm', round(float(run_mm), 2), run_mm <= 10.0)
    # M7b: z-stationarity of the normal-angle field between sections 10 mm apart (along y here); stripes would correlate
    th, adm, zmid = F['theta'], F['adm'], F['z_mid']; step = max(1, int(round(10 * mm / S['slab']))); cors = []
    for i in range(len(zmid) - step):
        m = adm[i] & adm[i + step]
        if m.sum() < 2000: continue
        cors.append(float(np.cos(2 * (th[i][m] - th[i + step][m])).mean()))
    if cors: bar('M7b_angle_field_stationarity_median', round(float(np.median(cors)), 3), np.median(cors) < 0.3, f'{len(cors)} section pairs 10 mm apart along y; note: a flattened stack has genuinely similar orientation fields along y, so this bar is reported with that caveat')
    bar('M8_smoothing_sensitivity_mm', U.get('smoothing_sensitivity_mm'), (U.get('smoothing_sensitivity_mm') or 0) <= 0.2); bar('M8_breaks', len(U.get('breaks', [])), all(c['jump_mm'] >= 1.0 for c in U.get('break_candidates', []) if c.get('accepted')), f"candidates {len(U.get('break_candidates', []))}")
    # M5b from slit_crossings.json
    if X:
        xc = [x for x in X if any(abs(x['z_mid'] - t['z_mid']) < 1e-6 for t in clean)]
        if xc:
            bf = np.array([x['balanced_frac'] for x in xc]); sp = np.array([x['total_spread'] for x in xc]); bar('M5b_up_down_balanced_frac_clean_median', round(float(np.median(bf)), 2), np.median(bf) >= 0.8, f'{len(xc)} clean sections'); bar('M5b_total_spread_clean_median', round(float(np.median(sp)), 1), np.median(sp) <= 2)
            V['M5b_mean_total_crossings_clean'] = {'value': round(float(np.median([x['mean_total'] for x in xc])), 1), 'pass': None, 'note': 'median over clean sections of the mean up+down layer crossings along the slit (level 3 resolves packets, not single windings)'}
    bar('M6_lasagna_agreement', None, None, 'not computable in the y frame: the organizers\' lasagna field gives in-plane xy normals; no decodable 3-D normal; reported as such (A1 item 5)')
    bar('old_axis_agreement', None, None, 'void: the 19-point centroid axis was built in the xy frame (UMB-GEOMETRY-RESULT)')
    hard = [k for k, v in V.items() if isinstance(v, dict) and v.get('pass') is False]
    V['verdict'] = {'clean_sections': len(clean), 'mask_sections': len(mask_slabs), 'defect_found': len(ok), 'failed_bars': hard, 'PASS_clean_zone': (len(hard) == 0 and cov >= 0.5), 'frac_z_confident_spline': U.get('frac_z_confident')}
    json.dump(V, open(os.path.join(O, 'validation.json'), 'w'), indent=1); print(json.dumps(V, indent=0)[:3500])

if __name__ == '__main__': main()
