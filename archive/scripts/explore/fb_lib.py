"""fiberbg exploration: shared helpers. 19.2 um/px pooled surface-aligned stacks."""
import os, json, numpy as np, cv2
from scipy.ndimage import gaussian_filter

ROOT = "/home/user/megara"
PITCH = 19.2  # um per pixel on the ds8 grid

TRAIN_CROPS = ([("20231005123336", "train")]
               + [("20230929220926", f"held{i}") for i in (1, 2, 3, 4)]
               + [("20231012184424", f"held{i}") for i in (1, 2, 3)])
VAL_CROPS = [("20231012184424", "held4")]
EVAL_CROPS = ([("20231005123336", f"held{i}") for i in (1, 2, 3)]
              + [("20231210121321", f"held{i}") for i in (1, 2, 3, 4)])


def cdir(seg, crop):
    return os.path.join(ROOT, "data/s1", seg, "derived", crop)


def load(seg, crop):
    d = cdir(seg, crop)
    x = np.load(os.path.join(d, "ds8_x.npy"))
    y = np.load(os.path.join(d, "ds8_y.npy"))
    m = x[22] > 0.5
    return x, y, m


def auc(score, pos, neg):
    """rank AUC of score[pos] vs score[neg] (boolean masks)."""
    a = score[pos].astype(np.float64); b = score[neg].astype(np.float64)
    if a.size < 10 or b.size < 10:
        return float("nan")
    v = np.concatenate([a, b])
    r = np.empty_like(v)
    order = np.argsort(v, kind="mergesort")
    sv = v[order]
    # average ranks for ties
    n = v.size
    i = 0
    ranks = np.empty(n)
    while i < n:
        j = i
        while j + 1 < n and sv[j + 1] == sv[i]:
            j += 1
        ranks[i:j + 1] = 0.5 * (i + j) + 1.0
        i = j + 1
    r[order] = ranks
    na, nb = a.size, b.size
    return float((r[:na].sum() - na * (na + 1) / 2.0) / (na * nb))


def auc_on(score, y, m):
    pos = (y == 1) & m
    neg = (y == 0) & m
    return auc(score, pos, neg)


def nconv(x, m, sigma):
    """normalised gaussian convolution over mask m."""
    mf = m.astype(np.float32)
    num = gaussian_filter(x * mf, sigma, mode="nearest")
    den = gaussian_filter(mf, sigma, mode="nearest")
    return num / np.maximum(den, 1e-3)


def structure_tensor(S, m, sigma_grad, sigma_tensor):
    """returns theta (fibre direction, rad, image coords y-down), coherence."""
    g = nconv(S, m, sigma_grad)
    g = np.where(m, g, 0.0).astype(np.float32)
    gy, gx = np.gradient(g)
    mf = m.astype(np.float32)
    gy *= mf; gx *= mf
    Jxx = gaussian_filter(gx * gx, sigma_tensor, mode="nearest")
    Jyy = gaussian_filter(gy * gy, sigma_tensor, mode="nearest")
    Jxy = gaussian_filter(gx * gy, sigma_tensor, mode="nearest")
    theta_grad = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)
    coh = np.sqrt((Jxx - Jyy) ** 2 + 4 * Jxy ** 2) / np.maximum(Jxx + Jyy, 1e-12)
    return theta_grad + np.pi / 2, coh


