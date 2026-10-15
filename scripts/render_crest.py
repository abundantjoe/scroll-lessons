#!/usr/bin/env python
"""R-CREST on a render: per-slice mean over the on-sheet pixels (non-zero in the middle slice) of a render zarr
(group '0', axes slice y x) -> read_chart.crest_check (ratio >= 1.20, crest in the central half). Writes JSON, exits 0
on pass, 1 on fail. Usage: render_crest.py <render.zarr> <out.json>"""
import sys, json, os, zarr, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import read_chart as RC

def main(render, out):
    a = zarr.open_group(render, mode='r')['0']; n = a.shape[0]
    mid = np.asarray(a[n // 2]); onsheet = mid > 0
    prof = [float(np.asarray(a[i])[onsheet].mean()) if onsheet.any() else 0.0 for i in range(n)]
    c = RC.crest_check(prof); c['profile'] = [round(v, 2) for v in prof]; c['n_slices'] = n
    c['onsheet_frac_mid'] = float(onsheet.mean()); c['render'] = render
    json.dump(c, open(out, 'w'), indent=1)
    print(f"R-CREST render {'PASS' if c['passed'] else 'VOID'}: ratio {c['ratio']} crest slice {c['crest_slice']} of {n} (central {c['central_bounds']}); on-sheet {c['onsheet_frac_mid']:.3f}; profile {c['profile']}")
    return 0 if c['passed'] else 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
