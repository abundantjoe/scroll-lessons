#!/usr/bin/env python3
"""GATE judge (6.2/6.3): per-crop pixel AUC of s_face vs the text reference, per-term AUCs, row test (5.6),
0.5/1/2 cm^2 unit statistics for the rule derivation (6.4). Records every crop; nothing is selected.
usage: gate_eval.py eval <derived_dir> <crop.json-name> <crops.json> <pitch> <ref.tif> <labels.zarr|none> <label_scale> <label_slice> <excl_px> <tag>
       gate_eval.py summary <tag> <out.json> <derived_dir> [...]"""
import sys, os, json, numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter1d
from sklearn.metrics import roc_auc_score
TEXT_T, BLANK_T = 0.40, 0.25; UNIT_TEXT_MIN, UNIT_BLANK_MAXTEXT, UNIT_BLANK_MINBLANK = 0.30, 0.05, 0.50
ROW_BAND_MM = (2.0, 4.0); ROW_PEAK_ON, ROW_PEAK_OFF, ROW_CT_MAX = 0.25, 0.15, 0.25

def autocorr(prof):
    p = prof - prof.mean(); n = len(p)
    ac = np.correlate(p, p, "full")[n - 1:]; return ac / max(ac[0], 1e-9)

def row_test(s, mask, ct, pitch):
    """row-mean profile along v (image rows) over masked pixels; first local max of the autocorrelation in the 2-4 mm band."""
    w = mask.sum(1); prof = np.where(w > 0, (s * mask).sum(1) / np.maximum(w, 1), 0.0)
    prof = gaussian_filter1d(prof, 0.1 * 1000 / pitch)             # 0.1 mm smoothing of the profile (fixed)
    ac = autocorr(prof[w > 0.2 * w.max()]) if (w > 0).any() else np.zeros(2)
    lo, hi = int(ROW_BAND_MM[0] * 1000 / pitch), int(ROW_BAND_MM[1] * 1000 / pitch)
    res = dict(peak=0.0, lag_mm=None)
    if len(ac) > hi + 1:
        seg = ac[lo:hi]
        for i in range(1, len(seg) - 1):
            if seg[i] >= seg[i - 1] and seg[i] >= seg[i + 1]:
                res = dict(peak=float(seg[i]), lag_mm=float((lo + i) * pitch / 1000)); break
        res["max_in_band"] = float(seg.max()); res["lag_max_mm"] = float((lo + int(seg.argmax())) * pitch / 1000)
    # CT fibre-banding control at the same lag
    cw = (ct > 0).sum(1); cprof = np.where(cw > 0, (ct * (ct > 0)).sum(1) / np.maximum(cw, 1), 0.0)
    cac = autocorr(gaussian_filter1d(cprof[cw > 0.2 * cw.max()], 0.1 * 1000 / pitch)) if (cw > 0).any() else np.zeros(2)
    if res["lag_mm"] is not None:
        lag = int(res["lag_mm"] * 1000 / pitch); res["ct_ac_at_lag"] = float(cac[lag]) if lag < len(cac) else None
    return res

def auc(x, pos, neg, rng, nmax=4_000_000):
    ip = np.flatnonzero(pos); ineg = np.flatnonzero(neg)
    if len(ip) < 1000 or len(ineg) < 1000: return None
    ip = rng.choice(ip, min(len(ip), nmax), replace=False); ineg = rng.choice(ineg, min(len(ineg), nmax), replace=False)
    xf = x.ravel(); return float(roc_auc_score(np.r_[np.ones(len(ip)), np.zeros(len(ineg))], np.r_[xf[ip], xf[ineg]]))

