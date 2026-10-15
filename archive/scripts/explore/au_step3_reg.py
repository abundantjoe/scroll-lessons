"""AUDIT step 3: how big is the registration residual, and what AUC ceiling does it imply?

A) residual: the (dy,dx) that best aligns the hand label with the team model's ink map, measured
   globally and per 3 mm tile on the 19.2 um grid.  The spread of the per-tile shifts is the
   within-crop registration residual that no global offset can remove.
B) ceiling: AUC of an ORACLE detector that is perfect but displaced by delta mm, measured against
   the same text/blank classes.  Two oracles: the team map (a real near-perfect detector) and the
   binary label itself (a literally perfect detector).  Displacement is applied to the class masks,
   which is identical to displacing the detector, and averaged over 8 directions.
C) the displacement delta* at which the oracle falls to our measured AUC.

usage: au_step3_reg.py <seg> <crop>
"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import au_lib as A

seg, crop = sys.argv[1], sys.argv[2]
rng = np.random.default_rng(7)
t0 = time.time()
L, text, blank, m = A.load_masks(seg, crop)
team = A.load_score(seg, crop, "team")

# ---------- A) registration residual on the 19.2 um grid ----------
B = 8                                            # 8 px = 19.2 um
n = L.shape[0] // B
def pool(a):
    return a[:n * B, :n * B].reshape(n, B, n, B).mean(axis=(1, 3)).astype(np.float32)
Lp = pool(L.astype(np.float32))
Tp = pool((team > 0.5).astype(np.float32))
Mp = pool(m.astype(np.float32))
valid = Mp > 0.5

def best_shift(lp, tp, vv, R=16):
    """shift applied to the LABEL; returns (dy,dx) cells maximising normalised correlation."""
    best, bs = -9e9, (0, 0)
    prof = np.full((2 * R + 1, 2 * R + 1), np.nan, np.float32)
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            ls = A.shift(lp, dy, dx)
            w = vv
            a = ls[w]; b = tp[w]
            if a.std() < 1e-6 or b.std() < 1e-6:
                continue
            c = float(((a - a.mean()) * (b - b.mean())).mean() / (a.std() * b.std()))
            prof[dy + R, dx + R] = c
            if c > best:
                best, bs = c, (dy, dx)
    return bs, best, prof

gs, gc, prof = best_shift(Lp, Tp, valid)
out = {"seg": seg, "crop": crop,
       "global_shift_cells": list(gs), "global_shift_um": [gs[0] * 19.2, gs[1] * 19.2],
       "global_corr": round(gc, 4), "corr_at_zero": round(float(prof[16, 16]), 4)}
print("global", out, flush=True)

# per-tile residual (tiles of 156 cells = 3.0 mm)
TS = 156
tiles = []
for ty in range(0, n - TS + 1, TS):
    for tx in range(0, n - TS + 1, TS):
        vv = valid[ty:ty + TS, tx:tx + TS]
        lp = Lp[ty:ty + TS, tx:tx + TS]; tp = Tp[ty:ty + TS, tx:tx + TS]
        if vv.sum() < 0.2 * TS * TS or lp[vv].mean() < 0.02:
            continue
        s, c, _ = best_shift(lp, tp, vv, R=12)
        tiles.append({"ty": ty, "tx": tx, "dy": s[0], "dx": s[1], "corr": round(c, 4)})
dy = np.array([t["dy"] for t in tiles], float) * 19.2
dx = np.array([t["dx"] for t in tiles], float) * 19.2
out["n_tiles"] = len(tiles)
out["tiles"] = tiles
if len(tiles):
    r = np.hypot(dy - dy.mean(), dx - dx.mean())
    out["tile_shift_um_mean"] = [round(float(dy.mean()), 1), round(float(dx.mean()), 1)]
    out["tile_shift_um_std"] = [round(float(dy.std()), 1), round(float(dx.std()), 1)]
    out["residual_um_rms_about_tile_mean"] = round(float(np.sqrt((r ** 2).mean())), 1)
    out["residual_um_max"] = round(float(r.max()), 1)
    gr = np.hypot(dy, dx)
    out["residual_um_rms_about_zero"] = round(float(np.sqrt((gr ** 2).mean())), 1)
print("tiles", out.get("tile_shift_um_mean"), out.get("tile_shift_um_std"),
      "rms", out.get("residual_um_rms_about_tile_mean"), "max", out.get("residual_um_max"), flush=True)

# ---------- B) oracle degradation with displacement ----------
DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
DELTA_MM = [0.0, 0.024, 0.048, 0.096, 0.144, 0.192, 0.288, 0.384, 0.48, 0.72, 0.96, 1.44]
Lf = L.astype(np.float32)
curve = {}
for dmm in DELTA_MM:
    px = dmm / A.MM
    accT, accL, k = [], [], 0
    dirs = DIRS if dmm > 0 else [(0, 0)]
    for uy, ux in dirs:
        nrm = np.hypot(uy, ux) or 1.0
        sy = int(round(px * uy / nrm)); sx = int(round(px * ux / nrm))
        p = A.shift(text, sy, sx, False); q = A.shift(blank, sy, sx, False)
        p &= m; q &= m
        if p.sum() < 1000 or q.sum() < 1000:
            continue
        v1, _, _ = A.auc_masked(team, p, q, rng)
        v2, _, _ = A.auc_masked(Lf, p, q, rng)
        if v1 is not None:
            accT.append(v1); accL.append(v2); k += 1
    curve[f"{dmm:g}"] = {"n_dir": k,
                         "oracle_team": round(float(np.mean(accT)), 4) if k else None,
                         "oracle_label": round(float(np.mean(accL)), 4) if k else None}
    print("  delta", dmm, curve[f"{dmm:g}"], flush=True)
out["oracle_vs_displacement_mm"] = curve
A.jwrite(os.path.join(A.ROOT, f"stats/explore/au_step3_{seg}_{crop}.json"), out)
print(f"done {time.time()-t0:.0f}s", flush=True)
