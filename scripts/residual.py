#!/usr/bin/env python3
"""5.4/5.5: relief, fibre-suppressed face residual, (optional) inpainting error -> s_top, s_bot.
Inputs: <derived dir> from topo_faces.py (+ optional a_top.npy / a_bot.npy from inpaint_net.py).
All parameters are FIXED here (METHOD.md); nothing is tuned per target.
usage: residual.py <derived_dir> <pitch_um> [--no-inpaint]"""
import os, sys, json, argparse, time, numpy as np, cv2
from scipy.ndimage import gaussian_filter, label
import gc
P = dict(
    t_min_um=30.0, t_max_um=380.0,          # on-sheet thickness bounds (= 4..40 voxels at 9.362 µm, expressed in µm so the same physical bound holds at 2.4 µm)
    sigma_undulation_mm=0.6,                 # relief = h - Gaussian(h, 0.6 mm)
    st_sigma_px=6, bg_len_mm=1.0, bg_width_px=1.5, n_orient=12,   # structure tensor + oriented background
    w_r=0.5, w_e=0.3, w_a=0.2,               # score weights (calibration-fixed)
    dog_small_mm=0.15, dog_large_mm=1.2,     # band-pass
    edge_margin_mm=0.4, grad_t_max=0.3, grad_t_sigma_mm=0.1, hole_open_mm=0.05,   # damage mask: t<t_min, |grad(t smoothed 0.1 mm)| > 0.3 voxel/px (tear/step), CT==0, dilated 0.4 mm
    grain_pct=99.9, grain_max_mm=0.1, grain_min_mm=0.02, grain_margin_mm=0.3,
    u8_scale=8.0,                            # uint8 = 255*clip(0.5 + s/8, 0, 1)
    valid_min_fraction=0.02,
)

def gauss(x, sigma):
    """Gaussian smoothing; for sigma >= 8 px three box passes of width L = sqrt(4 sigma^2 + 1) (same variance, O(1)/px)."""
    x = np.ascontiguousarray(x, dtype=np.float32)
    if sigma < 8: return gaussian_filter(x, sigma, mode="nearest")
    L = int(round(np.sqrt(4 * sigma * sigma + 1))) | 1
    for _ in range(3): x = cv2.boxFilter(x, -1, (L, L), normalize=True, borderType=cv2.BORDER_REPLICATE)
    return x

def dilate(mask, r):
    """binary dilation by a disc of radius r px (== distance transform <= r), low memory."""
    if r <= 0: return mask.copy()
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    return cv2.dilate(mask.astype(np.uint8), k) > 0

def nconv(x, m, sigma):
    """normalised Gaussian convolution of x over mask m (holes do not bleed)."""
    num = gauss(x * m, sigma); den = gauss(m.astype(np.float32), sigma)
    return num / np.maximum(den, 1e-3)

def mad_z(x, m):
    v = x[m]; med = np.median(v); mad = np.median(np.abs(v - med)) * 1.4826
    return (x - med) / max(mad, 1e-6), float(med), float(mad)

def orientation(S, m, sigma):
    g = gaussian_filter(S, 1.0, mode="nearest")
    gy, gx = np.gradient(g)
    Jxx = gaussian_filter(gx * gx, sigma); Jyy = gaussian_filter(gy * gy, sigma); Jxy = gaussian_filter(gx * gy, sigma)
    theta_grad = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)         # dominant gradient direction
    coh = np.sqrt((Jxx - Jyy) ** 2 + 4 * Jxy ** 2) / np.maximum(Jxx + Jyy, 1e-6)
    return theta_grad + np.pi / 2, coh                          # fibre direction = perpendicular to gradient

