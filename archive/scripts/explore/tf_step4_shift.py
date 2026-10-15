"""twoface step 4 (TRAINING crops only): spatial-scale audit of the face signals.

If a score map really images the strokes, its AUC must collapse when the map is translated
by more than a stroke width.  If the map is a slowly varying field that happens to be higher
where the writing is, the AUC survives large translations.  This separates "ink detected on
the far face" from "the far face is brighter in the written region".

Score maps compared (no fitting at all, all at sigma = 16 ds8 px = 0.31 mm):
  BOT   mean of B-4..B-1 (inside the writing face; where the declared contrast lives)
  TOPO  mean of T-4..T-1 (strictly OUTSIDE the non-writing face, 2.4-9.6 um above it)
  LVL   mean of all 22 channels
  TEAM  the team 2.4 um model pooled to the ds8 grid (only where s_bot_team.npy exists)
"""
import os, sys, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tf_lib import load_crop, fill, smooth, auc, TRAIN
from mf_lib import cropdir, pool

OUT = "/home/user/megara/stats/explore/tf_step4_shift.json"
SH = [0, 2, 4, 8, 16, 32, 64]          # ds8 px; 1 px = 19.2 um
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def shifted_auc(s, t, b, d):
    if d == 0:
        return auc(s, t, b)
    vals = []
    for dy, dx in DIRS:
        sm = np.roll(np.roll(s, dy * d, 0), dx * d, 1)
        # only pixels that stayed inside the array
        ok = np.ones_like(t)
        if dy * d > 0: ok[:dy * d] = False
        elif dy * d < 0: ok[dy * d:] = False
        if dx * d > 0: ok[:, :dx * d] = False
        elif dx * d < 0: ok[:, dx * d:] = False
        vals.append(auc(sm, t & ok, b & ok))
    return float(np.nanmean(vals))


res = {}
for seg, crop in TRAIN:
    x, m, t, b = load_crop(seg, crop)
    q = np.stack([smooth(fill(x[k], m, 2.0), 16.0) for k in range(22)])
    maps = {"BOT": q[11:15].mean(0), "TOPO": q[0:4].mean(0), "LVL": q.mean(0)}
    p = cropdir(seg, crop) + "/s_bot_team.npy"
    if os.path.exists(p):
        T = np.load(p).astype(np.float32)
        h8 = t.shape[0]
        maps["TEAM"] = smooth(fill(pool(T, h8, h8).astype(np.float32), m, 2.0), 16.0)
    ent = {}
    for name, s in maps.items():
        ent[name] = {str(d): round(shifted_auc(s, t, b, d), 4) for d in SH}
    res[f"{seg}/{crop}"] = ent
    print(f"{seg}/{crop}")
    for name in ent:
        print("   ", name, ent[name], flush=True)

# means across the training crops
agg = {}
for name in ("BOT", "TOPO", "LVL", "TEAM"):
    rows = [v[name] for v in res.values() if name in v]
    if rows:
        agg[name] = {d: round(float(np.mean([r[d] for r in rows])), 4) for d in rows[0]}
res["_mean"] = agg
print("MEAN over training crops:")
for k, v in agg.items():
    print("  ", k, v)
json.dump(res, open(OUT, "w"), indent=1)
print("wrote", OUT)
