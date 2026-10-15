"""E4+E5 (ds8 grid, TRAINING crops only). Builds a fibre-frame feature bank per crop, reports the
single-feature TRAIN AUCs (E4), and asks with leave-one-crop-out logistic regression whether the
FIBRE-FRAME features add anything on top of the isotropic ones (E5).
Nothing here touches an EVALUATION crop."""
import os, sys, json, numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
from fb_lib import *

MM = 1000.0 / PITCH
CH_BOT = [11, 12, 13, 14]
CH_TOP = [3, 4, 5]
SIG_PRE = 0.04 * MM
INT = 0.25 * MM
ST = 16
BANK = os.path.join(ROOT, "stats/explore/fb_bank")
os.makedirs(BANK, exist_ok=True)

ISO_KEYS = ["plain_g10", "plain_g25", "top_g25", "bp0.60", "bp1.20", "bp2.40", "bp3.00", "std_iso", "std_iso2"]
FIB_KEYS = ([f"or_a{a}_l{l}" for a in ("0.04", "0.08", "0.15", "0.30") for l in ("0.60", "1.20", "2.40")]
            + ["std_acr", "std_alo", "std_ratio", "std_acr2", "std_alo2", "std_ratio2",
               "coh", "cv_acr", "ratio_l0.6", "ratio_l2.4", "or_a0.08_l0.60_perp", "or_a0.08_l0.60_const"]
            + [f"tophat_l{l}_w{w}" for l in ("0.60", "1.20", "2.40") for w in ("0.04", "0.15")]
            + ["tophat_l1.20_w0.15_perp", "tophat_l1.20_w0.15_const", "tophat_iso_1.20"])


def build(seg, crop):
    p = os.path.join(BANK, f"{seg}_{crop}.npz")
    if os.path.exists(p):
        z = np.load(p)
        return {k: z[k] for k in z.files if k not in ("sel", "pos")}, z["sel"], z["pos"]
    x, _, m = load(seg, crop)
    y = fit_classes(seg, crop)
    S = x[CH_BOT].mean(axis=0); T = x[CH_TOP].mean(axis=0)
    Spre = nconv(S, m, SIG_PRE)
    th, coh = structure_tensor(S, m, 1.0, ST)
    f = {}
    f["plain_g10"] = nconv(Spre, m, 0.10 * MM)
    f["plain_g25"] = nconv(Spre, m, INT)
    f["top_g25"] = nconv(nconv(T, m, SIG_PRE), m, INT)
    for sb in ("0.60", "1.20", "2.40", "3.00"):
        f[f"bp{sb}"] = nconv(Spre - nconv(Spre, m, float(sb) * MM), m, INT)
    for a in ("0.04", "0.08", "0.15", "0.30"):
        for l in ("0.60", "1.20", "2.40"):
            bg = oriented_filter(Spre, m, th, float(l) * MM, float(a) * MM)
            f[f"or_a{a}_l{l}"] = nconv(Spre - bg, m, INT)
    bg = oriented_filter(Spre, m, th + np.pi / 2, 0.60 * MM, 0.08 * MM)
    f["or_a0.08_l0.60_perp"] = nconv(Spre - bg, m, INT)
    thc = np.full_like(th, float(np.median(np.mod(th[m], np.pi))))
    bg = oriented_filter(Spre, m, thc, 0.60 * MM, 0.08 * MM)
    f["or_a0.08_l0.60_const"] = nconv(Spre - bg, m, INT)
    sd = {}
    for k, (sl, sa) in {"acr": (0.05, 0.30), "alo": (0.30, 0.05), "iso": (0.15, 0.15),
                        "acr2": (0.05, 0.60), "alo2": (0.60, 0.05), "iso2": (0.25, 0.25)}.items():
        sd[k] = oriented_filter(Spre, m, th, sl * MM, sa * MM, mode="std")
        f[f"std_{k}"] = nconv(sd[k], m, INT)
    f["std_ratio"] = nconv(sd["acr"] / np.maximum(sd["alo"], 1e-3), m, INT)
    f["std_ratio2"] = nconv(sd["acr2"] / np.maximum(sd["alo2"], 1e-3), m, INT)
    f["coh"] = nconv(coh, m, INT)
    lvl = oriented_filter(Spre, m, th, 1.0 * MM, 0.05 * MM) + 6.0
    f["cv_acr"] = nconv(sd["acr"] / np.maximum(lvl, 0.5), m, INT)
    for sl in ("0.6", "2.4"):
        bgl = oriented_filter(Spre, m, th, float(sl) * MM, 0.05 * MM) + 6.0
        f[f"ratio_l{sl}"] = nconv((Spre + 6.0) / np.maximum(bgl, 0.5), m, INT)
    # oriented white top-hat: the background is the along-fibre LOWER ENVELOPE (robust to bright ink)
    for l in ("0.60", "1.20", "2.40"):
        for w in ("0.04", "0.15"):
            op = oriented_morph(Spre, m, th, float(l) * MM, float(w) * MM)
            f[f"tophat_l{l}_w{w}"] = nconv(Spre - op, m, INT)
    op = oriented_morph(Spre, m, th + np.pi / 2, 1.20 * MM, 0.15 * MM)
    f["tophat_l1.20_w0.15_perp"] = nconv(Spre - op, m, INT)
    op = oriented_morph(Spre, m, thc, 1.20 * MM, 0.15 * MM)
    f["tophat_l1.20_w0.15_const"] = nconv(Spre - op, m, INT)
    r = max(3, int(round(1.20 * MM / 2)))
    kk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    opi = cv2.morphologyEx(fill_holes(Spre, m, 6.0), cv2.MORPH_OPEN, kk, borderType=cv2.BORDER_REPLICATE)
    f["tophat_iso_1.20"] = nconv(Spre - opi, m, INT)

    sel = m & (y != -1)
    pos = (y == 1)[sel]
    np.savez_compressed(p, sel=sel, pos=pos, **{k: v[sel].astype(np.float32) for k, v in f.items()})
    return {k: v[sel].astype(np.float32) for k, v in f.items()}, sel, pos


