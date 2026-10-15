"""Stroke test (RULES.md): AUC of mean score over 0.25 mm DISKS inside strokes vs disks in blank. Applied to every method alike.
Disk means are computed exactly, at the sampled centres only."""
import sys, os, json, numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata

def stroke_auc(score, label, mask, pitch_um=2.4, r_mm=0.25, blank_mm=0.5, max_n=2000, seed=0):
    r = int(round(r_mm * 1000 / pitch_um))
    yy, xx = np.ogrid[-r:r + 1, -r:r + 1]; disk = (yy * yy + xx * xx) <= r * r
    din = distance_transform_edt(label) * pitch_um / 1000.0
    dout = distance_transform_edt(~label) * pitch_um / 1000.0
    g = np.zeros(label.shape, bool); g[r:-r:r, r:-r:r] = True          # centres on a 0.25 mm grid, r away from the border
    ink_c = np.argwhere(g & (din >= r_mm)); blk_c = np.argwhere(g & (dout >= blank_mm))
    rng = np.random.default_rng(seed)
    def means(cs):
        if len(cs) > 4 * max_n: cs = cs[rng.choice(len(cs), 4 * max_n, replace=False)]
        vals = []
        for y, x in cs:
            m = mask[y - r:y + r + 1, x - r:x + r + 1] & disk
            if m.sum() < 0.5 * disk.sum(): continue
            vals.append(float(score[y - r:y + r + 1, x - r:x + r + 1][m].mean()))
            if len(vals) >= max_n: break
        return np.array(vals)
    a, c = means(ink_c), means(blk_c)
    if len(a) < 20 or len(c) < 20: return None, len(a), len(c)
    rk = rankdata(np.concatenate([a, c])); n1, n0 = len(a), len(c)
    return float((rk[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)), n1, n0

if __name__ == "__main__":
    outp = "stats/stroke_test.json"; out = json.load(open(outp)) if os.path.exists(outp) else {}
    for spec in sys.argv[1:]:
        seg, crop = spec.split(":")
        d = f"data/s1/{seg}/derived/{crop}"
        if not os.path.exists(os.path.join(d, "label.npy")): print("skip", spec); continue
        label = np.load(os.path.join(d, "label.npy"))
        mask = (np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0)
        out.setdefault(spec, {})
        for tag in ("v0.1b", "v1a", "v1b", "v2", "v3", "v5", "v6", "v6b", "v6c", "v7", "v8", "gpr1", "gpr2", "e", "v0.3p", "team"):
            p = os.path.join(d, f"s_bot_{tag}.npy")
            if not os.path.exists(p) or tag in out[spec]: continue
            a, n1, n0 = stroke_auc(np.load(p).astype(np.float32), label, mask)
            out[spec][tag] = {"stroke_auc": (round(a, 4) if a is not None else None), "n_ink": n1, "n_blank": n0}
            print(spec, tag, out[spec][tag], flush=True)
        json.dump(out, open(outp, "w"), indent=1)