def oriented_filter(S, m, theta, sig_along, sig_across, n_orient=16, mode="mean"):
    """local mean (or std) of S in an anisotropic gaussian window aligned with theta.
    theta is the FIBRE direction; sig_along smooths along it, sig_across across it."""
    H, W = S.shape
    bins = np.round((np.mod(theta, np.pi) / np.pi) * n_orient).astype(np.int32) % n_orient
    out = np.zeros_like(S, dtype=np.float32)
    D = int(np.ceil(np.hypot(H, W))) + 2
    cx, cy = W / 2.0, H / 2.0
    Sm = (S * m).astype(np.float32)
    mf = m.astype(np.float32)
    S2 = (S * S * m).astype(np.float32) if mode == "std" else None
    for b in range(n_orient):
        sel = bins == b
        if not sel.any():
            continue
        ang = b * 180.0 / n_orient
        M = cv2.getRotationMatrix2D((cx, cy), ang, 1.0)
        M[0, 2] += D / 2 - cx; M[1, 2] += D / 2 - cy
        rs = cv2.warpAffine(Sm, M, (D, D), flags=cv2.INTER_LINEAR, borderValue=0)
        rm = cv2.warpAffine(mf, M, (D, D), flags=cv2.INTER_LINEAR, borderValue=0)
        # after rotation by ang, the fibre direction lies along the image x axis
        num = _sep(rs, sig_along, sig_across)
        den = _sep(rm, sig_along, sig_across)
        bg = num / np.maximum(den, 1e-3)
        if mode == "std":
            r2 = cv2.warpAffine(S2, M, (D, D), flags=cv2.INTER_LINEAR, borderValue=0)
            n2 = _sep(r2, sig_along, sig_across)
            bg = np.sqrt(np.maximum(n2 / np.maximum(den, 1e-3) - bg * bg, 0.0))
            del r2, n2
        Mi = cv2.invertAffineTransform(M)
        back = cv2.warpAffine(bg, Mi, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        out[sel] = back[sel]
        del rs, rm, num, den, bg, back
    return out


def _sep(img, sig_x, sig_y):
    kx = max(1, int(6 * sig_x) | 1); ky = max(1, int(6 * sig_y) | 1)
    if sig_x >= 8:
        L = int(round(np.sqrt(4 * sig_x * sig_x + 1))) | 1
        o = img
        for _ in range(3):
            o = cv2.boxFilter(o, -1, (L, 1), normalize=True, borderType=cv2.BORDER_REPLICATE)
    else:
        o = cv2.GaussianBlur(img, (kx, 1), sigmaX=sig_x, sigmaY=0, borderType=cv2.BORDER_REPLICATE)
    if sig_y >= 8:
        L = int(round(np.sqrt(4 * sig_y * sig_y + 1))) | 1
        for _ in range(3):
            o = cv2.boxFilter(o, -1, (1, L), normalize=True, borderType=cv2.BORDER_REPLICATE)
    else:
        o = cv2.GaussianBlur(o, (1, ky), sigmaX=0, sigmaY=sig_y, borderType=cv2.BORDER_REPLICATE)
    return o


def zmad(x, m):
    v = x[m]
    med = np.median(v); mad = np.median(np.abs(v - med)) * 1.4826
    return (x - med) / max(mad, 1e-9)


# ---- own label classes for the TRAINING segments (their cls_blank.npy is empty) ----
LBL_DIR = os.path.join(ROOT, "stats/explore/labels")

def fit_classes(seg, crop):
    """y2 on the ds8 grid: 1 = label, 0 = >=0.3 mm from any label AND inside the labelled zone
    (label closed with a 5 mm disc), -1 = ignore. Same geometric rule as the project's judge
    classes but WITHOUT the team-model blank veto (the training segments' cls_blank.npy is empty).
    For 20231005123336 the official ds8_y is used instead."""
    if seg == "20231005123336":
        return np.load(os.path.join(cdir(seg, crop), "ds8_y.npy"))
    os.makedirs(LBL_DIR, exist_ok=True)
    p = os.path.join(LBL_DIR, f"y2_{seg}_{crop}.npy")
    if os.path.exists(p):
        return np.load(p)
    F = 8
    L = np.load(os.path.join(cdir(seg, crop), "label.npy"))
    H8, W8 = L.shape[0] // F, L.shape[1] // F
    lp = L[:H8 * F, :W8 * F].reshape(H8, F, W8, F).mean(axis=(1, 3))
    lab = (lp > 0.5).astype(np.uint8)
    r_near = int(round(300.0 / PITCH))       # 0.3 mm
    r_zone = int(round(5000.0 / PITCH))      # 5 mm closing
    k = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    near = cv2.dilate(lab, k(r_near)) > 0
    zone = cv2.morphologyEx(lab, cv2.MORPH_CLOSE, k(r_zone)) > 0
    y = np.full(lab.shape, -1, np.int8)
    y[zone & ~near] = 0
    y[lab > 0] = 1
    np.save(p, y)
    return y


def fill_holes(S, m, sigma_px):
    """replace masked-out pixels by the local mean, so morphology is not pulled by zeros."""
    f = nconv(S, m, sigma_px)
    return np.where(m, S, f).astype(np.float32)


def oriented_morph(S, m, theta, len_along, wid_across, op="open", n_orient=16):
    """grey-scale morphology with a LINE structuring element along the local fibre direction.
    op='open' -> the along-fibre lower envelope (a background robust to bright ink, which a local
    MEAN is not); the white top-hat S - open(S) keeps whatever is short along the fibre."""
    H, W = S.shape
    Sf = fill_holes(S, m, 6.0)
    bins = np.round((np.mod(theta, np.pi) / np.pi) * n_orient).astype(np.int32) % n_orient
    out = np.zeros_like(S, dtype=np.float32)
    D = int(np.ceil(np.hypot(H, W))) + 2
    cx, cy = W / 2.0, H / 2.0
    L = max(3, int(round(len_along)) | 1)
    Wd = max(1, int(round(wid_across)) | 1)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (L, Wd))   # long along image x, thin along y
    for b in range(n_orient):
        sel = bins == b
        if not sel.any():
            continue
        ang = b * 180.0 / n_orient
        M = cv2.getRotationMatrix2D((cx, cy), ang, 1.0)
        M[0, 2] += D / 2 - cx; M[1, 2] += D / 2 - cy
        rs = cv2.warpAffine(Sf, M, (D, D), flags=cv2.INTER_LINEAR, borderValue=0)
        o = cv2.morphologyEx(rs, cv2.MORPH_OPEN if op == "open" else cv2.MORPH_CLOSE, k,
                             borderType=cv2.BORDER_REPLICATE)
        Mi = cv2.invertAffineTransform(M)
        back = cv2.warpAffine(o, Mi, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        out[sel] = back[sel]
        del rs, o, back
    return out
