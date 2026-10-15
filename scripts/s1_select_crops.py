"""Deterministic Scroll-1 crop selection (rule in RULES.md, GATE-S1). Writes data/s1/<seg>/crops.json."""
import sys, os, json, numpy as np
from PIL import Image
from scipy.ndimage import binary_closing, uniform_filter, zoom
Image.MAX_IMAGE_PIXELS = None
seg, lab_p, reg_p, mid_p, out = sys.argv[1:6]; ALL_HELD = int(sys.argv[6]) if len(sys.argv) > 6 else 0
reg = json.load(open(reg_p)); S = reg["scale_label_to_canvas"]; oy, ox = reg["offset_canvas_y"], reg["offset_canvas_x"]
lab = np.asarray(Image.open(lab_p).convert("L")) > 127
ds = 40  # work at 40 canvas px = 96 um
import glob
Hc, Wc = {"20231005123336": (34880, 97280), "20231210121321": (51000, 39980), "20230929220926": (32080, 75800), "20231012184424": (50800, 75720)}[seg]
# label -> canvas at 1/ds: canvas = label*S + off
Lc = zoom(lab.astype(np.float32), S / ds, order=1)
L = np.zeros((Hc // ds, Wc // ds), np.float32); y0, x0 = int(round(oy / ds)), int(round(ox / ds))
h, w = min(Lc.shape[0], L.shape[0] - y0), min(Lc.shape[1], L.shape[1] - x0); L[y0:y0 + h, x0:x0 + w] = Lc[:h, :w]
lab_c = L > 0.5
r = int(round(5000 / 2.4 / ds)); yy, xx = np.ogrid[-r:r + 1, -r:r + 1]; disc = (yy * yy + xx * xx) <= r * r
zone = binary_closing(lab_c, disc, iterations=1) | lab_c
mid = np.asarray(Image.open(mid_p)); mid = zoom(mid.astype(np.float32), (L.shape[0] / mid.shape[0], L.shape[1] / mid.shape[1]), order=0)
on = mid > 0
side = 6250 // ds; step = 1250 // ds
dens = uniform_filter(lab_c.astype(np.float32), side, mode="constant"); zf = uniform_filter(zone.astype(np.float32), side, mode="constant"); of = uniform_filter(on.astype(np.float32), side, mode="constant")
cands = []
for y in range(side // 2, L.shape[0] - side // 2, step):
    for x in range(side // 2, L.shape[1] - side // 2, step):
        if zf[y, x] >= 0.99 and of[y, x] >= 0.90: cands.append((float(dens[y, x]), y - side // 2, x - side // 2))
cands.sort(reverse=True)
# columns: split labelled x-extent at the largest gap of the column-wise label sum
colsum = lab_c.sum(axis=0); xs = np.where(colsum > 0)[0]; gaps = np.diff(xs); gi = int(np.argmax(gaps)); xsplit = (xs[gi] + xs[gi + 1]) // 2
left = [c for c in cands if c[2] + side // 2 < xsplit]; right = [c for c in cands if c[2] + side // 2 >= xsplit]
def nonover(a, b): return abs(a[1] - b[1]) >= side or abs(a[2] - b[2]) >= side
if ALL_HELD:
    held = []
    for c in cands:
        if all(nonover(c, h) for h in held): held.append(c)
        if len(held) == ALL_HELD: break
    crops = [{"name": f"held{i+1}", "kind": "held", "y0": int(c[1] * ds), "x0": int(c[2] * ds), "side": 6250, "label_density": round(c[0], 4)} for i, c in enumerate(held)]
    json.dump({"segment": seg, "pitch_um": 2.4, "registration": reg, "xsplit_canvas": int(xsplit * ds), "n_candidates": len(cands), "crops": crops, "rule": "all held-out: the densest non-overlapping windows"}, open(out, "w"), indent=1)
    print(json.dumps(crops, indent=None)); sys.exit(0)
train = left[0]; held = []
for c in right:
    if all(nonover(c, h) for h in held): held.append(c)
    if len(held) == 2: break
for c in left[1:]:
    if nonover(c, train) and all(nonover(c, h) for h in held): held.append(c); break
crops = [{"name": "train", "kind": "train", "y0": int(train[1] * ds), "x0": int(train[2] * ds), "side": 6250, "label_density": round(train[0], 4)}]
for i, c in enumerate(held): crops.append({"name": f"held{i+1}", "kind": "held", "y0": int(c[1] * ds), "x0": int(c[2] * ds), "side": 6250, "label_density": round(c[0], 4)})
json.dump({"segment": seg, "pitch_um": 2.4, "registration": reg, "xsplit_canvas": int(xsplit * ds), "n_candidates": len(cands), "crops": crops}, open(out, "w"), indent=1)
print(json.dumps(crops, indent=None))