def oriented_background(S, m, theta, sig_along, sig_across, n_orient):
    """S smoothed along the local fibre direction: per orientation bin rotate, separable Gaussian, rotate back, select."""
    H, W = S.shape; bins = np.round((np.mod(theta, np.pi) / np.pi) * n_orient).astype(int) % n_orient
    out = np.zeros_like(S); D = int(np.ceil(np.hypot(H, W))); cx, cy = W / 2, H / 2
    Sm = (S * m).astype(np.float32); mf = m.astype(np.float32)
    for b in range(n_orient):
        sel = bins == b
        if not sel.any(): continue
        ang = b * 180.0 / n_orient                                  # fibre direction angle (deg, image y-down)
        M = cv2.getRotationMatrix2D((cx, cy), ang, 1.0); M[0, 2] += D / 2 - cx; M[1, 2] += D / 2 - cy
        rs = cv2.warpAffine(Sm, M, (D, D), flags=cv2.INTER_LINEAR, borderValue=0)
        rm = cv2.warpAffine(mf, M, (D, D), flags=cv2.INTER_LINEAR, borderValue=0)
        kc = int(6 * sig_across) | 1; L = int(round(np.sqrt(4 * sig_along ** 2 + 1))) | 1
        num = cv2.GaussianBlur(rs, (1, kc), sigmaX=0, sigmaY=sig_across); den = cv2.GaussianBlur(rm, (1, kc), sigmaX=0, sigmaY=sig_across)
        for _ in range(3):
            num = cv2.boxFilter(num, -1, (L, 1), normalize=True, borderType=cv2.BORDER_REPLICATE); den = cv2.boxFilter(den, -1, (L, 1), normalize=True, borderType=cv2.BORDER_REPLICATE)
        bg = num / np.maximum(den, 1e-3)
        Mi = cv2.invertAffineTransform(M)
        back = cv2.warpAffine(bg, Mi, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        out[sel] = back[sel]; del rs, rm, num, den, bg, back
    del Sm, mf; gc.collect()
    return out

def face(prefix, d, pitch, onsheet, sign, log):
    h = np.clip(np.load(os.path.join(d, f"k_{prefix}.npy")).astype(np.float32), -2, 200) * pitch
    S = np.load(os.path.join(d, f"S_{prefix}.npy")).astype(np.float32)
    su = P["sigma_undulation_mm"] * 1000 / pitch
    relief = sign * (h - nconv(h, onsheet, su))                   # positive = proud of the sheet (outward)
    theta, coh = orientation(S, onsheet, P["st_sigma_px"]); coh_med = float(np.median(coh[onsheet])); del coh
    bg = oriented_background(S, onsheet, theta, P["bg_len_mm"] * 1000 / pitch, P["bg_width_px"], P["n_orient"]); del theta
    e = S - bg; del bg; gc.collect()
    ap = os.path.join(d, f"a_{prefix}.npy")
    a = np.load(ap).astype(np.float32) if os.path.exists(ap) else None
    zr, mr, sr = mad_z(relief, onsheet); ze, me, se = mad_z(e, onsheet)
    log[prefix] = dict(relief_median_um=mr, relief_mad_um=sr, e_median=me, e_mad=se, coherence_median=coh_med)
    if a is not None:
        za, ma, sa = mad_z(a, onsheet); log[prefix].update(a_median=ma, a_mad=sa)
        s = P["w_r"] * zr + P["w_e"] * ze + P["w_a"] * za; del za
    else:
        s = (P["w_r"] * zr + P["w_e"] * ze) / (P["w_r"] + P["w_e"]); log[prefix]["inpaint"] = "absent: weights renormalised (method v0.1)"
    del zr, ze, a; gc.collect()
    np.save(os.path.join(d, f"relief_{prefix}.npy"), relief.astype(np.float16)); np.save(os.path.join(d, f"e_{prefix}.npy"), e.astype(np.float16)); del relief, e
    return s.astype(np.float32), S

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("d"); ap.add_argument("pitch", type=float); ap.add_argument("--tag", default="v0.2"); ap.add_argument("--edge-margin-mm", type=float, default=None)
    a = ap.parse_args(); d = a.d; pitch = a.pitch; t0 = time.time()
    if os.path.exists(os.path.join(d, f"residual_{a.tag}.done")): print("done already"); return
    if a.edge_margin_mm is not None: P["edge_margin_mm"] = a.edge_margin_mm
    k_top = np.clip(np.load(os.path.join(d, "k_top.npy")).astype(np.float32), -2, 200); k_bot = np.clip(np.load(os.path.join(d, "k_bot.npy")).astype(np.float32), -2, 200); valid = np.load(os.path.join(d, "valid.npy")) > 0
    ct = np.load(os.path.join(d, "ct_mid.npy")).astype(np.float32); t = (k_bot - k_top) * pitch
    onsheet = valid & (t >= P["t_min_um"]) & (t <= P["t_max_um"]) & (ct > 0)
    log = dict(params=P, pitch_um=pitch, onsheet_fraction=float(onsheet.mean()), t_median_um=float(np.median(t[valid])) if valid.any() else None)
    assert onsheet.mean() > P["valid_min_fraction"], "chart has (almost) no on-sheet area"
    # damage mask: thin/absent sheet, steep thickness gradient, zero CT; dilated by edge_margin
    ts = nconv(np.where(valid, t / pitch, 0), valid, P["grad_t_sigma_mm"] * 1000 / pitch); gy, gx = np.gradient(ts); gradt = np.hypot(gy, gx)
    damage = (~onsheet) | (gradt > P["grad_t_max"])
    # macroscopic damage only: opening by a 0.05 mm disc removes fibre-scale voids (which stay excluded pixel-wise via onsheet)
    ro = int(round(P["hole_open_mm"] * 1000 / pitch)); ko = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * ro + 1, 2 * ro + 1))
    damage = cv2.morphologyEx(damage.astype(np.uint8), cv2.MORPH_OPEN, ko) > 0
    em = int(round(P["edge_margin_mm"] * 1000 / pitch))
    damage_d = dilate(damage, em); del ts, gy, gx, gradt, damage; gc.collect()
    for prefix, sign in (("top", -1.0), ("bot", +1.0)):
        s, S = face(prefix, d, pitch, onsheet, sign, log)
        # grains: bright, small
        thr = np.percentile(S[onsheet], P["grain_pct"]); g = (S > thr) & onsheet
        lab, n = label(g); sizes = np.bincount(lab.ravel()); maxpx = (P["grain_max_mm"] * 1000 / pitch) ** 2; minpx = (P["grain_min_mm"] * 1000 / pitch) ** 2
        small = np.zeros(n + 1, bool); small[1:] = (sizes[1:] <= maxpx) & (sizes[1:] >= minpx); grain = small[lab]
        gm = int(round(P["grain_margin_mm"] * 1000 / pitch)); grain_d = dilate(grain, gm) if grain.any() else grain; del lab
        mask = onsheet & ~damage_d & ~grain_d
        s_bp = nconv(s, mask, P["dog_small_mm"] * 1000 / pitch) - nconv(s, mask, P["dog_large_mm"] * 1000 / pitch)
        s_bp = np.where(mask, s_bp, 0).astype(np.float32)
        log[prefix].update(mask_fraction=float(mask.mean()), grain_fraction=float(grain.mean()), n_grains=int(small[1:].sum()))
        np.save(os.path.join(d, f"s_{prefix}_{a.tag}.npy"), s_bp.astype(np.float16))
        np.save(os.path.join(d, f"mask_{prefix}.npy"), mask)
        u8 = (255 * np.clip(0.5 + s_bp / P["u8_scale"], 0, 1)).astype(np.uint8); np.save(os.path.join(d, f"s_{prefix}_{a.tag}_u8.npy"), u8)
        del s, S, s_bp, u8, mask, g, grain, grain_d; gc.collect()
    np.save(os.path.join(d, "onsheet.npy"), onsheet); np.save(os.path.join(d, "damage_d.npy"), damage_d)
    log["seconds"] = time.time() - t0
    json.dump(log, open(os.path.join(d, f"residual_{a.tag}.json"), "w"), indent=1, default=str); print(json.dumps(log, indent=1, default=str))
    open(os.path.join(d, f"residual_{a.tag}.done"), "w").close()

if __name__ == "__main__":
    main()
