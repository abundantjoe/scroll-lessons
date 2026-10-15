"""How many additional non-overlapping TRAINING windows are reachable at relaxed window criteria, and what labelled
coverage would they add? Diagnostic only - selects nothing, writes nothing."""
import json, sys, numpy as np
from PIL import Image
from scipy.ndimage import binary_closing, uniform_filter, zoom
Image.MAX_IMAGE_PIXELS = None

CANVAS = {"20231005123336": (34880, 97280), "20231210121321": (51000, 39980),
          "20230929220926": (32080, 75800), "20231012184424": (50800, 75720)}
ds = 40

for seg in ("20230929220926", "20231012184424"):
    reg = json.load(open(f"data/s1/{seg}/label_registration.json"))
    S, oy, ox = reg["scale_label_to_canvas"], reg["offset_canvas_y"], reg["offset_canvas_x"]
    lab = np.asarray(Image.open(f"data/s1/labels/{seg}_inklabels_L.png").convert("L")) > 127
    Hc, Wc = CANVAS[seg]
    Lc = zoom(lab.astype(np.float32), S / ds, order=1)
    L = np.zeros((Hc // ds, Wc // ds), np.float32); y0, x0 = int(round(oy / ds)), int(round(ox / ds))
    h, w = min(Lc.shape[0], L.shape[0] - y0), min(Lc.shape[1], L.shape[1] - x0); L[y0:y0 + h, x0:x0 + w] = Lc[:h, :w]
    lab_c = L > 0.5
    r = int(round(5000 / 2.4 / ds)); yy, xx = np.ogrid[-r:r + 1, -r:r + 1]; disc = (yy * yy + xx * xx) <= r * r
    zone = binary_closing(lab_c, disc, iterations=1) | lab_c
    mid = np.asarray(Image.open(f"data/s1/{seg}/overview/onsheet_ds8.png"))
    mid = zoom(mid.astype(np.float32), (L.shape[0] / mid.shape[0], L.shape[1] / mid.shape[1]), order=0)
    on = mid > 0
    side = 6250 // ds; step = 1250 // ds
    dens = uniform_filter(lab_c.astype(np.float32), side, mode="constant")
    zf = uniform_filter(zone.astype(np.float32), side, mode="constant")
    of = uniform_filter(on.astype(np.float32), side, mode="constant")
    existing = [(c["y0"] // ds, c["x0"] // ds) for c in json.load(open(f"data/s1/{seg}/crops.json"))["crops"]]

    def sweep(zmin, omin, dmin):
        cands = []
        for y in range(side // 2, L.shape[0] - side // 2, step):
            for x in range(side // 2, L.shape[1] - side // 2, step):
                if zf[y, x] >= zmin and of[y, x] >= omin and dens[y, x] >= dmin:
                    cands.append((float(dens[y, x]), y - side // 2, x - side // 2))
        cands.sort(reverse=True)
        kept = [(0.0, ey, ex) for ey, ex in existing]          # new windows must also miss the existing crops
        n0 = len(kept)
        for c in cands:
            if all(abs(c[1] - k[1]) >= side or abs(c[2] - k[2]) >= side for k in kept): kept.append(c)
        return kept[n0:]

    tot = lab_c.sum()
    def cover(ws):
        m = np.zeros_like(lab_c)
        for _, y, x in ws: m[y:y + side, x:x + side] = True
        return float((lab_c & m).sum()) / tot

    base = cover([(0.0, ey, ex) for ey, ex in existing])
    print(f"\n{seg}: existing 4 crops cover {100*base:.1f}% of labelled pixels")
    for zmin, omin, dmin in ((0.99, 0.90, 0.0), (0.95, 0.75, 0.05), (0.90, 0.60, 0.05), (0.80, 0.50, 0.05)):
        w = sweep(zmin, omin, dmin)
        print(f"  zone>={zmin} onsheet>={omin} dens>={dmin}: +{len(w)} windows, "
              f"coverage {100*base:.1f}% -> {100*cover([(0.,ey,ex) for ey,ex in existing] + w):.1f}%, "
              f"densities {[round(c[0],3) for c in w[:8]]}")
