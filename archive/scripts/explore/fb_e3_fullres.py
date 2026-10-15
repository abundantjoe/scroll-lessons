"""E3: WHY did v0.1b's oriented papyrus subtraction fail? Run at the resolution it ran at
(2.4 um/px) on the one crop we are allowed to fit on, 20231005123336/train, using the surviving
full-resolution face image proj_bot_v1a.npy (the v1b depth projection of the bottom face).
Sweeps the orientation scale and the window scales around v0.1b's fixed (sigma_tensor 6 px,
1.0 mm along / 1.5 px across) and compares against the isotropic background of the same area."""
import os, sys, json, itertools, numpy as np, cv2, gc
sys.path.insert(0, os.path.dirname(__file__))
from fb_lib import auc, ROOT, cdir, _sep

PITCH = 2.4
MM = 1000.0 / PITCH
SEG, CROP = "20231005123336", "train"
N = 4096                       # central NxN window (~1 cm^2) to stay inside the memory budget

def gblur(x, s):
    """gaussian blur; for sigma >= 8 px, three box passes of the same variance (O(1) per pixel)."""
    if s <= 0: return x.copy()
    if s < 8:
        k = int(6 * s) | 1
        return cv2.GaussianBlur(x, (k, k), sigmaX=s, sigmaY=s, borderType=cv2.BORDER_REPLICATE)
    L = int(round(np.sqrt(4 * s * s + 1))) | 1
    o = np.ascontiguousarray(x, dtype=np.float32)
    for _ in range(3):
        o = cv2.boxFilter(o, -1, (L, L), normalize=True, borderType=cv2.BORDER_REPLICATE)
    return o

def nconv(x, mf, s):
    return gblur(x * mf, s) / np.maximum(gblur(mf, s), 1e-3)

def orientation(S, mf, sg, st):
    g = gblur(S * mf, sg) / np.maximum(gblur(mf, sg), 1e-3)
    g = (g * mf).astype(np.float32)
    gy, gx = np.gradient(g); del g
    gy *= mf; gx *= mf
    Jxx = gblur(gx * gx, st); Jyy = gblur(gy * gy, st); Jxy = gblur(gx * gy, st)
    del gx, gy; gc.collect()
    th = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy) + np.pi / 2
    coh = np.sqrt((Jxx - Jyy) ** 2 + 4 * Jxy ** 2) / np.maximum(Jxx + Jyy, 1e-12)
    del Jxx, Jyy, Jxy; gc.collect()
    return th.astype(np.float32), coh.astype(np.float32)

