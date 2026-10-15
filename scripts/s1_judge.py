"""GATE-S1 judge: pixel AUC and letter AUC of a score map against the registered GP label. Also writes cls_text/cls_blank for the crop."""
import sys, os, json, numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, label as cclabel, zoom, distance_transform_edt
from scipy.stats import rankdata
Image.MAX_IMAGE_PIXELS = None
d, crops_p, name, lab_p, tag, pitch = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], float(sys.argv[6])
C = json.load(open(crops_p)); c = [x for x in C["crops"] if x["name"] == name][0]; reg = C["registration"]; S = reg["scale_label_to_canvas"]
y0, x0, side = c["y0"], c["x0"], c["side"]
if not os.path.exists(os.path.join(d, "cls_text.npy")):
    lab = np.asarray(Image.open(lab_p).convert("L")) > 127
    # canvas px (y,x) -> label px ((y - oy)/S, (x - ox)/S); sample nearest
    lo = c.get("local_offset", [0, 0])
    ys = ((np.arange(y0, y0 + side) - reg["offset_canvas_y"] - lo[0]) / S).round().astype(int); xs = ((np.arange(x0, x0 + side) - reg["offset_canvas_x"] - lo[1]) / S).round().astype(int)
    ok_y = (ys >= 0) & (ys < lab.shape[0]); ok_x = (xs >= 0) & (xs < lab.shape[1])
    L = np.zeros((side, side), bool); L[np.ix_(ok_y, ok_x)] = lab[np.ix_(ys[ok_y], xs[ok_x])]
    m = (np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0)
    dist = distance_transform_edt(~L) * pitch / 1000.0  # mm to nearest label
    r = int(round(5000 / pitch)); zone = binary_dilation(L, iterations=1, structure=np.ones((3, 3)))  # zone via distance: within 5 mm of label
    zone = dist <= 5.0
    text = L & m; blank = (~L) & (dist >= 0.3) & zone & m
    if len(sys.argv) > 7:   # training-segment veto: blank also requires team ds8 prediction < thr (RULES.md)
        from scipy.ndimage import zoom as _zoom
        ink = np.asarray(Image.open(sys.argv[7]).convert("L")).astype(np.float32) / 255.0; thr = float(sys.argv[8])
        sub = ink[y0 // 8:(y0 + side) // 8 + 1, x0 // 8:(x0 + side) // 8 + 1]; up = _zoom(sub, 8, order=1)[:side, :side]
        v = np.zeros((side, side), np.float32); v[:up.shape[0], :up.shape[1]] = up
        base = blank
        q = float(np.percentile(v[base], 100.0 * thr)) if base.any() else 0.0   # thr is now a QUANTILE (RULES.md, incident 3)
        blank = base & (v <= q)
        print("veto: quantile", thr, "-> team value", round(q, 4), "blank px", int(blank.sum()), "of", int(base.sum()))
        print("veto applied: blank px", int(blank.sum()))
    np.save(os.path.join(d, "cls_text.npy"), text); np.save(os.path.join(d, "cls_blank.npy"), blank); np.save(os.path.join(d, "label.npy"), L)
text = np.load(os.path.join(d, "cls_text.npy")); blank = np.load(os.path.join(d, "cls_blank.npy")); L = np.load(os.path.join(d, "label.npy"))
rng = np.random.default_rng(0); sub = rng.random(text.shape) < 0.05
def auc(x):
    a, b = x[text & sub], x[blank & sub]; rk = rankdata(np.concatenate([a, b])); n1, n0 = len(a), len(b)
    return float((rk[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)) if n1 and n0 else None
res = {"tag": tag, "crop": name, "text_px": int(text.sum()), "blank_px": int(blank.sum())}
lab_cc, n = cclabel(L); sizes = np.bincount(lab_cc.ravel()); min_px = (0.5 / pitch * 1000) ** 2 * 1  # 0.5 mm^2 = (707 um)^2
min_px = 0.5e6 / (pitch * pitch)
letters = [i for i in range(1, n + 1) if sizes[i] >= min_px]
by, bx = np.where(blank)
for f in ("top", "bot"):
    p = os.path.join(d, f"s_{f}_{tag}.npy")
    if not os.path.exists(p): continue
    s = np.load(p).astype(np.float32); res[f] = {"auc_px": auc(s)}
    wins = 0; tot = 0
    for i in letters:
        yy, xx = np.where(lab_cc == i); mm = text[yy, xx]
        if mm.sum() < 0.5 * len(yy): continue
        ms = s[yy[mm], xx[mm]].mean(); rad = int(np.sqrt(mm.sum() / np.pi))
        for _ in range(200):
            j = rng.integers(len(by)); cy, cx = by[j], bx[j]
            ys, xs = slice(max(cy - rad, 0), cy + rad + 1), slice(max(cx - rad, 0), cx + rad + 1)
            bm = blank[ys, xs]
            if bm.sum() < 0.5 * np.pi * rad * rad: continue
            tot += 1; wins += float(s[ys, xs][bm].mean() < ms)
    res[f]["auc_letter"] = wins / tot if tot else None; res[f]["n_letters"] = len(letters)
    print(f, res[f], flush=True)
json.dump(res, open(os.path.join(d, f"judge_{tag}.json"), "w"), indent=1)
