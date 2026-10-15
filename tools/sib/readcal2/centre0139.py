# Provenance: Project HERCULES | owner the owner | [id removed]
"""PHerc0139 centre curve for state-A orientation, as PROBE-3 (ct_mask_centroid_level4, smooth 256 vox): the
masked-scroll centroid per level-4 slice of the official 9.362 um volume, streamed (no image kept). Output
/work/rc2/centre0139.npz + logs/sib/readcal2/centre0139.json (curve numbers, ranges vs PROBE-3's recorded ranges)."""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'src'))
from hercules.pipeline.centre import mask_centroid_curve  # noqa: E402

URL = 's3://vesuvius-challenge-open-data/PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr'
PROBE3 = {'z_range': [1212.4609375, 8959.1572265625], 'x_range': [2579.3679447875784, 3231.9310613244475],
          'y_range': [2808.7630548184206, 3170.825556075301], 'n_slices': 486}

mc = mask_centroid_curve(URL, level=4, z_range=(PROBE3['z_range'][0], PROBE3['z_range'][1]), smooth_sigma_vox=256.0,
                         workers=8)
c = mc.curve
np.savez('/work/rc2/centre0139.npz', z=c.z, x=c.x, y=c.y)
rec = {'provenance': 'Provenance: Project HERCULES | owner the owner | [id removed]', 'url': URL, 'level': 4,
       'smooth_sigma_vox': 256.0, 'n_slices': int(len(mc.z_full)), 'n_requests': int(mc.n_requests),
       'seconds': float(mc.seconds), 'z_range': [float(c.z.min()), float(c.z.max())],
       'x_range': [float(c.x.min()), float(c.x.max())], 'y_range': [float(c.y.min()), float(c.y.max())],
       'probe3_recorded': PROBE3, 'z': c.z.tolist(), 'x': c.x.tolist(), 'y': c.y.tolist()}
open(os.path.join(REPO, 'logs/sib/readcal2/centre0139.json'), 'w').write(json.dumps(rec, indent=1) + '\n')
print({k: rec[k] for k in ('n_slices', 'n_requests', 'seconds', 'z_range', 'x_range', 'y_range')})
