#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-UMB-2 (+A1) bars B1-B5 over the pass-2 lane records (logs/umb/native2/lane*/core_native.json, merged by y).
Per y: left/right z_c (innermost U-turn apex heights, mm), agreement, nesting correlations, interior test, crossing balance,
and the confidence product of item 3 (agree within 2 local pitches x crossings balanced x nesting monotone <= -0.5 both
sides at both columns). Bars (nothing lowered): B1 agreement <= 2 pitches on >= 80 % of sampled y; B2 crossing balance on
>= 80 % of lines through the slit; B3 z_c(y) continuity (step <= 2 pitches between consecutive samples, seams excepted and
counted); B4 innermost interior empty at both columns on >= 80 %; B5 coverage: a core on >= 50 % of the in-domain y range.
usage: umb2_bars.py <out.json> [--glob 'logs/umb/native2/lane*/core_native.json'] [--pitch_mm 0.38] [--md out.md]
Writes the per-y table and the bar numbers; claims nothing beyond them."""
import argparse, glob, json, numpy as np

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--glob', default='logs/umb/native2/lane*/core_native.json'); ap.add_argument('--pitch_mm', type=float, default=0.38); ap.add_argument('--md', default=None); ap.add_argument('--y_range', type=float, nargs=2, default=[1536, 11136])
    a = ap.parse_args(); recs = {}
    for f in sorted(glob.glob(a.glob)):
        for r in json.load(open(f)).get('records', []): recs[r['y']] = r | {'lane_file': f}
    ys = sorted(recs); rows = []; P = a.pitch_mm
    for y in ys:
        r = recs[y]; L, R = r.get('left', {}), r.get('right', {}); row = {'y': y, 'y_mm': round(y * 8.64e-3, 2)}
        ok = L.get('status') == 'ok' and R.get('status') == 'ok' and 'zc_mm' in L and 'zc_mm' in R
        row['status'] = 'core' if ok else f"L:{L.get('status')} R:{R.get('status')}"
        if ok:
            row.update({'zc_L': L['zc_mm'], 'zc_R': R['zc_mm'], 'zc': round(0.5 * (L['zc_mm'] + R['zc_mm']), 3), 'agree_mm': round(abs(L['zc_mm'] - R['zc_mm']), 3), 'agree_ok': abs(L['zc_mm'] - R['zc_mm']) <= 2 * P,
                        'depth_L': L.get('apex_depth_mm_at_zc'), 'depth_R': R.get('apex_depth_mm_at_zc'), 'int_L': L.get('interior_ridges_within_3_pitches'), 'int_R': R.get('interior_ridges_within_3_pitches'),
                        'interior_ok': (L.get('interior_ridges_within_3_pitches', 99) < 14 and R.get('interior_ridges_within_3_pitches', 99) < 14),
                        'nest': [L.get('nesting_corr_above'), L.get('nesting_corr_below'), R.get('nesting_corr_above'), R.get('nesting_corr_below')],
                        'cross_frac': (r.get('crossings') or {}).get('balanced_frac'), 'n_ws': [L.get('uturns', {}).get('n_winding_scale'), R.get('uturns', {}).get('n_winding_scale')]})
            nest_ok = all(v is not None and v <= -0.5 for v in row['nest']); cross_ok = (row['cross_frac'] or 0) >= 0.8
            row['nest_ok'] = nest_ok; row['cross_ok'] = cross_ok; row['confident'] = bool(row['agree_ok'] and cross_ok and nest_ok)
        rows.append(row)
    core = [q for q in rows if q['status'] == 'core']; n = len(rows)
    def frac(key, pool): return (round(float(np.mean([bool(q[key]) for q in pool])), 3) if pool else None)
    bars = {'n_sampled_y': n, 'n_core': len(core), 'B1_agree_frac': frac('agree_ok', core), 'B1_pass': bool(core) and frac('agree_ok', core) >= 0.8,
            'B2_cross_frac_mean': (round(float(np.mean([q['cross_frac'] for q in core if q['cross_frac'] is not None])), 3) if core else None),
            'B2_pass': bool(core) and all((q['cross_frac'] or 0) >= 0.8 for q in core), 'B4_interior_frac': frac('interior_ok', core), 'B4_pass': bool(core) and frac('interior_ok', core) >= 0.8,
            'nesting_frac': frac('nest_ok', core), 'confident_frac': frac('confident', core)}
    # B3 continuity along y among confident cores (consecutive samples): steps > 2 pitches counted as seams/events
    conf = [q for q in core if q['confident']]; steps = [abs(conf[i + 1]['zc'] - conf[i]['zc']) for i in range(len(conf) - 1)]
    bars['B3_steps'] = len(steps); bars['B3_steps_gt_2pitch'] = int(sum(s > 2 * P for s in steps)); bars['B3_pass'] = (bool(steps) and bars['B3_steps_gt_2pitch'] == 0) if steps else None
    # B5 coverage: fraction of the in-domain y range within half a sample spacing of a confident core
    if conf and n > 1:
        sp = (a.y_range[1] - a.y_range[0]) / max(n - 1, 1); covered = set()
        for q in conf: covered.add(int(round((q['y'] - a.y_range[0]) / sp)))
        bars['B5_coverage'] = round(len(covered) / max(n, 1), 3); bars['B5_pass'] = bars['B5_coverage'] >= 0.5
    else: bars['B5_coverage'] = 0.0; bars['B5_pass'] = False
    bars['umbilicus_determined'] = bool(bars['B1_pass'] and bars['B2_pass'] and bars['B4_pass'] and bars['B5_pass'] and (bars['B3_pass'] is not False))
    out = {'declaration': 'DECL-UMB-2 + DECL-UMB-2-A1', 'pitch_mm': P, 'bars': bars, 'rows': rows}; json.dump(out, open(a.out, 'w'), indent=1); print(json.dumps(bars))
    if a.md:
        with open(a.md, 'w') as f:
            f.write('| y | y mm | status | zc_L | zc_R | agree mm | depth L/R mm | interior L/R | nesting (La,Lb,Ra,Rb) | cross | winding-scale L/R | confident |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n')
            for q in rows: f.write(f"| {q['y']} | {q['y_mm']} | {q['status']} | {q.get('zc_L','')} | {q.get('zc_R','')} | {q.get('agree_mm','')} | {q.get('depth_L','')}/{q.get('depth_R','')} | {q.get('int_L','')}/{q.get('int_R','')} | {q.get('nest','')} | {q.get('cross_frac','')} | {q.get('n_ws','')} | {q.get('confident','')} |\n")
            f.write('\nBars: ' + json.dumps(bars) + '\n')

if __name__ == '__main__': main()
