"""Step 5: the crispest form of the hypothesis.
(a) elongated (anisotropic) Gaussian integration, max-pooled over 12 orientations,
    vs an ISOTROPIC Gaussian OF THE SAME EFFECTIVE AREA  (sigma_eff = sqrt(sl*sw)).
    Aspect ratio 1 is literally the isotropic baseline, so the comparison is exact.
(b) the un-whitened matched filter h = c (mean ink stamp) and its radial average.
(c) lambda sweep of the Wiener solve.
All numbers are leave-one-crop-out over the 8 TRAINING crops (max-pool has no fitted
parameters, so for (a) the number is just the per-crop mean)."""
import sys, os, json, numpy as np
sys.path.insert(0, "/home/user/megara/scripts/explore")
from mf_lib import *
import mf_step4 as S4
from scipy.signal import fftconvolve
from scipy.ndimage import map_coordinates

def elong_maxpool(q, sl, sw, nth=12):
    rad = int(np.ceil(3 * max(sl, sw)))
    yy, xx = np.mgrid[-rad:rad + 1, -rad:rad + 1].astype(np.float32)
    best = None
    for k in range(nth):
        th = np.pi * k / nth
        u = xx * np.cos(th) + yy * np.sin(th)
        v = -xx * np.sin(th) + yy * np.cos(th)
        Kk = np.exp(-u * u / (2 * sl * sl) - v * v / (2 * sw * sw))
        Kk /= Kk.sum()
        r = fftconvolve(q, Kk, mode="same").astype(np.float32)
        best = r if best is None else np.maximum(best, r)
        if sl == sw:
            return r
    return best

if __name__ == "__main__":
    cache = {(s, c): S4.prep(s, c) for s, c in TRAIN}
    out = {}

    # ---- (a) matched area, aspect sweep ----
    print("== (a) anisotropic max-pool vs isotropic at equal area ==", flush=True)
    tab = {}
    for seff in [8, 11, 16, 22, 32]:
        for ar in [1, 2, 4, 8, 16]:
            sl = seff * np.sqrt(ar); sw = seff / np.sqrt(ar)
            if sw < 1.2: continue
            key = "seff%d_ar%d" % (seff, ar)
            aucs = []
            for s, c in TRAIN:
                q, v, t, b, sel = cache[(s, c)]
                sc = elong_maxpool(q, sl, sw)
                aucs.append(auc(sc[sel], t[sel], b[sel]))
            tab[key] = round(float(np.mean(aucs)), 4)
            print("  %-12s sl=%5.1f sw=%4.1f  TRAIN-mean AUC %.4f" % (key, sl, sw, tab[key]), flush=True)
    out["aspect_sweep"] = tab

    # ---- (b),(c) Wiener / template, LOCO ----
    print("== (b,c) Wiener lambda sweep + un-whitened template, LOCO ==", flush=True)
    parts = {k: S4.contrib(k[0], k[1], cache) for k in TRAIN}
    lam_res = {}
    for lam in [1e-3, 1e-2, 1e-1, 1.0, 10.0]:
        r_full, r_ani = [], []
        for held in TRAIN:
            A, C, CR = S4.accumulate([x for x in TRAIN if x != held], parts)
            hf = S4.solve(A, C, lam); ha = S4.solve(A, CR, lam)
            q, v, t, b, sel = cache[held]
            sc = fftconvolve(q, hf[::-1, ::-1], mode="same")
            r_full.append(auc(sc[sel], t[sel], b[sel]))
            sa = S4.apply_max_rot(q, ha)
            r_ani.append(auc(sa[sel], t[sel], b[sel]))
        lam_res["lam%g" % lam] = {"h_full": round(float(np.mean(r_full)), 4),
                                  "h_aniso_max": round(float(np.mean(r_ani)), 4)}
        print("  lam %-6g h_full %.4f  h_aniso_max %.4f" % (lam, np.mean(r_full), np.mean(r_ani)), flush=True)
    out["wiener_lambda"] = lam_res

    tmpl = {"template": [], "template_radial": [], "template_aniso_max": []}
    for held in TRAIN:
        A, C, CR = S4.accumulate([x for x in TRAIN if x != held], parts)
        q, v, t, b, sel = cache[held]
        for nm, h, rot in (("template", C, False), ("template_radial", S4.radialise(C), False),
                           ("template_aniso_max", CR, True)):
            sc = S4.apply_max_rot(q, np.asarray(h, np.float64)) if rot else \
                 fftconvolve(q, np.asarray(h)[::-1, ::-1], mode="same")
            tmpl[nm].append(auc(sc[sel], t[sel], b[sel]))
    out["template"] = {k: round(float(np.mean(v)), 4) for k, v in tmpl.items()}
    print("  un-whitened template:", out["template"], flush=True)
    json.dump(out, open("/home/user/megara/stats/explore/step5_shape_vs_iso.json", "w"), indent=1)