def oriented(S, mf, th, sig_along, sig_across, n_orient=12, mode="mean"):
    H, W = S.shape
    bins = np.round((np.mod(th, np.pi) / np.pi) * n_orient).astype(np.int32) % n_orient
    out = np.zeros_like(S)
    D = int(np.ceil(np.hypot(H, W))) + 2
    cx, cy = W / 2.0, H / 2.0
    Sm = (S * mf).astype(np.float32)
    S2 = (S * S * mf).astype(np.float32) if mode == "std" else None
    for b in range(n_orient):
        sel = bins == b
        if not sel.any(): continue
        ang = b * 180.0 / n_orient
        M = cv2.getRotationMatrix2D((cx, cy), ang, 1.0); M[0, 2] += D / 2 - cx; M[1, 2] += D / 2 - cy
        rs = cv2.warpAffine(Sm, M, (D, D), flags=cv2.INTER_LINEAR, borderValue=0)
        rm = cv2.warpAffine(mf, M, (D, D), flags=cv2.INTER_LINEAR, borderValue=0)
        num = _sep(rs, sig_along, sig_across); den = _sep(rm, sig_along, sig_across)
        bg = num / np.maximum(den, 1e-3); del rs, num
        if mode == "std":
            r2 = cv2.warpAffine(S2, M, (D, D), flags=cv2.INTER_LINEAR, borderValue=0)
            n2 = _sep(r2, sig_along, sig_across)
            bg = np.sqrt(np.maximum(n2 / np.maximum(den, 1e-3) - bg * bg, 0.0)); del r2, n2
        del rm, den
        Mi = cv2.invertAffineTransform(M)
        back = cv2.warpAffine(bg, Mi, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        out[sel] = back[sel]; del bg, back
        gc.collect()
    del Sm
    return out

d = cdir(SEG, CROP)
def sub(a):
    H, W = a.shape; y0 = (H - N) // 2; x0 = (W - N) // 2
    return np.ascontiguousarray(a[y0:y0 + N, x0:x0 + N])

S = sub(np.load(os.path.join(d, "proj_bot_v1a.npy")).astype(np.float32))
St = sub(np.load(os.path.join(d, "proj_top_v1a.npy")).astype(np.float32))
m = sub(np.load(os.path.join(d, "mask_top.npy"))) & sub(np.load(os.path.join(d, "mask_bot.npy")))
txt = sub(np.load(os.path.join(d, "cls_text.npy"))) & m
blk = sub(np.load(os.path.join(d, "cls_blank.npy"))) & m
mf = m.astype(np.float32)
med = np.median(S[m]); mad = np.median(np.abs(S[m] - med)) * 1.4826
S = ((S - med) / mad).astype(np.float32) * mf
med = np.median(St[m]); mad = np.median(np.abs(St[m] - med)) * 1.4826
St = ((St - med) / mad).astype(np.float32) * mf
print("window", S.shape, "mask %.3f" % m.mean(), "text", int(txt.sum()), "blank", int(blk.sum()), flush=True)

out = {"window_px": N, "pitch_um": PITCH, "n_text": int(txt.sum()), "n_blank": int(blk.sum())}

Spre = nconv(S, mf, 0.01 * MM).astype(np.float32) * mf

if __name__ == "__main__":
    # --- (1) the orientation field at 2.4 um: coherence and top/bottom-face agreement ---
    for st in (2, 6, 12, 25, 50, 100):
        th, coh = orientation(S, mf, 1.0, st)
        tht, _ = orientation(St, mf, 1.0, st)
        dd = np.mod(th - tht, np.pi); dd = np.minimum(dd, np.pi - dd)
        thm = np.mod(th[m], np.pi)
        c2 = np.cos(2 * thm).mean(); s2 = np.sin(2 * thm).mean()
        out[f"st{st}"] = dict(coh_med=round(float(np.median(coh[m])), 4),
                              R_global=round(float(np.hypot(c2, s2)), 4),
                              theta_global_deg=round(float(np.rad2deg(0.5 * np.arctan2(s2, c2)) % 180), 1),
                              topbot_med_absdiff_deg=round(float(np.rad2deg(np.median(dd[m]))), 1),
                              topbot_frac_within20deg=round(float((np.rad2deg(dd[m]) < 20).mean()), 3))
        print(f"st{st}", out[f"st{st}"], flush=True)
        del th, coh, tht, dd; gc.collect()
    del St; gc.collect()

    # --- (2) AUC of oriented vs isotropic background removal at 2.4 um ---
    SIG_PRE = 0.01 * MM            # ~4 px, suppresses the per-voxel noise only
    Spre = nconv(S, mf, SIG_PRE).astype(np.float32) * mf
    INT = [0.0, 0.10 * MM, 0.25 * MM]
    res = {}
    def add(name, r):
        for lab, si in zip(["raw", "0.10", "0.25"], INT):
            f = nconv(r, mf, si) if si > 0 else r
            res[f"{name}|int{lab}"] = round(auc(f, txt, blk), 4)
        print(name, {k: v for k, v in res.items() if k.startswith(name + "|")}, flush=True)

    add("plain", Spre)
    for sb in (0.25, 0.5, 1.0, 2.0):
        add(f"iso|bg{sb}", Spre - nconv(Spre, mf, sb * MM))
    # v0.1b exactly: sigma_tensor 6 px, 1.0 mm along, 1.5 px across (on this face image)
    for st in (6, 25, 100):
        th, _ = orientation(S, mf, 1.0, st)
        for sa_px, sl_mm in [(1.5, 1.0), (1.5, 0.25), (6.0, 1.0), (6.0, 0.25), (20.0, 1.0), (20.0, 0.5), (50.0, 2.0)]:
            bg = oriented(Spre, mf, th, sl_mm * MM, sa_px)
            add(f"or{st}|a{sa_px}px|l{sl_mm}mm", Spre - bg)
            del bg; gc.collect()
        if st == 25:
            for sa_px, sl_mm in [(6.0, 1.0), (20.0, 1.0)]:
                bg = oriented(Spre, mf, th + np.pi / 2, sl_mm * MM, sa_px)
                add(f"perp{st}|a{sa_px}px|l{sl_mm}mm", Spre - bg); del bg
                se = np.sqrt(sa_px * sl_mm * MM)
                add(f"isoarea|a{sa_px}px|l{sl_mm}mm", Spre - nconv(Spre, mf, se))
                gc.collect()
        del th; gc.collect()
    out["auc"] = res
    json.dump(out, open(os.path.join(ROOT, "stats/explore/fb_e3_fullres.json"), "w"), indent=1)
    print("\ntop:")
    for k, v in sorted(res.items(), key=lambda t: -t[1])[:15]:
        print(f"  {v:.4f} {k}")