def fit_logistic(X, yb, w, l2=10.0, iters=60):
    n, d = X.shape
    Xa = np.hstack([X, np.ones((n, 1), np.float32)])
    b = np.zeros(d + 1)
    yv = yb.astype(np.float64)
    for _ in range(iters):
        z = Xa @ b
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
        g = Xa.T @ (w * (p - yv)) + l2 * np.r_[b[:-1], 0.0]
        s = w * p * (1 - p)
        H = (Xa * s[:, None]).T @ Xa + l2 * np.diag(np.r_[np.ones(d), 0.0])
        step = np.linalg.solve(H + 1e-6 * np.eye(d + 1), g)
        b -= step
        if np.abs(step).max() < 1e-8:
            break
    return b


def auc_v(s, pos):
    return auc(s, pos, ~pos)


if __name__ == "__main__":
    data = {}
    for seg, crop in TRAIN_CROPS:
        f, sel, pos = build(seg, crop)
        data[(seg, crop)] = (f, pos)
        print("built", seg, crop, int(pos.sum()), int((~pos).sum()), flush=True)
    keys = ISO_KEYS + FIB_KEYS
    single = {k: {f"{s}/{c}": round(auc_v(data[(s, c)][0][k], data[(s, c)][1]), 4) for s, c in TRAIN_CROPS}
              for k in keys}
    for k in keys:
        single[k]["MEAN"] = round(float(np.mean([v for kk, v in single[k].items()])), 4)
    print("\n== E4 single-feature TRAIN mean AUC (sorted by |AUC-0.5|)")
    for k in sorted(keys, key=lambda k: -abs(single[k]["MEAN"] - 0.5)):
        print(f"  {single[k]['MEAN']:.4f}  {k}")

    def loco(bank_keys):
        out = []
        for held in TRAIN_CROPS:
            Xs, ys, ws = [], [], []
            for s, c in TRAIN_CROPS:
                if (s, c) == held:
                    continue
                f, pos = data[(s, c)]
                X = np.stack([f[k] for k in bank_keys], 1)
                X = (X - X.mean(0)) / (X.std(0) + 1e-6)
                w = np.where(pos, 1.0 / max(pos.sum(), 1), 1.0 / max((~pos).sum(), 1))
                Xs.append(X); ys.append(pos); ws.append(w)
            Xa = np.concatenate(Xs); ya = np.concatenate(ys); wa = np.concatenate(ws)
            b = fit_logistic(Xa, ya, wa)
            f, pos = data[held]
            Xh = np.stack([f[k] for k in bank_keys], 1)
            Xh = (Xh - Xh.mean(0)) / (Xh.std(0) + 1e-6)
            out.append(auc_v(Xh @ b[:-1], pos))
        return out

    res = {"single": single}
    for name, kk in [("ISO", ISO_KEYS), ("FIB", FIB_KEYS), ("ISO+FIB", ISO_KEYS + FIB_KEYS)]:
        a = loco(kk)
        res[name] = {"loco": [round(v, 4) for v in a], "mean": round(float(np.mean(a)), 4)}
        print(f"\nLOCO {name}: mean {np.mean(a):.4f}  " + " ".join(f"{v:.3f}" for v in a))
    json.dump(res, open(os.path.join(ROOT, "stats/explore/fb_e45.json"), "w"), indent=1)
