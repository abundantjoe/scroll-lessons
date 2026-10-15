# Provenance: Project HERCULES | owner the owner | [id removed]
"""Level-0 (x, y, z) mesh points of the PHerc0841 J windows (J1-J5,
logs/d1/d1_build_prep.json organizer_window boxes on the 9.366 um organizer
canvas; canvas pixel c <-> grid g = (c + 0.5) * scale). Every valid grid
vertex whose index lies in the box expanded by one vertex is kept
(conservative). Output: npy of points + JSON summary."""
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from hercules.geometry.tifxyz import read_tifxyz, valid_mask  # noqa: E402

S3 = Path("/work/handed/s3")
prep = json.loads((ROOT / "logs/d1/d1_build_prep.json").read_text())
pts, summ = [], {}
for name, w in prep["windows"].items():
    if w.get("set") != "J":
        continue
    seg = w["segment"]
    short = seg.split("-")[0]
    d = S3 / f"PHerc0841/segments/{seg}/mesh/{short}-on-20250821151531-9.366um.tifxyz"
    m = read_tifxyz(d)
    sc = m.scale[0]
    ow = w["organizer_window"]
    r0 = max(0, math.floor((ow["y0"] + 0.5) * sc) - 1)
    r1 = min(m.points.shape[0] - 1, math.ceil((ow["y0"] + ow["h"] - 0.5) * sc) + 1)
    c0 = max(0, math.floor((ow["x0"] + 0.5) * sc) - 1)
    c1 = min(m.points.shape[1] - 1, math.ceil((ow["x0"] + ow["w"] - 0.5) * sc) + 1)
    sub = m.points[r0:r1 + 1, c0:c1 + 1]
    ok = valid_mask(sub)
    pts.append(sub[ok].astype(np.float64))
    summ[name] = dict(segment=seg, scale=list(m.scale), grid_rows=[r0, r1], grid_cols=[c0, c1], n_points=int(ok.sum()),
                      canvas_hw_check=[round(m.points.shape[0] / sc), round(m.points.shape[1] / sc)],
                      canvas_hw_prep=w["organizer_canvas_hw"])
P = np.concatenate(pts)
np.save(sys.argv[1], P)
summ["total_points"] = int(P.shape[0])
summ["bbox"] = [P.min(0).tolist(), P.max(0).tolist()]
Path(sys.argv[2]).write_text(json.dumps(summ, indent=1))
print(json.dumps(summ))
