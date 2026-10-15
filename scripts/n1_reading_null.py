"""Post-hoc null N1 (RULES.md): is the reading-run agreement statistic above what spatial layout alone produces?

Agreement statistic (as in R1/R2): AUC of a detector's score separating the team model's confident ink (> 0.80) from its confident blank
(< 0.20) on an unread window, inside the judge mask. Null: the same statistic with the score map of window i and the team classes of
window j != i (all ordered pairs of the four R1 windows; all windows are 6250 px square). Writes results/n1_reading_null.json.
"""
import itertools, json, sys
import numpy as np
from PIL import Image
from scipy.ndimage import zoom
sys.path.insert(0, ".")
from inkeval import auc

Image.MAX_IMAGE_PIXELS = None
WIN = []
for seg in ("20231005123336", "20231210121321"):
    for c in json.load(open(f"data/s1/{seg}/unread.json"))["crops"]:
        WIN.append((seg, c))
team, masks = {}, {}
for seg, c in WIN:
    ink = np.asarray(Image.open(f"data/s1/{seg}/overview/ink_ds8.jpg").convert("L")).astype(np.float32) / 255.0
    y0, x0, s = c["y0"], c["x0"], c["side"]
    t = zoom(ink[y0 // 8:(y0 + s) // 8 + 1, x0 // 8:(x0 + s) // 8 + 1], 8, order=1)[:s, :s]
    d = f"data/s1/{seg}/derived/{c['name']}"
    k = f"{seg}:{c['name']}"
    masks[k] = (np.load(f"{d}/mask_top.npy") > 0) & (np.load(f"{d}/mask_bot.npy") > 0)
    team[k] = (t > 0.80, t < 0.20)
keys = list(team)
sub = np.random.default_rng(0).random(masks[keys[0]].shape) < 0.05   # the judge's subsample rule, to keep ranks small
out = {"status": "post-hoc (declared after R1/R2; RULES.md N1)", "windows": keys, "tags": {}}
for tag in ("v8", "e"):
    sc = {k: np.load(f"data/s1/{k.split(':')[0]}/derived/{k.split(':')[1]}/s_bot_{tag}.npy").astype(np.float32) for k in keys}
    matched = {k: auc(sc[k][team[k][0] & masks[k] & sub], sc[k][team[k][1] & masks[k] & sub]) for k in keys}
    null = [auc(sc[i][team[j][0] & masks[i] & sub], sc[i][team[j][1] & masks[i] & sub]) for i, j in itertools.permutations(keys, 2)]
    null = [v for v in null if v is not None]
    out["tags"][tag] = {"matched": matched, "matched_mean": float(np.mean(list(matched.values()))),
                        "null_values": null, "null_mean": float(np.mean(null)), "null_min": float(np.min(null)),
                        "null_max": float(np.max(null)),
                        "matched_above_null_max": int(sum(v > max(null) for v in matched.values()))}
    print(tag, "matched", {k: round(v, 4) for k, v in matched.items()}, "null mean %.4f range [%.4f, %.4f]" % (np.mean(null), min(null), max(null)), flush=True)
json.dump(out, open("results/n1_reading_null.json", "w"), indent=1)
print("written results/n1_reading_null.json")