def units(s_face, s_other, mask, text, blank, side):
    H, W = s_face.shape; out = []
    for i in range(H // side):
        for j in range(W // side):
            sl = (slice(i * side, (i + 1) * side), slice(j * side, (j + 1) * side)); m = mask[sl]
            if m.mean() < 0.5: continue
            tf = text[sl][m].mean(); bf = blank[sl][m].mean()
            cls = "text" if tf >= UNIT_TEXT_MIN else ("blank" if (tf <= UNIT_BLANK_MAXTEXT and bf >= UNIT_BLANK_MINBLANK) else "other")
            out.append(dict(i=i, j=j, cls=cls, text_frac=float(tf), blank_frac=float(bf), valid_frac=float(m.mean()),
                            mean_s=float(s_face[sl][m].mean()), mean_diff=float((s_face[sl] - s_other[sl])[m].mean())))
    return out

def evaluate(d, name, crops, pitch, ref_path, labels, lscale, lslice, excl, tag):
    import tifffile, zarr
    rng = np.random.default_rng(0)
    c = [c for c in json.load(open(crops))["crops"] if c["name"] == name][0]; y0, x0 = c["y0"], c["x0"]; hh, ww = c.get("h", c["side"]), c.get("w", c["side"])
    full = np.load(ref_path) if ref_path.endswith(".npy") else tifffile.imread(ref_path)
    ref = full[y0:y0 + hh, x0:x0 + ww].astype(np.float32) / 255.0
    excl_mask = np.zeros(ref.shape, bool)
    if labels != "none":
        L = zarr.open(labels, mode="r"); arr = L[list(L.array_keys())[0]] if hasattr(L, "array_keys") and list(L.array_keys()) else L
        lab = np.asarray(arr[lslice]) > 0
        lab_d = distance_transform_edt(~lab) <= excl / lscale
        ys, xs = np.arange(y0, y0 + hh) // lscale, np.arange(x0, x0 + ww) // lscale
        excl_mask = lab_d[np.ix_(np.clip(ys, 0, lab.shape[0] - 1), np.clip(xs, 0, lab.shape[1] - 1))]
    res = dict(crop=c, tag=tag, pitch=pitch, excluded_fraction=float(excl_mask.mean()))
    ct = np.load(os.path.join(d, "ct_mid.npy")).astype(np.float32); faces = {}
    S = {f: np.load(os.path.join(d, f"s_{f}_{tag}.npy")).astype(np.float32) for f in ("top", "bot")}
    M = {f: np.load(os.path.join(d, f"mask_{f}.npy")) & ~excl_mask for f in ("top", "bot")}
    for f, o in (("top", "bot"), ("bot", "top")):
        m = M[f]; text = (ref >= TEXT_T) & m; blank = (ref <= BLANK_T) & m
        r = dict(mask_fraction=float(m.mean()), text_px=int(text.sum()), blank_px=int(blank.sum()),
                 auc=auc(S[f], text, blank, rng), row=row_test(S[f], m, ct, pitch))
        for term in ("relief", "e", "a"):
            p = os.path.join(d, f"{term}_{f}.npy")
            if os.path.exists(p): r[f"auc_{term}"] = auc(np.load(p).astype(np.float32), text, blank, rng)
        for cm2, nm in ((0.5, "u05"), (1.0, "u1"), (2.0, "u2")):
            us = int(round(np.sqrt(cm2) * 10000 / pitch)); r[nm] = units(S[f], S[o], m, ref >= TEXT_T, ref <= BLANK_T, us)
        faces[f] = r
    res["faces"] = faces
    res["writing_face"] = max(("top", "bot"), key=lambda f: faces[f]["row"]["peak"])
    json.dump(res, open(os.path.join(d, f"gate_{tag}.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "faces"}, indent=1)); 
    for f in faces: print(f, {k: v for k, v in faces[f].items() if not k.startswith("u")})

def summary(tag, out, dirs):
    R = [json.load(open(os.path.join(d, f"gate_{tag}.json"))) for d in dirs]
    text_crops = [r for r in R if r["crop"]["kind"] == "text"]
    aucs = [r["faces"][r["writing_face"]]["auc"] for r in text_crops]
    S = dict(tag=tag, crops=[dict(name=r["crop"]["name"], kind=r["crop"]["kind"], writing_face=r["writing_face"],
             auc_top=r["faces"]["top"]["auc"], auc_bot=r["faces"]["bot"]["auc"], row_top=r["faces"]["top"]["row"], row_bot=r["faces"]["bot"]["row"],
             terms={f: {k: v for k, v in r["faces"][f].items() if k.startswith("auc_")} for f in ("top", "bot")}) for r in R])
    S["mean_auc_text_crops_writing_face"] = float(np.mean([a for a in aucs if a is not None])) if any(a is not None for a in aucs) else None
    # rule 6.4 derivation on writing-face units of ALL crops (text units vs blank units)
    for nm in ("u05", "u1", "u2"):
        T = []; Bk = []
        for r in R:
            f = r["writing_face"]
            for u in r["faces"][f][nm]:
                (T if u["cls"] == "text" else Bk if u["cls"] == "blank" else []).append(u)
        if T and Bk:
            tau = 0.5 * (np.mean([u["mean_s"] for u in T]) + np.mean([u["mean_s"] for u in Bk]))
            Mg = 0.5 * (np.mean([u["mean_diff"] for u in T]) + np.mean([u["mean_diff"] for u in Bk]))
            flag = lambda u: u["mean_s"] >= tau and u["mean_diff"] >= Mg
            S[nm] = dict(n_text=len(T), n_blank=len(Bk), tau=float(tau), M=float(Mg),
                         text_mean_s=float(np.mean([u["mean_s"] for u in T])), blank_mean_s=float(np.mean([u["mean_s"] for u in Bk])),
                         text_mean_diff=float(np.mean([u["mean_diff"] for u in T])), blank_mean_diff=float(np.mean([u["mean_diff"] for u in Bk])),
                         hit_text=float(np.mean([flag(u) for u in T])), hit_blank=float(np.mean([flag(u) for u in Bk])))
        else: S[nm] = dict(n_text=len(T), n_blank=len(Bk))
    json.dump(S, open(out, "w"), indent=1); print(json.dumps(S, indent=1))

if __name__ == "__main__":
    if sys.argv[1] == "eval":
        d, name, crops, pitch, ref, labels, lscale, lslice, excl, tag = sys.argv[2:12]
        evaluate(d, name, crops, float(pitch), ref, labels, int(lscale), int(lslice), int(excl), tag)
    else: summary(sys.argv[2], sys.argv[3], sys.argv[4:])
