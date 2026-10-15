"""E6 (ds8, TRAINING crops): the full-resolution sweep found the best background window direction
at ~90 deg, which on that crop is BOTH the papyrus structure direction and the perpendicular to the
text lines. Separate them: on eight training crops, find the AUC-optimal constant window angle and
compare it with (a) the papyrus direction from the structure tensor (measured on blank pixels, no
ink can steer it) and (b) the text-line direction from the label field's line-spacing spectrum.
If the optimum follows the papyrus direction, the effect is fibre physics; if it follows the text
lines, it is the background window falling into the inter-line gaps."""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from fb_lib import *

MM = 1000.0 / PITCH
CH_BOT = [11, 12, 13, 14]

def line_direction(lab, m):
    """direction of the TEXT LINES: the 2-D power spectrum of the label field has a peak at the
    line pitch in the direction PERPENDICULAR to the lines; returns (line_dir_deg, pitch_mm, power)."""
    f = (lab.astype(np.float32) - lab[m].mean() * m)
    H, W = f.shape
    win = np.outer(np.hanning(H), np.hanning(W)).astype(np.float32)
    P = np.abs(np.fft.fftshift(np.fft.fft2(f * win))) ** 2
    cy, cx = H // 2, W // 2
    yy, xx = np.mgrid[0:H, 0:W]
    fy = (yy - cy) / H; fx = (xx - cx) / W          # cycles per pixel
    r = np.hypot(fy, fx)
    lo = PITCH / 10000.0; hi = PITCH / 3000.0        # 1/(10 mm) .. 1/(3 mm) in cycles/px
    band = (r > lo) & (r < hi)
    idx = np.argmax(np.where(band, P, -1))
    iy, ix = np.unravel_index(idx, P.shape)
    ang_perp = np.rad2deg(np.arctan2(fy[iy, ix], fx[iy, ix])) % 180   # direction of the wave vector
    line_dir = (ang_perp + 90) % 180
    pitch_mm = 1.0 / max(r[iy, ix], 1e-9) * PITCH / 1000.0
    return round(float(line_dir), 1), round(float(pitch_mm), 2)

res = {}
for seg, crop in TRAIN_CROPS:
    x, _, m = load(seg, crop)
    y = fit_classes(seg, crop)
    S = x[CH_BOT].mean(axis=0)
    Spre = nconv(S, m, 0.04 * MM)
    pos = (y == 1) & m; neg = (y == 0) & m
    rec = {}
    for st in (4, 16, 32):
        th, _ = structure_tensor(S, m, 1.0, st)
        for nm, sel in (("all", m), ("blank", neg)):
            t = np.mod(th[sel], np.pi)
            a = np.rad2deg(np.mod(np.arctan2(np.sin(2 * t).mean(), np.cos(2 * t).mean()) / 2, np.pi))
            R = float(np.hypot(np.cos(2 * t).mean(), np.sin(2 * t).mean()))
            rec[f"theta_st{st}_{nm}"] = [round(float(a), 1), round(R, 3)]
    rec["line_dir_deg"], rec["line_pitch_mm"] = line_direction((y == 1).astype(np.float32), m)
    sweep = {}
    for ang in range(0, 180, 15):
        F = np.full(S.shape, np.deg2rad(ang), np.float32)
        bg = oriented_filter(Spre, m, F, 3.0 * MM, 0.12 * MM, n_orient=180)
        sweep[ang] = round(auc(nconv(Spre - bg, m, 0.40 * MM), pos, neg), 4)
    rec["sweep"] = sweep
    rec["best_angle"] = max(sweep, key=lambda a: sweep[a])
    rec["best_auc"] = sweep[rec["best_angle"]]
    rec["auc_at_theta_st16blank"] = None
    a0 = rec["theta_st16_blank"][0]
    F = np.full(S.shape, np.deg2rad(a0), np.float32)
    bg = oriented_filter(Spre, m, F, 3.0 * MM, 0.12 * MM, n_orient=360)
    rec["auc_at_theta_st16blank"] = round(auc(nconv(Spre - bg, m, 0.40 * MM), pos, neg), 4)
    a1 = (rec["line_dir_deg"] + 90) % 180
    F = np.full(S.shape, np.deg2rad(a1), np.float32)
    bg = oriented_filter(Spre, m, F, 3.0 * MM, 0.12 * MM, n_orient=360)
    rec["auc_perp_to_lines"] = round(auc(nconv(Spre - bg, m, 0.40 * MM), pos, neg), 4)
    res[f"{seg}/{crop}"] = rec
    print(f"{seg}/{crop} best={rec['best_angle']} ({rec['best_auc']}) theta_ST16blank={rec['theta_st16_blank']} "
          f"line_dir={rec['line_dir_deg']} pitch={rec['line_pitch_mm']}mm "
          f"auc@ST={rec['auc_at_theta_st16blank']} auc@perp_lines={rec['auc_perp_to_lines']}", flush=True)
    print("   sweep", sweep, flush=True)

json.dump(res, open(os.path.join(ROOT, "stats/explore/fb_e6_confound.json"), "w"), indent=1)
