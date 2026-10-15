"""Reading run R1 (RULES.md): choose unread windows by the declared rule, mechanically.

Windows of 6250 canvas px with on-sheet coverage >= 0.90 and NO labelled pixel within 5 mm.
  reading window  = the admissible window whose centre is NEAREST the labelled zone (ties: lower row index)
  control window  = the admissible window whose centre is FARTHEST from the labelled zone (the declared negative control)
Writes data/s1/<seg>/unread.json. Chooses locations only; no score map is computed or consulted.
"""
import json, sys, numpy as np
from PIL import Image
from scipy.ndimage import binary_closing, uniform_filter, zoom, distance_transform_edt
Image.MAX_IMAGE_PIXELS = None

CANVAS = {"20231005123336": (34880, 97280), "20231210121321": (51000, 39980),
          "20230929220926": (32080, 75800), "20231012184424": (50800, 75720)}
ds = 40

for seg in sys.argv[1:]:
    reg = json.load(open(f"data/s1/{seg}/label_registration.json"))
    S, oy, ox = reg["scale_label_to_canvas"], reg["offset_canvas_y"], reg["offset_canvas_x"]
    import os
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

    mp = f"data/s1/{seg}/overview/onsheet_ds8.png"
    if not os.path.exists(mp): mp = f"data/s1/{seg}/overview/render_ds8.jpg"
    mid = np.asarray(Image.open(mp).convert("L"))
    mid = zoom(mid.astype(np.float32), (L.shape[0] / mid.shape[0], L.shape[1] / mid.shape[1]), order=0)
    on = mid > 0

    side = 6250 // ds; step = 1250 // ds
    of = uniform_filter(on.astype(np.float32), side, mode="constant")
    # distance from every cell to the nearest labelled pixel, in mm
    dmm = distance_transform_edt(~lab_c) * ds * 2.4 / 1000.0
    # a window is admissible if no labelled pixel lies within 5 mm of ANY of its cells:
    # equivalently the minimum of dmm over the window exceeds 5 mm + half the window diagonal is not needed -
    # we require the window's own cells to all be > 5 mm from a label.
    near = (dmm <= 5.0).astype(np.float32)
    nf = uniform_filter(near, side, mode="constant")

    cands = []
    for y in range(side // 2, L.shape[0] - side // 2, step):
        for x in range(side // 2, L.shape[1] - side // 2, step):
            if of[y, x] >= 0.90 and nf[y, x] == 0.0:
                cands.append((float(dmm[y, x]), y - side // 2, x - side // 2))
    if not cands:
        print(f"{seg}: NO admissible unread window (on-sheet >= 0.90 and > 5 mm from every label)")
        continue
    cands.sort(key=lambda c: (c[0], c[1]))
    read_w = cands[0]                      # nearest the labelled zone
    ctrl_w = cands[-1]                     # farthest - the declared negative control
    out = {"segment": seg, "rule": "on-sheet >= 0.90, no labelled pixel within 5 mm; reading = nearest label, control = farthest",
           "n_admissible": len(cands),
           "crops": [{"name": "unread1", "kind": "reading", "y0": int(read_w[1] * ds), "x0": int(read_w[2] * ds),
                      "side": 6250, "dist_to_label_mm": round(read_w[0], 2)},
                     {"name": "control1", "kind": "control", "y0": int(ctrl_w[1] * ds), "x0": int(ctrl_w[2] * ds),
                      "side": 6250, "dist_to_label_mm": round(ctrl_w[0], 2)}]}
    json.dump(out, open(f"data/s1/{seg}/unread.json", "w"), indent=1)
    print(f"{seg}: {len(cands)} admissible; reading at ({out['crops'][0]['y0']},{out['crops'][0]['x0']}) "
          f"{read_w[0]:.1f} mm from label; control at ({out['crops'][1]['y0']},{out['crops'][1]['x0']}) {ctrl_w[0]:.1f} mm")
