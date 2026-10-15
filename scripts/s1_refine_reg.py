"""Per-crop translation of the registered label against the team ds8 prediction (fine search), written into crops.json as local_offset."""
import sys, os, json, numpy as np
from PIL import Image
from scipy.ndimage import zoom, gaussian_filter
Image.MAX_IMAGE_PIXELS = None
crops_p, lab_p, ink_p = sys.argv[1:4]
C = json.load(open(crops_p)); reg = C["registration"]; S = reg["scale_label_to_canvas"]
lab = np.asarray(Image.open(lab_p).convert("L")) > 127; ink = np.asarray(Image.open(ink_p).convert("L")).astype(np.float32) / 255.0
ds = 8
for c in C["crops"]:
    y0, x0, side = c["y0"], c["x0"], c["side"]; pad = 640
    ys = ((np.arange(y0 - pad, y0 + side + pad) - reg["offset_canvas_y"]) / S).round().astype(int); xs = ((np.arange(x0 - pad, x0 + side + pad) - reg["offset_canvas_x"]) / S).round().astype(int)
    ys = np.clip(ys, 0, lab.shape[0] - 1); xs = np.clip(xs, 0, lab.shape[1] - 1); L = lab[np.ix_(ys, xs)].astype(np.float32)
    Ld = gaussian_filter(zoom(L, 1 / ds, order=1), 1.5); I = gaussian_filter(ink[y0 // ds:(y0 + side) // ds, x0 // ds:(x0 + side) // ds], 1.5)
    I = I - I.mean(); h, w = I.shape; P = pad // ds; best = None
    for dy in range(-P, P + 1):
        for dx in range(-P, P + 1):
            a = Ld[P + dy:P + dy + h, P + dx:P + dx + w]; a = a - a.mean()
            cc = float((a * I).sum() / np.sqrt((a * a).sum() * (I * I).sum() + 1e-9))
            if best is None or cc > best[0]: best = (cc, dy, dx)
    # label window shifted by (dy,dx) matches the crop => canvas = label_transform + (-dy, -dx)*ds
    c["local_offset"] = [-best[1] * ds, -best[2] * ds]; c["local_reg_corr"] = round(best[0], 3)
    print(c["name"], "corr %.3f" % best[0], "local_offset canvas px", c["local_offset"], "um", [v * 2.4 for v in c["local_offset"]], flush=True)
json.dump(C, open(crops_p, "w"), indent=1)
