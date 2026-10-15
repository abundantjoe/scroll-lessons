"""FINAL held-out run. Everything below is frozen from TRAINING crops only.

Models (all built on the same pooled stack ds8_x):
  gauss16      : project with the step-1 depth weights, then a single isotropic
                 Gaussian, sigma = 16 px = 0.31 mm   (plain-smoothing baseline)
  dxs_iso      : 22 depth channels x 8 ISOTROPIC scales, logistic  (isotropic control)
  dxs_both     : the same plus 22 x 6 ANISOTROPIC orientation-max-pooled channels
                 (elongated Gaussians, 12 orientations)             (shape-matched)
Existing methods re-measured by this script on the same pixels: v2, v3, team.

Reported: pixel AUC on the 19.2 um grid (official ds8_y), and judge-identical
pixel AUC + letter AUC at 2.4 um on cls_text / cls_blank.
Nothing is written into data/."""
import sys, os, json, numpy as np
sys.path.insert(0, "/home/user/megara/scripts/explore")
from mf_lib import *
from scipy.ndimage import gaussian_filter, zoom, label as cclabel, distance_transform_edt
from scipy.signal import fftconvolve
from scipy.stats import rankdata

SC = [0, 2, 4, 8, 11, 16, 22, 32]
ANI = [(8, 2), (8, 4), (11, 4), (16, 2), (16, 4), (22, 2)]
NTH = 12
LAM_BOTH = 1.0   # LOCO-best for DxS-ISO+ANISO (step9)
LAM_ISO  = 0.3   # LOCO-best for DxS-ISO   (step9)
PW = np.load("/home/user/megara/stats/explore/proj_w.npy").astype(np.float32)

def maxpool(q, sl, sw):
    rad = int(np.ceil(3 * max(sl, sw)))
    yy, xx = np.mgrid[-rad:rad + 1, -rad:rad + 1].astype(np.float32)
    best = None
    for k in range(NTH):
        th = np.pi * k / NTH
        u = xx * np.cos(th) + yy * np.sin(th); v = -xx * np.sin(th) + yy * np.cos(th)
        Kk = np.exp(-u * u / (2 * sl * sl) - v * v / (2 * sw * sw)); Kk /= Kk.sum()
        r = fftconvolve(q, Kk, mode="same").astype(np.float32)
        best = r if best is None else np.maximum(best, r)
    return best

def channels(s, c):
    """yields (kind, feature map) for the crop; kind in {'iso','ani'}"""
    x, mp = load_x(s, c)
    m = (mp > 0.5).astype(np.float32)
    den = gaussian_filter(m, 2.0, mode="constant")
    valid = mp > 0.5
    for i in range(22):
        num = gaussian_filter(x[i] * m, 2.0, mode="constant")
        qi = np.where(den > 1e-3, num / np.maximum(den, 1e-6), 0.0).astype(np.float32)
        for sg in SC:
            yield "iso", (gaussian_filter(qi, sg, mode="nearest") if sg else qi)
        for seff, ar in ANI:
            yield "ani", maxpool(qi, seff * np.sqrt(ar), seff / np.sqrt(ar))

def design(s, c, sel):
    """one pass: standardise each feature by its own mean/sd over the crop's valid mask
    (no label information is used for the standardisation)."""
    x, mp = load_x(s, c); valid = mp > 0.5
    cols, kinds = [], []
    for kind, f in channels(s, c):
        v = f[valid]; mu = float(v.mean()); sd = float(v.std()) + 1e-6
        cols.append(((f[sel] - mu) / sd).astype(np.float32)); kinds.append(kind)
    return np.stack(cols, 1), kinds

def score_maps(s, c, wlist):
    """one pass: returns a list of dense score maps, one per weight vector."""
    x, mp = load_x(s, c); valid = mp > 0.5
    outs = [np.zeros(mp.shape, np.float32) for _ in wlist]
    for j, (kind, f) in enumerate(channels(s, c)):
        v = f[valid]; mu = float(v.mean()); sd = float(v.std()) + 1e-6
        z = (f - mu) / sd
        for o, w in zip(outs, wlist):
            if w[j] != 0.0:
                o += w[j] * z
    return [np.where(valid, o, 0.0) for o in outs], valid

def proj_gauss(s, c, sigma=16.0):
    x, mp = load_x(s, c)
    m = (mp > 0.5).astype(np.float32)
    pj = np.tensordot(PW, x, axes=(0, 0)).astype(np.float32)
    num = gaussian_filter(pj * m, 2.0, mode="constant"); den = gaussian_filter(m, 2.0, mode="constant")
    q = np.where(den > 1e-3, num / np.maximum(den, 1e-6), 0.0).astype(np.float32)
    return gaussian_filter(q, sigma, mode="nearest"), mp > 0.5

