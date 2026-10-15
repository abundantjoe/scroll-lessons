"""P4-I (RULES.md DECL-P4-8): reader-free numeric row-structure statistic.

Numbers only. Tiles are loaded as uint8 arrays; nothing is displayed.

Per tile (1068 x 1068 display PNG, 53.4 px/mm, 0 outside mesh-valid):
  support  = mesh-valid, in-scan pixels: the complement of the connected
             zero-valued regions of area >= ZERO_BLOB_MIN_MM2 (tiles are written 0
             outside mesh-valid and, for the 1.129 um materials, 0 out of scan;
             small zero blobs are valid dark pixels, e.g. the 1 % clip of the
             CT stretch, and stay in).
  field    = the tile at 13.35 px/mm (INTER_AREA / 4), minus its local mean
             (normalized Gaussian convolution, sigma LOCAL_MEAN_MM), tapered
             inside the support (erode 2 sigma, blur sigma = TAPER_MM) and by a
             radial Tukey window (rotation-symmetric, so no axis leakage).
  spectrum = |FFT|^2 zero-padded to NFFT, sampled on a polar grid:
             periods 3-9 mm (N_RAD radii, linear in |k|), theta 0-178 deg step 2.
  S_row    = max over theta of P(k*(theta), theta) / median_theta' P(k*(theta), theta'),
             k*(theta) = argmax over the band of P(., theta).  theta* = its angle.
Angle convention: theta is the wavevector angle in image axes (x = column to
the right, y = row downward), mod 180.  Text rows running along x (stacked
along y) give theta* = 90.
"""
import cv2
import numpy as np

PX_PER_MM_DISPLAY = 53.4
DS = 4                               # 1068 -> 267 px, 13.35 px/mm
PX_PER_MM = PX_PER_MM_DISPLAY / DS
PERIOD_MM = (3.0, 9.0)               # DECL-P4-8 item 2 band
THETA_STEP = 2.0                     # DECL-P4-8 item 2
THETAS = np.arange(0.0, 180.0, THETA_STEP)
N_RAD = 48
NFFT = 1024
ZERO_BLOB_MIN_MM2 = 2.0
LOCAL_MEAN_MM = 4.0
TAPER_MM = 0.5
TUKEY_INNER = 0.75
MIN_SUPPORT = 0.25                   # of the tile area after erosion; else insufficient
FLAT_RMS = 0.25                      # grey levels: a de-meaned field this flat is blank (8-bit)
PARAMS = dict(PX_PER_MM_DISPLAY=PX_PER_MM_DISPLAY, DS=DS, PERIOD_MM=PERIOD_MM,
              THETA_STEP=THETA_STEP, N_RAD=N_RAD, NFFT=NFFT,
              ZERO_BLOB_MIN_MM2=ZERO_BLOB_MIN_MM2, LOCAL_MEAN_MM=LOCAL_MEAN_MM,
              TAPER_MM=TAPER_MM, TUKEY_INNER=TUKEY_INNER, MIN_SUPPORT=MIN_SUPPORT,
              FLAT_RMS=FLAT_RMS)


def support_mask(a):
    """Mesh-valid, in-scan support of a display tile (bool, same shape)."""
    z = (a == 0).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(z, connectivity=8)
    amin = ZERO_BLOB_MIN_MM2 * PX_PER_MM_DISPLAY ** 2
    big = np.zeros(n, bool)
    big[1:] = stats[1:, cv2.CC_STAT_AREA] >= amin
    return ~big[lab]


def _radial_window(n):
    y, x = np.mgrid[0:n, 0:n].astype(np.float64)
    c = (n - 1) / 2.0
    r = np.hypot(x - c, y - c) / (n / 2.0)
    w = np.ones_like(r)
    t = (r > TUKEY_INNER) & (r < 1.0)
    w[t] = 0.5 * (1 + np.cos(np.pi * (r[t] - TUKEY_INNER) / (1 - TUKEY_INNER)))
    w[r >= 1.0] = 0.0
    return w


def _polar_grid(nfft):
    c = nfft // 2
    kmin, kmax = 1.0 / PERIOD_MM[1], 1.0 / PERIOD_MM[0]          # cycles / mm
    ks = np.linspace(kmin, kmax, N_RAD)
    rho = ks / PX_PER_MM * nfft                                   # FFT bins
    th = np.deg2rad(THETAS)
    mx = (c + rho[:, None] * np.cos(th)[None, :]).astype(np.float32)
    my = (c + rho[:, None] * np.sin(th)[None, :]).astype(np.float32)
    return ks, mx, my


_WIN = {}
_GRID = {}


