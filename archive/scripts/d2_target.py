"""Diagnostic D2 (RULES.md): build the team model's prediction on the 19.2 um pooled grid as a regression target.

DIAGNOSTIC ONLY - this is distillation from the team model and can never be one of our methods.
Writes ds8_team.npy (float32, 0..1, -1 outside the judge mask) next to each crop's pooled stack.
"""
import sys, os, json, numpy as np
from PIL import Image
from scipy.ndimage import zoom
Image.MAX_IMAGE_PIXELS = None

F = 8
for spec in sys.argv[1:]:
    seg, crop = spec.split(":")
    d = f"data/s1/{seg}/derived/{crop}"
    C = json.load(open(f"data/s1/{seg}/crops.json"))
    c = [x for x in C["crops"] if x["name"] == crop][0]
    y0, x0, side = c["y0"], c["x0"], c["side"]
    ink = np.asarray(Image.open(f"data/s1/{seg}/overview/ink_ds8.jpg").convert("L")).astype(np.float32) / 255.0
    sub = ink[y0 // F:(y0 + side) // F + 1, x0 // F:(x0 + side) // F + 1]
    X = np.load(os.path.join(d, "ds8_x.npy"), mmap_mode="r"); H8, W8 = X.shape[1], X.shape[2]
    t = zoom(sub, (H8 / sub.shape[0], W8 / sub.shape[1]), order=1)[:H8, :W8]
    m = np.asarray(X[22]) > 0.5
    out = np.where(m, np.clip(t, 0, 1), -1).astype(np.float32)
    np.save(os.path.join(d, "ds8_team.npy"), out)
    print(f"{d}  team target: mask {m.mean():.3f}  mean {out[m].mean():.3f}  p10/p90 {np.percentile(out[m],10):.3f}/{np.percentile(out[m],90):.3f}", flush=True)
