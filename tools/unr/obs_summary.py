#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-E2E-3 item 1: summarise the band-observability survey (logs/unr/obs/obs_y<y>_w<w>.json) into summary.json and a figure
(margins over the controls, competitor distance, texture power and motion against y and depth). Reading rule as declared:
observable at dy 4 iff margin(T - C1) >= 0.30 and margin(T - C3) >= 0.30. No window is validated by this; nothing is tracked.
usage: obs_summary.py <obs_dir> <out_json> [--png <figure.png>]"""
import os, sys, json, glob, argparse, numpy as np

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('obs_dir'); ap.add_argument('out'); ap.add_argument('--png', default=None); a = ap.parse_args()
    rows = []
    for f in sorted(glob.glob(os.path.join(a.obs_dir, 'obs_y*_w*.json'))):
        r = json.load(open(f))
        if 'margin_T_minus_C1' not in r: rows.append({'y': r.get('y'), 'w': r.get('window'), 'n_cells': r.get('n_cells'), 'note': r.get('note', 'no statistics')}); continue
        rows.append({'y': r['y'], 'w': r['window'], 'bbox_zx': r.get('bbox_zx'), 'n_cells': r['n_cells'], 'tau': round(r['tau'], 4), 'in_mask': round(r['in_mask_frac'], 3), 'dcomp_p10_25_50': r['dcomp_p10_25_50'], 'open_frac': r['open_frac'], 'accept': r['accept_d4_in_Mk1'], 'm1': r['margin_T_minus_C1'], 'm3': r['margin_T_minus_C3'], 'observable': r['observable_at_dy4'], 'g5': r['g5_on_Mk1'], 'texture_power': (r.get('texture') or {}).get('power'), 'zsame_median': (r.get('texture') or {}).get('zsame_median'), 'twin_dA_change_p50_p90': r.get('twin_dA_change_p50_p90'), 'motion_lag_p50_p90': r.get('motion_abs_lag_p50_p90'), 'motion_frac_gt4': r.get('motion_frac_gt4'), 'fetch_s': (r.get('fetch') or {}).get('fetch_s'), 'secs': r.get('secs')})
    ok = [r for r in rows if 'm1' in r]; ys = sorted({r['y'] for r in ok})
    summ = {'declaration': 'DECL-E2E-3 item 1', 'n_windows': len(rows), 'n_with_stats': len(ok), 'n_y_positions': len(ys), 'y_range': [min(ys), max(ys)] if ys else None,
            'observable_windows': sum(1 for r in ok if r['observable']), 'observable_frac': round(float(np.mean([r['observable'] for r in ok])), 3) if ok else None,
            'm1_p10_50_90': [round(float(v), 3) for v in np.percentile([r['m1'] for r in ok], [10, 50, 90])] if ok else None, 'm3_p10_50_90': [round(float(v), 3) for v in np.percentile([r['m3'] for r in ok], [10, 50, 90])] if ok else None,
            'dcomp_p50_median_over_windows': round(float(np.median([r['dcomp_p10_25_50'][2] for r in ok])), 1) if ok else None, 'texture_power_p10_50_90': [round(float(v), 3) for v in np.percentile([r['texture_power'] for r in ok if r['texture_power'] is not None], [10, 50, 90])] if any(r['texture_power'] is not None for r in ok) else None,
            'motion_lag_p50_median': round(float(np.median([r['motion_lag_p50_p90'][0] for r in ok if r['motion_lag_p50_p90']])), 2) if ok else None,
            'best_windows_by_min_margin': sorted([{'y': r['y'], 'w': r['w'], 'min_margin': round(min(r['m1'], r['m3']), 3), 'm1': r['m1'], 'm3': r['m3'], 'dcomp_p50': r['dcomp_p10_25_50'][2], 'texture_power': r['texture_power'], 'motion_p50': r['motion_lag_p50_p90'][0] if r['motion_lag_p50_p90'] else None} for r in ok], key=lambda d: -d['min_margin'])[:12],
            'per_y': {str(y): {'m1_mean': round(float(np.mean([r['m1'] for r in ok if r['y'] == y])), 3), 'm3_mean': round(float(np.mean([r['m3'] for r in ok if r['y'] == y])), 3), 'observable': int(sum(r['observable'] for r in ok if r['y'] == y)), 'n': int(sum(1 for r in ok if r['y'] == y))} for y in ys}, 'rows': rows}
    json.dump(summ, open(a.out, 'w'), indent=1); print(json.dumps({k: summ[k] for k in summ if k not in ('rows', 'per_y', 'best_windows_by_min_margin')}))
    if a.png and ok:
        try:
            import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
            fig, ax = plt.subplots(2, 2, figsize=(12, 8)); yy = np.array([r['y'] for r in ok]) * 8.64 / 1000; ww = np.array([r['w'] for r in ok])
            for w, mk in zip(range(3), 'o^s'):
                m = ww == w; ax[0, 0].plot(yy[m], [r['m1'] for r, q in zip(ok, m) if q], mk, label=f'window {w} (T - C1)'); ax[0, 0].plot(yy[m], [r['m3'] for r, q in zip(ok, m) if q], mk, mfc='none', label=f'window {w} (T - C3)')
            ax[0, 0].axhline(0.30, color='k', ls='--'); ax[0, 0].set_xlabel('y (mm)'); ax[0, 0].set_ylabel('acceptance margin at dy 4'); ax[0, 0].legend(fontsize=7); ax[0, 0].set_title('margins over the controls (bar 0.30)')
            ax[0, 1].plot(yy, [r['dcomp_p10_25_50'][2] for r in ok], '.'); ax[0, 1].set_xlabel('y (mm)'); ax[0, 1].set_ylabel('d_comp p50 (vox)'); ax[0, 1].set_title('competitor distance')
            ax[1, 0].plot(yy, [r['texture_power'] if r['texture_power'] is not None else np.nan for r in ok], '.'); ax[1, 0].axhline(0.8, color='k', ls='--'); ax[1, 0].set_xlabel('y (mm)'); ax[1, 0].set_ylabel('texture power'); ax[1, 0].set_title('I4 texture power at dy 4 (bar 0.8)')
            ax[1, 1].plot(yy, [r['motion_lag_p50_p90'][0] if r['motion_lag_p50_p90'] else np.nan for r in ok], '.', label='p50'); ax[1, 1].plot(yy, [r['motion_lag_p50_p90'][1] if r['motion_lag_p50_p90'] else np.nan for r in ok], 'x', label='p90'); ax[1, 1].set_xlabel('y (mm)'); ax[1, 1].set_ylabel('|lag| per 4 sections (vox)'); ax[1, 1].legend(); ax[1, 1].set_title('sheet motion per 4 sections')
            fig.suptitle('PHerc0268 band-observability survey (DECL-E2E-3 item 1): statistics of ridge fields, not evidence of readable sheets'); fig.tight_layout(); fig.savefig(a.png, dpi=110)
        except Exception as e: print('figure skipped:', e)

if __name__ == '__main__': main()
