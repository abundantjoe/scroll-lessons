"""Per-run ink inference wall time of a control run: the E2E_WALL_S line that scripts/pipeline/run_ink_local.py writes to
each batch_ink.sh ink log, with the strip size in Mpx from its ensemble map.

  python ink_runtime.py <BI_ROOT> --out ink_runtime.json
"""
import argparse
import glob
import json
import os
import re

import tifffile

ap = argparse.ArgumentParser()
ap.add_argument('bi')
ap.add_argument('--out', required=True)
a = ap.parse_args()
runs = []
for d in sorted(glob.glob(os.path.join(a.bi, 'ctrlS_*'))):
    H, W = tifffile.imread(os.path.join(d, 'ens_d1.tif')).shape
    for f in sorted(glob.glob(os.path.join(d, 'logs', 'ink_*.log'))):
        m = re.search(r'E2E_WALL_S ([\d.]+) threads=(\d+)', open(f).read())
        if m:
            runs.append(dict(strip=os.path.basename(d), model=os.path.basename(f)[4:-4], seconds=float(m.group(1)),
                             threads=int(m.group(2)), mpx=H * W / 1e6))
tot_s, tot_mpx = sum(r['seconds'] for r in runs), sum(r['mpx'] for r in runs)
out = dict(n_runs=len(runs), seconds_per_mpx_per_run=tot_s / tot_mpx, total_run_minutes=tot_s / 60, runs=runs)
json.dump(out, open(a.out, 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'runs'}))
