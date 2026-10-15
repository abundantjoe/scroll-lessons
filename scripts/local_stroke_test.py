"""Local stroke test L (RULES.md): ink disks vs blank disks within 1.5 mm, paired. Cancels any contrast varying above ~2 mm."""
import sys, os, json, numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

def local_stroke(score, label, mask, pitch_um=2.4, r_mm=0.25, blank_mm=0.5, near_mm=1.5, max_ink=1500, seed=0):
    r = int(round(r_mm * 1000 / pitch_um)); near_px = near_mm * 1000 / pitch_um
    yy, xx = np.ogrid[-r:r + 1, -r:r + 1]; disk = (yy * yy + xx * xx) <= r * r; need = 0.5 * disk.sum()
    din = distance_transform_edt(label) * pitch_um / 1000.0
    dout = distance_transform_edt(~label) * pitch_um / 1000.0
    g = np.zeros(label.shape, bool); g[r:-r:r, r:-r:r] = True
    rng = np.random.default_rng(seed)
    def collect(cs, cap):
        out_c, out_v = [], []
        if len(cs) > cap * 4: cs = cs[rng.choice(len(cs), cap * 4, replace=False)]
        for y, x in cs:
            m = mask[y - r:y + r + 1, x - r:x + r + 1] & disk
            if m.sum() < need: continue
            out_c.append((y, x)); out_v.append(float(score[y - r:y + r + 1, x - r:x + r + 1][m].mean()))
            if len(out_c) >= cap: break
        return np.array(out_c, float).reshape(-1, 2), np.array(out_v)
    ic, iv = collect(np.argwhere(g & (din >= r_mm)), max_ink)
    bc, bv = collect(np.argwhere(g & (dout >= blank_mm)), 6000)
    if len(ic) < 20 or len(bc) < 20: return None, 0, 0, 0
    tree = cKDTree(bc); wins = tot = 0.0; used = 0
    for i in range(len(ic)):
        nb = tree.query_ball_point(ic[i], near_px)
        if not nb: continue
        used += 1
        v = bv[nb]; w = float((iv[i] > v).sum() + 0.5 * (iv[i] == v).sum()) / len(v)
        wins += w; tot += 1
    return (wins / tot if tot else None), len(ic), len(bc), used

if __name__ == "__main__":
    outp = "stats/local_stroke_test.json"; out = json.load(open(outp)) if os.path.exists(outp) else {}
    for spec in sys.argv[1:]:
        seg, crop = spec.split(":")
        d = f"data/s1/{seg}/derived/{crop}"
        if not os.path.exists(os.path.join(d, "label.npy")): print("skip", spec); continue
        label = np.load(os.path.join(d, "label.npy"))
        mask = (np.load(os.path.join(d, "mask_top.npy")) > 0) & (np.load(os.path.join(d, "mask_bot.npy")) > 0)
        out.setdefault(spec, {})
        for tag in ("v0.1b", "v1b", "v2", "v3", "v5", "v6", "v6b", "v6c", "v7", "v8", "gpr1", "gpr2", "e", "team"):
            p = os.path.join(d, f"s_bot_{tag}.npy")
            if not os.path.exists(p) or tag in out[spec]: continue
            L, ni, nb, used = local_stroke(np.load(p).astype(np.float32), label, mask)
            out[spec][tag] = {"L": (round(L, 4) if L is not None else None), "n_ink": ni, "n_blank": nb, "n_paired": used}
            print(spec, tag, out[spec][tag], flush=True)
        json.dump(out, open(outp, "w"), indent=1)
