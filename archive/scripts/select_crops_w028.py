#!/usr/bin/env python3
"""Deterministic crop selection for GATE-T1 on w028 (rule written before any residual is computed).
Candidate windows: 4 cm^2 squares (side = round(20000/2.399) = 8337 px at level 0), on a grid with
step 1024 px, entirely inside the canvas. Validity: on-sheet fraction (CT mid slice > 0 at level 4)
>= 0.95. Text fraction = fraction of window pixels with team prediction >= 0.40 (102/255).
TEXT crops: the 5 valid windows with the highest text fraction, chosen greedily, non-overlapping.
BLANK crops: the 2 valid windows with the lowest text fraction, non-overlapping with each other and
with the text crops. Coordinates are snapped down to multiples of 128 (chunk boundaries)."""
import numpy as np, json
PITCH = 2.399; SIDE = round(20000 / PITCH); STEP = 1024
pred = np.load("data/w028/overview/pred_ds20.npy")          # 20x block mean of team prediction, uint8
on4 = np.load("data/w028/overview/onsheet_l4.npy")          # level-4 (16x) on-sheet mask
H, W = 37420, 30340
cands = []
for y0 in range(0, H - SIDE + 1, STEP):
    for x0 in range(0, W - SIDE + 1, STEP):
        p = pred[y0 // 20:(y0 + SIDE) // 20, x0 // 20:(x0 + SIDE) // 20]
        o = on4[y0 // 16:(y0 + SIDE) // 16, x0 // 16:(x0 + SIDE) // 16]
        cands.append((y0, x0, float((p >= 102).mean()), float(o.mean())))
valid = [c for c in cands if c[3] >= 0.95]
def overlaps(a, b): return not (a[0] + SIDE <= b[0] or b[0] + SIDE <= a[0] or a[1] + SIDE <= b[1] or b[1] + SIDE <= a[1])
chosen = []
for c in sorted(valid, key=lambda c: -c[2]):
    if len(chosen) == 5: break
    if all(not overlaps(c, d) for d in chosen): chosen.append(c)
text = [dict(name=f"text{i+1}", y0=c[0], x0=c[1], side=SIDE, text_frac=round(c[2], 3), onsheet=round(c[3], 3), kind="text") for i, c in enumerate(chosen)]
blank = []
for c in sorted(valid, key=lambda c: c[2]):
    if len(blank) == 2: break
    if all(not overlaps(c, d) for d in chosen + blank): blank.append(c)
blank = [dict(name=f"blank{i+1}", y0=c[0], x0=c[1], side=SIDE, text_frac=round(c[2], 3), onsheet=round(c[3], 3), kind="blank") for i, c in enumerate(blank)]
out = dict(pitch_um=PITCH, side_px=SIDE, rule=__doc__, n_candidates=len(cands), n_valid=len(valid), crops=text + blank)
json.dump(out, open("data/w028/crops.json", "w"), indent=1)
for c in text + blank: print(c)
