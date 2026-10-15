"""Comparator: the team's 2.4 um prediction (ds8 overview) upsampled to the crop, written as s_top_team/s_bot_team."""
import sys, os, json, numpy as np
from PIL import Image
from scipy.ndimage import zoom
Image.MAX_IMAGE_PIXELS = None
d, crops_p, name, ink_p = sys.argv[1:5]
c = [x for x in json.load(open(crops_p))["crops"] if x["name"] == name][0]; y0, x0, side = c["y0"], c["x0"], c["side"]
ink = np.asarray(Image.open(ink_p).convert("L")).astype(np.float32) / 255.0
sub = ink[y0 // 8:(y0 + side) // 8 + 1, x0 // 8:(x0 + side) // 8 + 1]
up = zoom(sub, 8, order=1)[:side, :side]
m = (np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0)
z = np.where(m, up, 0).astype(np.float16)
for f in ("top", "bot"): np.save(os.path.join(d, f"s_{f}_team.npy"), z)
print(d, "team comparator written")
