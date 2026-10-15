# Provenance: Project HERCULES | owner the owner | [id removed]
"""Fraction of each accepted window (windows_dedupe.json, tol 10) lying inside the official 20260918
supervision / validation masks and label ink, for the one labelled segment. Numbers only."""
import glob, json
import zarr
L = '/home/user/dominion/logs/sib/reg0009b'
D = json.load(open(f'{L}/windows_dedupe.json'))
out = []
for a in D['tol']['10']['accepted']:
    g = glob.glob(f"/work/reg0009b/data/{a['segment']}/ink-labels/*/*/")
    if not g: continue
    x0, y0, x1, y1 = a['canvas2_px_x0y0x1y1']
    r = dict(segment=a['segment'], canvas2_px_x0y0x1y1=a['canvas2_px_x0y0x1y1'])
    for n in ('supervision', 'validation', 'inklabels'):
        m = zarr.open_array(g[0] + f'{n}.zarr/0', mode='r')[y0:y1, x0:x1]
        r[f'frac_{n}'] = round(float((m > 0).mean()), 5)
    out.append(r); print(r)
json.dump(out, open(f'{L}/window_labels.json', 'w'), indent=1)
