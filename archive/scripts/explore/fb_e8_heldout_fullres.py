"""E8 -- DECLARED BEFORE RUNNING. The same four measures as E7 but at the native 2.4 um pitch,
where the papyrus fibre texture is actually resolved, on the whole of each crop.
Base: proj_bot_v1a.npy (the existing v1b bottom-face depth projection), MAD-standardised in the mask.
Spre = G_0.01mm(base); theta_crop = circular mean of the structure-tensor direction
(sigma_grad 1 px, sigma_tensor 128 px = 307 um, the same physical scale as the E7 rule) over the MASK.
  A FIB-theta : bg = anisotropic mean, sigma_along 3.0 mm along theta_crop, sigma_across 0.12 mm
  B ANI-90    : the same with the direction fixed at 90 deg
  C ISO-3.0   : isotropic 3.0 mm background
  D PLAIN     : no background removal
score = G_0.40mm(residual). Pixel AUC against cls_text / cls_blank inside mask_top & mask_bot -- the
judge's own pixel-AUC definition. v0.1b / v1b / v2 / v3 / team are scored on exactly the same pixels.
Both protocols (E7 at 19.2 um and E8 at 2.4 um) are reported whatever they show; neither is selected
after the fact."""
import os, sys, json, numpy as np, gc
sys.path.insert(0, os.path.dirname(__file__))
from fb_lib import auc, ROOT, cdir, EVAL_CROPS, _sep
import cv2

PITCH = 2.4; MM = 1000.0 / PITCH

def gblur(x, s):
    if s <= 0: return x
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

def theta_global(S, mf, m, st):
    g = (nconv(S, mf, 1.0) * mf).astype(np.float32)
    gy, gx = np.gradient(g); del g
    gy *= mf; gx *= mf
    Jxx = gblur(gx * gx, st); Jyy = gblur(gy * gy, st); Jxy = gblur(gx * gy, st)
    del gx, gy; gc.collect()
    th = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy) + np.pi / 2
    del Jxx, Jyy, Jxy; gc.collect()
    t = np.mod(th[m], np.pi); del th; gc.collect()
    return float(np.mod(np.arctan2(np.sin(2 * t).mean(), np.cos(2 * t).mean()) / 2, np.pi))

def aniso_bg(S, mf, ang, sig_along, sig_across):
    H, W = S.shape
    D = int(np.ceil(np.hypot(H, W))) + 2
    cx, cy = W / 2.0, H / 2.0
    M = cv2.getRotationMatrix2D((cx, cy), np.rad2deg(ang), 1.0)
    M[0, 2] += D / 2 - cx; M[1, 2] += D / 2 - cy
    rs = cv2.warpAffine((S * mf).astype(np.float32), M, (D, D), flags=cv2.INTER_LINEAR, borderValue=0)
    rm = cv2.warpAffine(mf, M, (D, D), flags=cv2.INTER_LINEAR, borderValue=0)
    num = _sep(rs, sig_along, sig_across); del rs
    den = _sep(rm, sig_along, sig_across); del rm
    bg = num / np.maximum(den, 1e-3); del num, den; gc.collect()
    Mi = cv2.invertAffineTransform(M)
    out = cv2.warpAffine(bg, Mi, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    del bg; gc.collect()
    return out

res = {}
for seg, crop in EVAL_CROPS:
    d = cdir(seg, crop)
    S = np.load(os.path.join(d, "proj_bot_v1a.npy")).astype(np.float32)
    m = np.load(os.path.join(d, "mask_top.npy")) & np.load(os.path.join(d, "mask_bot.npy"))
    txt = np.load(os.path.join(d, "cls_text.npy")) & m
    blk = np.load(os.path.join(d, "cls_blank.npy")) & m
    mf = m.astype(np.float32)
    med = np.median(S[m]); mad = np.median(np.abs(S[m] - med)) * 1.4826
    S = ((S - med) / mad).astype(np.float32) * mf
    Spre = (nconv(S, mf, 0.01 * MM) * mf).astype(np.float32)
    a = theta_global(S, mf, m, 128)
    rec = {"theta_crop_deg": round(float(np.rad2deg(a)), 1),
           "n_text": int(txt.sum()), "n_blank": int(blk.sum())}
    for name, ang in (("A_FIB_theta", a), ("B_ANI_90", np.pi / 2)):
        bg = aniso_bg(Spre, mf, ang, 3.0 * MM, 0.12 * MM)
        rec[name] = round(auc(nconv(Spre - bg, mf, 0.40 * MM), txt, blk), 4)
        del bg; gc.collect()
    rec["C_ISO_3.0"] = round(auc(nconv(Spre - nconv(Spre, mf, 3.0 * MM), mf, 0.40 * MM), txt, blk), 4)
    rec["D_PLAIN"] = round(auc(nconv(Spre, mf, 0.40 * MM), txt, blk), 4)
    del S, Spre; gc.collect()
    for t in ("v0.1b", "v1b", "v2", "v3", "team"):
        p = os.path.join(d, f"s_bot_{t}.npy")
        if os.path.exists(p):
            s = np.load(p).astype(np.float32)
            rec[t] = round(auc(s, txt, blk), 4)
            del s; gc.collect()
    res[f"{seg}/{crop}"] = rec
    print(f"{seg}/{crop} {json.dumps(rec)}", flush=True)
    del m, mf, txt, blk; gc.collect()

json.dump(res, open(os.path.join(ROOT, "stats/explore/fb_e8_heldout_fullres.json"), "w"), indent=1)
print("\n-- EVAL means (7 crops, 2.4 um): " + "  ".join(
    f"{t}={np.mean([res[k][t] for k in res]):.4f}" for t in
    ("A_FIB_theta", "B_ANI_90", "C_ISO_3.0", "D_PLAIN", "v0.1b", "v1b", "v2", "v3", "team")))