def prepare(a, mask=None):
    """Tapered, locally de-meaned field at 13.35 px/mm and its weight; None if insufficient."""
    a = np.asarray(a)
    if mask is None:
        mask = support_mask(a)
    x = cv2.resize(a.astype(np.float32), None, fx=1.0 / DS, fy=1.0 / DS, interpolation=cv2.INTER_AREA)
    m = cv2.resize(mask.astype(np.float32), None, fx=1.0 / DS, fy=1.0 / DS, interpolation=cv2.INTER_AREA)
    m = (m >= 0.999).astype(np.float32)
    s = LOCAL_MEAN_MM * PX_PER_MM
    num = cv2.GaussianBlur(x * m, (0, 0), s, borderType=cv2.BORDER_CONSTANT)
    den = cv2.GaussianBlur(m, (0, 0), s, borderType=cv2.BORDER_CONSTANT)
    v = np.where(m > 0, x - num / np.maximum(den, 1e-6), 0.0)
    st = TAPER_MM * PX_PER_MM
    k = int(2 * round(2 * st) + 1)
    me = cv2.erode(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    w = cv2.GaussianBlur(me, (0, 0), st, borderType=cv2.BORDER_CONSTANT) * m
    n = x.shape[0]
    if n not in _WIN:
        _WIN[n] = _radial_window(n)
    w = w * _WIN[n]
    if me.mean() < MIN_SUPPORT or w.sum() <= 0:
        return None
    mu = (v * w).sum() / w.sum()
    if np.sqrt((((v - mu) ** 2) * w).sum() / w.sum()) < FLAT_RMS:
        return None
    f = (v - mu) * w
    return f


def polar_power(f):
    n = f.shape[0]
    pad = np.zeros((NFFT, NFFT), np.float64)
    o = (NFFT - n) // 2
    pad[o:o + n, o:o + n] = f
    P = np.abs(np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(pad)))) ** 2
    if NFFT not in _GRID:
        _GRID[NFFT] = _polar_grid(NFFT)
    ks, mx, my = _GRID[NFFT]
    return ks, cv2.remap(P.astype(np.float32), mx, my, cv2.INTER_LINEAR).astype(np.float64)


def s_row_from_polar(Pp, ks):
    """DECL-P4-8 item 2 on a polar spectrum Pp[rad, theta]."""
    med = np.median(Pp, axis=1)                       # per |k|, over orientations
    kstar = np.argmax(Pp, axis=0)                     # per theta, band peak
    peak = Pp[kstar, np.arange(Pp.shape[1])]
    R = peak / np.maximum(med[kstar], 1e-300)
    j = int(np.argmax(R))
    return dict(S_row=float(R[j]), theta_star=float(THETAS[j]),
                period_mm_at_peak=float(1.0 / ks[kstar[j]]), R_theta=R)


def tile_stat(a, mask=None):
    """S_row, theta*, peak period for one display tile; S_row None if insufficient support."""
    if mask is None:
        mask = support_mask(a)
    f = prepare(a, mask)
    if f is None:
        return dict(S_row=None, theta_star=None, period_mm_at_peak=None,
                    support_frac=float(mask.mean()), insufficient=True)
    ks, Pp = polar_power(f)
    r = s_row_from_polar(Pp, ks)
    r.pop('R_theta')
    r.update(support_frac=float(mask.mean()), insufficient=False)
    return r


def tile_R(a, mask=None):
    """Per-orientation ratio R(theta) (item 2, before the max); None if insufficient."""
    if mask is None:
        mask = support_mask(a)
    f = prepare(a, mask)
    if f is None:
        return None
    ks, Pp = polar_power(f)
    return s_row_from_polar(Pp, ks)['R_theta']


def s_anch(R, theta_c, tol=10.0):
    """PROPOSED (ASK-1), not declared: max of R(theta) within +-tol of the fixed theta_c."""
    if R is None or theta_c is None:
        return None
    sel = ang_diff(THETAS, theta_c) <= tol
    return float(np.max(np.asarray(R)[sel]))


def ang_diff(a, b):
    """Absolute difference of axial angles mod 180 (deg)."""
    d = np.abs((np.asarray(a, float) - np.asarray(b, float)) % 180.0)
    return np.minimum(d, 180.0 - d)


def circ_median(angles, step=0.5):
    """Axial (mod 180) median: the angle minimizing the summed axial distance."""
    a = np.asarray([x for x in angles if x is not None], float)
    if a.size == 0:
        return None
    cand = np.arange(0.0, 180.0, step)
    cost = ang_diff(cand[:, None], a[None, :]).sum(axis=1)
    return float(cand[int(np.argmin(cost))])


def m_ink(a, mask, thr):
    """Fraction of support pixels above thr (the control strip's pixel p95)."""
    v = a[mask]
    return float((v > thr).mean()) if v.size else 0.0


def auc(pos, neg):
    """Mann-Whitney AUC P(pos > neg) + 0.5 P(tie)."""
    pos = np.asarray(pos, float); neg = np.asarray(neg, float)
    if pos.size == 0 or neg.size == 0:
        return None
    allv = np.concatenate([pos, neg])
    order = np.argsort(allv, kind='mergesort')
    ranks = np.empty(allv.size)
    sv = allv[order]
    i = 0
    while i < sv.size:
        j = i
        while j + 1 < sv.size and sv[j + 1] == sv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1
        i = j + 1
    rp = ranks[:pos.size].sum()
    return float((rp - pos.size * (pos.size + 1) / 2.0) / (pos.size * neg.size))


def jaccard(a, b):
    a, b = set(a), set(b)
    u = a | b
    return None if not u else len(a & b) / len(u)


def jaccard_perm_p(a, b, universe, n_perm=10000, seed=20260926):
    """P(J(random |a|-set, random |b|-set from universe) >= J(a, b)), add-one."""
    j0 = jaccard(a, b)
    if j0 is None:
        return None, None
    U = sorted(universe)
    rng = np.random.default_rng(seed)
    na, nb = len(set(a)), len(set(b))
    ge = 0
    for _ in range(n_perm):
        ra = set(rng.choice(len(U), na, replace=False).tolist())
        rb = set(rng.choice(len(U), nb, replace=False).tolist())
        if (jaccard(ra, rb) or 0.0) >= j0:
            ge += 1
    return j0, (ge + 1) / (n_perm + 1)
