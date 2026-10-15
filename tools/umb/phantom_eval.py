#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
Score st_axis.py (and, if present, axis_spline.py) output against a phantom's known axis (DECL-UMB-1 bar M9).
usage: phantom_eval.py <phantom.json> <out_dir with slabs.json [umbilicus.json]> <report.json>
"""
import json, sys, numpy as np

def main():
    truth = json.load(open(sys.argv[1])); D = sys.argv[2]; S = json.load(open(f'{D}/slabs.json'))['slabs']; v = truth['vox_um']; mm = 1000.0 / v
    ax, ay = np.array(truth['axis_x']), np.array(truth['axis_y']); zc0, zc1 = truth['crush_zone']; zk = truth['z_kink']
    rows = []
    for r in S:
        if r.get('status') != 'ok': rows.append({'z0': r['z0'], 'status': r['status']}); continue
        zm = int(round(r['z_mid'])); zone = 'crushed' if zc0 <= zm <= zc1 else ('ramp' if (zc0 - 10 <= zm < zc0 or zc1 < zm <= zc1 + 10) else 'clean'); kink = r['z0'] <= zk < r['z1']
        err = float(np.hypot(r['centre'][0] - ax[zm], r['centre'][1] - ay[zm])) / mm
        rows.append({'z0': r['z0'], 'zone': zone, 'spans_kink': kink, 'model': r.get('model'), 'err_mm': round(err, 4), 'confidence': r.get('confidence'), 'resid_mm': r.get('median_resid_mm'), 'multi_centre': r.get('multi_centre'), 'aspect_s': (r.get('metric_model') or {}).get('aspect_s')})
    def stat(zone, key='err_mm'):
        e = [x[key] for x in rows if x.get('zone') == zone and not x.get('spans_kink') and x.get(key) is not None]
        return {'n': len(e), 'median': round(float(np.median(e)), 4), 'max': round(float(np.max(e)), 4)} if e else {'n': 0}
    rep = {'clean': stat('clean'), 'crushed': stat('crushed'), 'ramp': stat('ramp'), 'clean_conf': stat('clean', 'confidence'), 'crushed_conf': stat('crushed', 'confidence'),
           'crushed_models': sorted(set(x.get('model') for x in rows if x.get('zone') == 'crushed')), 'true_squash': truth['squash'], 'est_aspect_crushed': [x['aspect_s'] for x in rows if x.get('zone') == 'crushed' and x.get('aspect_s')],
           'bars': {'clean_err_le_0p15mm': stat('clean')['max'] <= 0.15 if stat('clean')['n'] else None, 'crushed_err_le_0p5mm': stat('crushed')['max'] <= 0.5 if stat('crushed')['n'] else None}, 'rows': rows}
    try:
        U = json.load(open(f'{D}/umbilicus.json')); zz = np.array(U['z']); ux, uy = np.array(U['x']), np.array(U['y']); e = np.hypot(ux - ax[zz.astype(int)], uy - ay[zz.astype(int)]) / mm
        clean = np.array([(z < zc0 - 10 or z > zc1 + 10) and abs(z - zk) > 20 for z in zz]); rep['spline'] = {'clean_median_mm': round(float(np.median(e[clean])), 4), 'clean_p95_mm': round(float(np.percentile(e[clean], 95)), 4), 'all_max_mm': round(float(e.max()), 4), 'breaks': U.get('breaks'), 'true_kink': zk,
                                                                                                                       'kink_localised_within_mm': (min(abs(np.array(U.get('breaks', [])) - zk)) / mm if U.get('breaks') else None)}
    except FileNotFoundError: pass
    json.dump(rep, open(sys.argv[3], 'w'), indent=1); print(json.dumps({k: rep[k] for k in rep if k != 'rows'}))

if __name__ == '__main__': main()
