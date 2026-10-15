#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UMB-1-A2 (fold skeleton = the owner's multi-point mini-umbilici): in every xz section, the +1/2 and -1/2 defects of
the layer-orientation (director) field are the fold axes of the stacked packets (a +1/2 at each hairpin tip, a -1/2
between consecutive hairpins). Each defect is located as the centroid of its index plateau at the SMALL radius R0 (local)
and must persist at R1 (stability); defects are tracked along y into lines by nearest-neighbour assignment within
`--link_mm`. Validation per line: index sign consistent, plateau found at both radii in >= 80 % of its sections, mean
step between consecutive sections <= link_mm / 2, length. Writes <out>/defects.json.
usage: topo_defects.py <out_dir of st_axis.py> [--vox_um 69.12] [--R0 3] [--R1 6] [--link_mm 2.5]
"""
import argparse, json, os, sys, numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from topo_axis import index_map

def comps(idx, lo, hi, min_cells):
    m = np.isfinite(idx) & (idx > lo) & (idx <= hi); lab, n = ndi.label(m, structure=np.ones((3, 3))); out = []
    for k in range(1, n + 1):
        yy, xx = np.nonzero(lab == k)
        if len(xx) < min_cells: continue
        out.append((float(xx.mean()), float(yy.mean()), int(len(xx)), float(idx[lab == k].mean())))
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--vox_um', type=float, default=69.12); ap.add_argument('--R0', type=float, default=3.0); ap.add_argument('--R1', type=float, default=6.0); ap.add_argument('--link_mm', type=float, default=2.5); ap.add_argument('--min_len', type=int, default=3)
    a = ap.parse_args(); F = np.load(os.path.join(a.out, 'fields.npz')); TH, CO, zmid, stride = F['theta'], F['coh'], F['z_mid'], int(F['stride']); mm = 1000.0 / a.vox_um; g = stride / mm
    per = []
    for i in range(len(zmid)):
        th, co = TH[i], CO[i]; valid = co > 1e-6
        if valid.sum() < 2000: per.append([]); continue
        m0 = index_map(th, co, valid, stride, a.R0 * mm); m1 = index_map(th, co, valid, stride, a.R1 * mm); found = []
        for sign, (lo, hi) in [(+0.5, (0.3, 0.7)), (-0.5, (-0.7, -0.3)), (+1.0, (0.75, 1.6)), (-1.0, (-1.6, -0.75))]:
            for cx, cy, n, v in comps(m0, lo, hi, 3):
                # stability: a component of the same sign band at R1 whose centroid is within R1 of this one
                near = [c for c in comps(m1, lo, hi, 3) if np.hypot(c[0] - cx, c[1] - cy) * g <= a.R1]
                found.append({'x': round(cx * stride, 1), 'z': round(cy * stride, 1), 'sign': sign, 'cells': n, 'index': round(v, 3), 'stable_R1': bool(near)})
        per.append(found)
    # tracking along y: greedy nearest-neighbour links between consecutive sections, same sign, within link_mm
    lines = []; active = []
    for i, found in enumerate(per):
        used = set(); new_active = []
        for L in active:
            last = L['pts'][-1]; best = None
            for j, d in enumerate(found):
                if j in used or d['sign'] != L['sign']: continue
                dist = np.hypot(d['x'] - last['x'], d['z'] - last['z']) / mm
                if dist <= a.link_mm and (best is None or dist < best[0]): best = (dist, j)
            if best is not None: used.add(best[1]); d = found[best[1]]; L['pts'].append({'y': float(zmid[i]), **d, 'step_mm': round(float(best[0]), 3)}); new_active.append(L)
            else: L['gap'] = L.get('gap', 0) + 1; (new_active.append(L) if L['gap'] <= 1 else lines.append(L))
        for j, d in enumerate(found):
            if j not in used: new_active.append({'sign': d['sign'], 'pts': [{'y': float(zmid[i]), **d, 'step_mm': 0.0}], 'gap': 0})
        active = new_active
    lines += active
    out = []
    for L in lines:
        if len(L['pts']) < a.min_len: continue
        steps = [p['step_mm'] for p in L['pts'][1:]]; stab = np.mean([p['stable_R1'] for p in L['pts']])
        out.append({'sign': L['sign'], 'n_sections': len(L['pts']), 'y_range': [L['pts'][0]['y'], L['pts'][-1]['y']], 'length_mm': round((L['pts'][-1]['y'] - L['pts'][0]['y'] + 16) / mm, 1), 'mean_step_mm': round(float(np.mean(steps)), 3) if steps else 0.0, 'max_step_mm': round(float(np.max(steps)), 3) if steps else 0.0,
                    'stable_frac': round(float(stab), 3), 'x_mean_mm': round(float(np.mean([p['x'] for p in L['pts']]) / mm), 2), 'z_mean_mm': round(float(np.mean([p['z'] for p in L['pts']]) / mm), 2), 'valid': bool(stab >= 0.8 and np.mean(steps) <= a.link_mm / 2 if steps else False), 'pts': L['pts']})
    out.sort(key=lambda L: -L['n_sections'])
    n_def = sum(len(f) for f in per); summ = {'sections': len(per), 'defects_total': n_def, 'defects_per_section_median': float(np.median([len(f) for f in per])), 'lines': len(out), 'valid_lines': sum(1 for L in out if L['valid']), 'lines_ge10_sections': sum(1 for L in out if L['n_sections'] >= 10),
            'plus_half_lines': sum(1 for L in out if L['sign'] == 0.5), 'minus_half_lines': sum(1 for L in out if L['sign'] == -0.5), 'R0_mm': a.R0, 'R1_mm': a.R1, 'link_mm': a.link_mm}
    json.dump({'summary': summ, 'lines': out, 'per_section': per}, open(os.path.join(a.out, 'defects.json'), 'w')); print(json.dumps(summ))
    for L in out[:12]: print({k: L[k] for k in ['sign', 'n_sections', 'y_range', 'length_mm', 'mean_step_mm', 'max_step_mm', 'stable_frac', 'x_mean_mm', 'z_mean_mm', 'valid']})

if __name__ == '__main__': main()
