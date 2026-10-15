"""Confirmation test C1 (RULES.md): choose untouched labelled windows mechanically.

Strict original crop criteria (label-zone coverage >= 0.99, on-sheet coverage >= 0.90), non-overlapping with EVERY window this project
has processed on the segment (crops.json + unread.json), descending label density, up to N per segment.
Writes data/s1/<seg>/confirm.json with the segment's registration so the judge and the refinement can use it unchanged.

  select_confirm.py <seg> [N]
"""
import json, os, sys, numpy as np
from PIL import Image
from scipy.ndimage import binary_closing, uniform_filter, zoom
Image.MAX_IMAGE_PIXELS = None

CANVAS = {"20231005123336": (34880, 97280), "20231210121321": (51000, 39980),
          "20230929220926": (32080, 75800), "20231012184424": (50800, 75720)}
ds = 40
seg = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 3

C = json.load(open(f"data/s1/{seg}/crops.json")); reg = C["registration"]
S, oy, ox = reg["scale_label_to_canvas"], reg["offset_canvas_y"], reg["offset_canvas_x"]
lp = f"data/s1/labels/{seg}_inklabels_L.png"
if not os.path.exists(lp): lp = f"data/s1/labels/{seg}_inklabels.png"
lab = np.asarray(Image.open(lp).convert("L")) > 127
Hc, Wc = CANVAS[seg]
Lc = zoom(lab.astype(np.float32), S / ds, order=1)
L = np.zeros((Hc // ds, Wc // ds), np.float32)
y0, x0 = int(round(oy / ds)), int(round(ox / ds))
h, w = min(Lc.shape[0], L.shape[0] - y0), min(Lc.shape[1], L.shape[1] - x0)
L[y0:y0 + h, x0:x0 + w] = Lc[:h, :w]
lab_c = L > 0.5
r = int(round(5000 / 2.4 / ds)); yy, xx = np.ogrid[-r:r + 1, -r:r + 1]; disc = (yy * yy + xx * xx) <= r * r
zone = binary_closing(lab_c, disc, iterations=1) | lab_c

mp = f"data/s1/{seg}/overview/onsheet_ds8.png"
if not os.path.exists(mp): mp = f"data/s1/{seg}/overview/mid_l3.png"
mid = np.asarray(Image.open(mp).convert("L"))
mid = zoom(mid.astype(np.float32), (L.shape[0] / mid.shape[0], L.shape[1] / mid.shape[1]), order=0)
on = mid > 0

side = 6250 // ds; step = 1250 // ds
dens = uniform_filter(lab_c.astype(np.float32), side, mode="constant")
zf = uniform_filter(zone.astype(np.float32), side, mode="constant")
of = uniform_filter(on.astype(np.float32), side, mode="constant")

used = [(c["y0"] // ds, c["x0"] // ds) for c in C["crops"]]
up = f"data/s1/{seg}/unread.json"
if os.path.exists(up): used += [(c["y0"] // ds, c["x0"] // ds) for c in json.load(open(up))["crops"]]

cands = []
for y in range(side // 2, L.shape[0] - side // 2, step):
    for x in range(side // 2, L.shape[1] - side // 2, step):
        if zf[y, x] >= 0.99 and of[y, x] >= 0.90:
            cands.append((float(dens[y, x]), y - side // 2, x - side // 2))
cands.sort(reverse=True)

def nonover(a, b): return abs(a[0] - b[0]) >= side or abs(a[1] - b[1]) >= side
kept = []
for c in cands:
    p = (c[1], c[2])
    if all(nonover(p, u) for u in used) and all(nonover(p, (k[1], k[2])) for k in kept):
        kept.append(c)
    if len(kept) == N: break

out = {"segment": seg, "pitch_um": 2.4, "registration": reg, "onsheet_source": os.path.basename(mp),
       "rule": "C1: strict criteria (zone>=0.99, onsheet>=0.90), non-overlapping with every processed window, density order",
       "n_candidates": len(cands), "excluded_windows": len(used),
       "crops": [{"name": f"conf{i+1}", "kind": "confirm", "y0": int(k[1] * ds), "x0": int(k[2] * ds), "side": 6250,
                  "label_density": round(k[0], 4)} for i, k in enumerate(kept)]}
json.dump(out, open(f"data/s1/{seg}/confirm.json", "w"), indent=1)
print(f"{seg}: {len(cands)} candidates, {len(used)} windows excluded, kept {len(kept)}: "
      + ", ".join(f"({c['y0']},{c['x0']}) dens {c['label_density']}" for c in out["crops"]))
