"""E1: does a coherent fibre orientation field exist in these CT surfaces, and is the papyrus
background anisotropic at all? Diagnostics only, TRAIN + VAL crops."""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from fb_lib import *
from scipy.ndimage import gaussian_filter

def base(x, chans):
    return x[chans].mean(axis=0)

def masked_acf(img, m, half=60):
    """masked autocorrelation of img (mean removed inside m), normalised by the mask's own acf."""
    f = np.where(m, img, 0.0).astype(np.float32)
    mu = f.sum() / max(m.sum(), 1)
    f = np.where(m, img - mu, 0.0).astype(np.float32)
    mf = m.astype(np.float32)
    H, W = f.shape
    n = 1 << int(np.ceil(np.log2(max(H, W) * 2)))
    F = np.fft.rfft2(f, s=(n, n)); M = np.fft.rfft2(mf, s=(n, n))
    ac = np.fft.irfft2(F * np.conj(F), s=(n, n))
    am = np.fft.irfft2(M * np.conj(M), s=(n, n))
    r = ac / np.maximum(am, 1.0)
    r = np.fft.fftshift(r)
    c = n // 2
    r = r[c - half:c + half + 1, c - half:c + half + 1]
    return r / max(r[half, half], 1e-12)

def acf_profile(r, half, ang_deg):
    """radial profile of the acf along direction ang (deg, image y-down, 0 = +x)."""
    a = np.deg2rad(ang_deg)
    ds = np.arange(0, half + 1)
    ys = half + ds * np.sin(a); xs = half + ds * np.cos(a)
    from scipy.ndimage import map_coordinates
    return map_coordinates(r, [ys, xs], order=1, mode="nearest")

def corr_len(prof):
    """first lag (px) where the profile falls below 1/e, linear interp."""
    th = np.exp(-1.0)
    for i in range(1, len(prof)):
        if prof[i] < th:
            p0, p1 = prof[i - 1], prof[i]
            return (i - 1) + (p0 - th) / max(p0 - p1, 1e-9)
    return float(len(prof))

CH_BOT = [11, 12, 13, 14]     # delta = -4..-1 (D1/D2 depth of maximum on the bottom face)
CH_TOP = [3, 4, 5]            # delta = -1..+1 on the top face
res = {}
for seg, crop in TRAIN_CROPS + VAL_CROPS:
    x, _, m = load(seg, crop)
    y = fit_classes(seg, crop)
    Sb = base(x, CH_BOT); St = base(x, CH_TOP)
    rec = {}
    # sanity: does the plain smoothed brightness show the known ~0.6 signal on these crops?
    rec["auc_raw_bot"] = round(auc_on(Sb, y, m), 4)
    rec["auc_g250um_bot"] = round(auc_on(nconv(Sb, m, 250.0 / PITCH), y, m), 4)
    rec["auc_g250um_top"] = round(auc_on(nconv(St, m, 250.0 / PITCH), y, m), 4)
    # orientation field at several tensor scales
    for st in (2, 4, 8, 16, 32):
        th, coh = structure_tensor(Sb, m, 1.0, st)
        thm = np.mod(th, np.pi)
        rec[f"coh_med_st{st}"] = round(float(np.median(coh[m])), 4)
        # crop-global dominant direction from the vector mean of 2*theta
        c2 = np.cos(2 * thm[m]).mean(); s2 = np.sin(2 * thm[m]).mean()
        R = float(np.hypot(c2, s2))               # 0 = uniform directions, 1 = one direction
        rec[f"R_global_st{st}"] = round(R, 4)
        rec[f"theta_global_st{st}_deg"] = round(float(np.rad2deg(0.5 * np.arctan2(s2, c2)) % 180), 1)
        if st == 8:
            th8 = thm.copy()
    # top/bottom face agreement of the orientation field at st=8
    tht, _ = structure_tensor(St, m, 1.0, 8)
    d = np.mod(th8 - np.mod(tht, np.pi), np.pi)
    d = np.minimum(d, np.pi - d)
    rec["topbot_theta_med_absdiff_deg"] = round(float(np.rad2deg(np.median(d[m]))), 1)
    rec["topbot_theta_frac_within20deg"] = round(float((np.rad2deg(d[m]) < 20).mean()), 3)
    # anisotropy of the papyrus background: masked acf over BLANK pixels only, after removing
    # scales > 1 mm (so the acf measures texture, not chart-scale gradients)
    hp = Sb - nconv(Sb, m, 1000.0 / PITCH)
    mb = m & (y == 0)
    half = 60
    r = masked_acf(hp, mb, half)
    best = None
    for a in range(0, 180, 5):
        cl = corr_len(acf_profile(r, half, a))
        if best is None or cl > best[1]:
            best = (a, cl)
    a_long, cl_long = best
    cl_perp = corr_len(acf_profile(r, half, (a_long + 90) % 180))
    worst = min(((a, corr_len(acf_profile(r, half, a))) for a in range(0, 180, 5)), key=lambda t: t[1])
    rec["acf_corrlen_max_um"] = round(cl_long * PITCH, 1)
    rec["acf_dir_max_deg"] = a_long
    rec["acf_corrlen_perp_um"] = round(cl_perp * PITCH, 1)
    rec["acf_corrlen_min_um"] = round(worst[1] * PITCH, 1)
    rec["acf_anisotropy_max_over_min"] = round(cl_long / max(worst[1], 1e-9), 3)
    # the same for the LABEL field (what the ink texture looks like), for comparison
    rl = masked_acf((y == 1).astype(np.float32), m, half)
    bl = max(((a, corr_len(acf_profile(rl, half, a))) for a in range(0, 180, 5)), key=lambda t: t[1])
    wl = min(((a, corr_len(acf_profile(rl, half, a))) for a in range(0, 180, 5)), key=lambda t: t[1])
    rec["label_acf_corrlen_max_um"] = round(bl[1] * PITCH, 1)
    rec["label_acf_dir_max_deg"] = bl[0]
    rec["label_acf_corrlen_min_um"] = round(wl[1] * PITCH, 1)
    res[f"{seg}/{crop}"] = rec
    print(f"{seg}/{crop}", json.dumps(rec), flush=True)

json.dump(res, open(os.path.join(ROOT, "stats/explore/fb_e1_orient.json"), "w"), indent=1)
