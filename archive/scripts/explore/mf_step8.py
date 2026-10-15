"""Step 8: the hypothesis re-tested on the STRONGER base.
Smoothing each depth channel before combining (depth x scale) reaches LOCO 0.708,
well above project-then-smooth (0.672). On that base:
  DxS-ISO        : 22 channels x N isotropic scales                    (isotropic control)
  DxS-ANISO      : 22 channels x N anisotropic max-pools (ar=2,4)      (shape only)
  DxS-ISO+ANISO  : both
Equal number of channels, equal effective areas -> the ONLY difference is filter shape.
Leave-one-crop-out over the 8 TRAINING crops. Pixels subsampled 1-in-4 for memory."""
import sys, os, json, numpy as np
sys.path.insert(0, "/home/user/megara/scripts/explore")
from mf_lib import *
from scipy.ndimage import gaussian_filter
from scipy.signal import fftconvolve

SC = [0, 4, 8, 16, 32]
ANI = [(8, 4), (16, 2), (16, 4), (32, 2)]     # (sigma_eff, aspect ratio)
NTH = 12

def maxpool(q, sl, sw, nth=NTH):
    rad = int(np.ceil(3 * max(sl, sw)))
    yy, xx = np.mgrid[-rad:rad + 1, -rad:rad + 1].astype(np.float32)
    best = None
    for k in range(nth):
        th = np.pi * k / nth
        u = xx * np.cos(th) + yy * np.sin(th); v = -xx * np.sin(th) + yy * np.cos(th)
        Kk = np.exp(-u * u / (2 * sl * sl) - v * v / (2 * sw * sw)); Kk /= Kk.sum()
        r = fftconvolve(q, Kk, mode="same").astype(np.float32)
        best = r if best is None else np.maximum(best, r)
    return best

def crop_feats(s, c, stride=2):
    x, mp = load_x(s, c)
    t, b = ds8_labels(s, c)
    m = (mp > 0.5).astype(np.float32)
    den = gaussian_filter(m, 2.0, mode="constant")
    sel = (t | b) & (mp > 0.5)
    sub = np.zeros_like(sel); sub[::stride, ::stride] = True
    sel = sel & sub
    ISO, AN = [], []
    for i in range(22):
        num = gaussian_filter(x[i] * m, 2.0, mode="constant")
        qi = np.where(den > 1e-3, num / np.maximum(den, 1e-6), 0.0).astype(np.float32)
        for sg in SC:
            ISO.append((gaussian_filter(qi, sg, mode="nearest") if sg else qi)[sel])
        for seff, ar in ANI:
            AN.append(maxpool(qi, seff * np.sqrt(ar), seff / np.sqrt(ar))[sel])
    return (np.stack(ISO, 1).astype(np.float32), np.stack(AN, 1).astype(np.float32),
            t[sel].astype(np.int8), b[sel])

def loco(D, pick, lam):
    aucs = []
    for held in TRAIN:
        Xs, ys, ws = [], [], []
        for k in TRAIN:
            if k == held: continue
            X = pick(D[k]); y = D[k][2]
            X = (X - X.mean(0)) / (X.std(0) + 1e-6)
            w = np.where(y == 1, 1.0 / max(y.sum(), 1), 1.0 / max((y == 0).sum(), 1))
            Xs.append(X); ys.append(y); ws.append(w)
        wt, _ = fit_logistic(np.concatenate(Xs), np.concatenate(ys), np.concatenate(ws), l2=lam)
        Xh = pick(D[held]); Xh = (Xh - Xh.mean(0)) / (Xh.std(0) + 1e-6)
        yh = D[held][2]
        aucs.append(auc(Xh @ wt, yh == 1, yh == 0))
    return aucs

if __name__ == "__main__":
    D = {}
    for s, c in TRAIN:
        D[(s, c)] = crop_feats(s, c)
        print("feat", s, c, D[(s, c)][0].shape, D[(s, c)][1].shape, flush=True)
    picks = {"DxS-ISO": lambda d: d[0],
             "DxS-ANISO": lambda d: d[1],
             "DxS-ISO+ANISO": lambda d: np.concatenate([d[0], d[1]], 1)}
    out = {}
    for nm, pk in picks.items():
        for lam in [0.1, 0.3, 1.0, 3.0]:
            a = loco(D, pk, lam)
            out["%s_l2_%g" % (nm, lam)] = {"folds": [round(v, 4) for v in a],
                                           "mean": round(float(np.mean(a)), 4)}
            print("%-14s l2=%-5g LOCO %.4f" % (nm, lam, np.mean(a)), flush=True)
    json.dump(out, open("/home/user/megara/stats/explore/step8_dxs_shape.json", "w"), indent=1)
