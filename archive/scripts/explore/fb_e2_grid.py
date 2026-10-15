"""E2 (ds8 grid, 19.2 um/px, TRAINING crops only): does removing the papyrus background in the
FIBRE FRAME beat removing it isotropically?
feature = G_sigma_int( S_pre - bg ),  S_pre = G_0.04mm(S_bot_band)
bg = anisotropic local mean, sigma_along along the estimated fibre direction, sigma_across across it.
Controls: theta+90 (long window ACROSS the fibre), a constant global theta, and the isotropic
background with the same window area."""
import os, sys, json, itertools, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from fb_lib import *

MM = 1000.0 / PITCH          # px per mm
CH_BOT = [11, 12, 13, 14]
SIG_PRE = 0.04 * MM
SIG_INT = [0.10 * MM, 0.25 * MM]
ACROSS = [0.04, 0.08, 0.15, 0.30]      # mm
ALONG = [0.15, 0.30, 0.60, 1.20, 2.40]  # mm
TENSOR = [4, 16]                        # structure-tensor sigma in px (77, 307 um)

crops = TRAIN_CROPS
rows = {}
for seg, crop in crops:
    x, _, m = load(seg, crop)
    y = fit_classes(seg, crop)
    S = x[CH_BOT].mean(axis=0)
    Spre = nconv(S, m, SIG_PRE)
    pos = (y == 1) & m; neg = (y == 0) & m
    rec = {}

    def add(name, r):
        for i, si in enumerate(SIG_INT):
            f = nconv(r, m, si)
            rec[f"{name}|int{['0.10','0.25'][i]}"] = round(auc(f, pos, neg), 4)

    # reference: isotropic band-pass (the family v2 belongs to)
    for sb in (0.30, 0.60, 1.20, 2.40, 3.00):
        add(f"iso|bg{sb:.2f}", Spre - nconv(Spre, m, sb * MM))
    thetas = {}
    for st in TENSOR:
        th, coh = structure_tensor(S, m, 1.0, st)
        thetas[st] = th
    for st in TENSOR:
        th = thetas[st]
        for sa, sl in itertools.product(ACROSS, ALONG):
            if sl <= sa:
                continue
            bg = oriented_filter(Spre, m, th, sl * MM, sa * MM)
            add(f"or{st}|a{sa:.2f}|l{sl:.2f}", Spre - bg)
            if sa == 0.08 and sl in (0.60, 2.40):
                bg90 = oriented_filter(Spre, m, th + np.pi / 2, sl * MM, sa * MM)
                add(f"perp{st}|a{sa:.2f}|l{sl:.2f}", Spre - bg90)
                thc = np.full_like(th, float(np.median(np.mod(th[m], np.pi))))
                bgc = oriented_filter(Spre, m, thc, sl * MM, sa * MM)
                add(f"const{st}|a{sa:.2f}|l{sl:.2f}", Spre - bgc)
                # isotropic background with the same window area
                se = np.sqrt(sa * sl)
                add(f"isoarea|a{sa:.2f}|l{sl:.2f}", Spre - nconv(Spre, m, se * MM))
    rows[f"{seg}/{crop}"] = rec
    print("done", seg, crop, len(rec), flush=True)

json.dump(rows, open(os.path.join(ROOT, "stats/explore/fb_e2_grid.json"), "w"), indent=1)
keys = list(next(iter(rows.values())).keys())
mean = {k: float(np.mean([rows[c][k] for c in rows])) for k in keys}
print("\n== TRAIN mean AUC over %d crops, top 25" % len(rows))
for k, v in sorted(mean.items(), key=lambda t: -t[1])[:25]:
    print(f"  {v:.4f}  {k}")
print("\n== isotropic reference")
for k in keys:
    if k.startswith("iso|"):
        print(f"  {mean[k]:.4f}  {k}")
