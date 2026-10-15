"""Per-crop residual shift between the registered label and the team ds8 prediction (alignment check, method-independent)."""
import sys, os, json, numpy as np
from PIL import Image
from scipy.ndimage import zoom, gaussian_filter
Image.MAX_IMAGE_PIXELS = None
crops_p, ink_p, out = sys.argv[1:4]
C = json.load(open(crops_p)); ink = np.asarray(Image.open(ink_p).convert("L")).astype(np.float32) / 255.0
res = {}
for c in C["crops"]:
    d = os.path.join(os.path.dirname(crops_p), "derived", c["name"]); L = np.load(os.path.join(d, "label.npy"))
    y0, x0, side = c["y0"], c["x0"], c["side"]; ds = 8
    Ld = zoom(L.astype(np.float32), 1 / ds, order=1); I = ink[y0 // ds:(y0 + side) // ds, x0 // ds:(x0 + side) // ds]
    h, w = min(Ld.shape[0], I.shape[0]), min(Ld.shape[1], I.shape[1]); Ld, I = Ld[:h, :w], I[:h, :w]
    Ld = gaussian_filter(Ld, 2) - gaussian_filter(Ld, 2).mean(); I = gaussian_filter(I, 2) - gaussian_filter(I, 2).mean()
    best = None
    for dy in range(-60, 61, 4):
        for dx in range(-60, 61, 4):
            a = Ld[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)]; b = I[max(0, -dy):h + min(0, -dy), max(0, -dx):w + min(0, -dx)]
            cc = float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum() + 1e-9))
            if best is None or cc > best[0]: best = (cc, dy, dx)
    c0 = float((Ld * I).sum() / np.sqrt((Ld * Ld).sum() * (I * I).sum() + 1e-9))
    res[c["name"]] = {"corr_at_zero": round(c0, 3), "best_corr": round(best[0], 3), "shift_canvas_px": [best[1] * ds, best[2] * ds], "shift_um": [best[1] * ds * 2.4, best[2] * ds * 2.4]}
    print(c["name"], res[c["name"]], flush=True)
json.dump(res, open(out, "w"), indent=1)