# ---------- judge-identical full-resolution evaluation ----------
def judge_like(d, sfull, pitch=2.4):
    text = np.load(d + "/cls_text.npy"); blank = np.load(d + "/cls_blank.npy")
    L = np.load(d + "/label.npy")
    rng = np.random.default_rng(0); sub = rng.random(text.shape) < 0.05
    a = sfull[text & sub]; z = sfull[blank & sub]
    rk = rankdata(np.concatenate([a, z])); n1, n0 = len(a), len(z)
    apx = float((rk[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
    lab_cc, n = cclabel(L); sizes = np.bincount(lab_cc.ravel())
    min_px = 0.5e6 / (pitch * pitch)
    letters = [i for i in range(1, n + 1) if sizes[i] >= min_px]
    by, bx = np.where(blank)
    wins = tot = 0
    for i in letters:
        yy, xx = np.where(lab_cc == i); mm = text[yy, xx]
        if mm.sum() < 0.5 * len(yy): continue
        ms = sfull[yy[mm], xx[mm]].mean(); rad = int(np.sqrt(mm.sum() / np.pi))
        for _ in range(200):
            j = rng.integers(len(by)); cy, cx = by[j], bx[j]
            ys, xs = slice(max(cy - rad, 0), cy + rad + 1), slice(max(cx - rad, 0), cx + rad + 1)
            bm = blank[ys, xs]
            if bm.sum() < 0.5 * np.pi * rad * rad: continue
            tot += 1; wins += float(sfull[ys, xs][bm].mean() < ms)
    return apx, (wins / tot if tot else None), len(letters)

def up8(s8, shape):
    u = np.repeat(np.repeat(np.nan_to_num(s8, nan=0.0), 8, 0), 8, 1)
    out = np.zeros(shape, np.float32)
    h = min(shape[0], u.shape[0]); w = min(shape[1], u.shape[1])
    out[:h, :w] = u[:h, :w]
    return out

if __name__ == "__main__":
    # ---------- fit on the 8 TRAINING crops ----------
    print("fitting on TRAIN (%d crops)" % len(TRAIN), flush=True)
    Xs, ys, ws, kinds = [], [], [], None
    for s, c in TRAIN:
        t, b = ds8_labels(s, c)
        x, mp = load_x(s, c)
        sel = (t | b) & (mp > 0.5)
        sub = np.zeros_like(sel); sub[::2, ::2] = True; sel = sel & sub
        X, kinds = design(s, c, sel); y = t[sel].astype(np.int8)
        w = np.where(y == 1, 1.0 / max(y.sum(), 1), 1.0 / max((y == 0).sum(), 1))
        Xs.append(X); ys.append(y); ws.append(w)
        print("  train feats", s, c, X.shape, flush=True)
    kinds = np.array(kinds)
    Xa = np.concatenate(Xs); ya = np.concatenate(ys); wa = np.concatenate(ws)
    iso_only = kinds == "iso"
    w_both, _ = fit_logistic(Xa, ya, wa, l2=LAM_BOTH)
    w_iso, _ = fit_logistic(Xa[:, iso_only], ya, wa, l2=LAM_ISO)
    W_ISO = np.zeros(len(kinds)); W_ISO[iso_only] = w_iso
    del Xs, Xa
    np.savez("/home/user/megara/stats/explore/final_weights.npz",
             w_both=w_both, w_iso=W_ISO, kinds=kinds, SC=np.array(SC), ANI=np.array(ANI),
             lam_both=LAM_BOTH, lam_iso=LAM_ISO)
    print("fitted.", flush=True)

    # ---------- held-out ----------
    res = {}
    for s, c in EVAL:
        d = cropdir(s, c)
        y8 = np.load(d + "/ds8_y.npy")
        t8, b8 = (y8 == 1), (y8 == 0)
        (sb, si), valid = score_maps(s, c, [w_both, W_ISO])
        maps = {"dxs_both": sb, "dxs_iso": si, "gauss16": proj_gauss(s, c)[0]}
        r = {}
        for k, v in maps.items():
            r[k] = {"ds8_auc_px": round(auc(np.nan_to_num(v, nan=0.0), t8, b8), 4)}
        # existing methods, block-mean-pooled to the same 19.2 um grid
        for tag in ("v2", "v3", "team"):
            p = d + f"/s_bot_{tag}.npy"
            if not os.path.exists(p): continue
            a = np.load(p).astype(np.float32)
            H8 = a.shape[0] // 8
            ap = a[:H8 * 8, :H8 * 8].reshape(H8, 8, H8, 8).mean(axis=(1, 3))
            r[tag] = {"ds8_auc_px": round(auc(ap, t8, b8), 4)}
            px, lt, nl = judge_like(d, a)
            r[tag].update({"full_auc_px": round(px, 4),
                           "full_auc_letter": (round(lt, 4) if lt else None), "n_letters": nl})
            del a, ap
        for k, v in maps.items():
            sf = up8(v, (6250, 6250))
            px, lt, nl = judge_like(d, sf)
            r[k].update({"full_auc_px": round(px, 4),
                         "full_auc_letter": (round(lt, 4) if lt else None), "n_letters": nl})
            del sf
        res[f"{s}/{c}"] = r
        print(f"{s}/{c}", json.dumps(r), flush=True)
    keys = sorted({k for v in res.values() for k in v})
    summary = {}
    for k in keys:
        for met in ("ds8_auc_px", "full_auc_px", "full_auc_letter"):
            vals = [res[x][k][met] for x in res if k in res[x] and res[x][k].get(met) is not None]
            if vals: summary.setdefault(k, {})[met] = round(float(np.mean(vals)), 4)
    print("\n=== HELD-OUT MEANS (7 EVAL crops) ===")
    for k in keys:
        print("  %-9s" % k, summary.get(k))
    json.dump({"per_crop": res, "held_out_mean": summary,
               "lam_both": LAM_BOTH, "lam_iso": LAM_ISO},
              open("/home/user/megara/stats/explore/final_heldout.json", "w"), indent=1)
