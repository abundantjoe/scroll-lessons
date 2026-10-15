"""P4-H crackle channel (RULES.md DECL-P4-9 item 1), shared by the gate, the builder and the tests.

Provenance: Project HERCULES | owner the owner | [id removed]

Numbers only: no image, tile or CT pixel is ever displayed or printed.

Channel, fixed by DECL-P4-9 item 1:
- level 0 of the 1.129 um surface volume (2.258 um in-plane and depth), slices within +-20 um of the
  mesh surface: centre 58 = n//2 of 116, |k| <= 8 (8 x 2.258 = 18.06 um), slices 50..66;
- per slice DoG = G(sigma 1.5 px) - G(sigma 6 px), squared; mean over the 17 slices;
- area average (cv2.INTER_AREA) of the T x T tile to the 1068 px display grid (18.7 um);
- DECL-P4-5-A1 stretch (builder.linear_window_ct over mesh-valid px with CT > 0), 0 elsewhere.
"""
import concurrent.futures as cf
import hashlib
import math
import time

import cv2
import numpy as np
import requests

BUCKET = "https://vesuvius-challenge-open-data.s3.amazonaws.com"
N_SLICES, CENTRE, HALF = 116, 58, 8
SL0, SL1 = CENTRE - HALF, CENTRE + HALF + 1  # 50..66 inclusive
SIG1, SIG2 = 1.5, 6.0
HALO = 32  # >= 4 * SIG2 = 24 px, so no tile-edge effect
CH = 128
PLANE = CH * CH
OUT_SIDE = 1068
POS_EPS = 1e-6

_S = requests.Session()
_S.mount("https://", requests.adapters.HTTPAdapter(pool_connections=96, pool_maxsize=96))


def ksize(sig):
    return 2 * int(math.ceil(4 * sig)) + 1


def dog_energy(stack):
    """stack: (n, h, w) array. Returns float32 (h, w) mean over slices of (G1.5 - G6)^2."""
    acc = np.zeros(stack.shape[1:], np.float32)
    k1, k2 = ksize(SIG1), ksize(SIG2)
    for s in stack:
        f = s.astype(np.float32)
        d = cv2.GaussianBlur(f, (k1, k1), SIG1, borderType=cv2.BORDER_REFLECT)
        d -= cv2.GaussianBlur(f, (k2, k2), SIG2, borderType=cv2.BORDER_REFLECT)
        cv2.accumulateSquare(d, acc)
    acc /= float(stack.shape[0])
    return acc


def _get(url, rng, tries=7):
    for i in range(tries):
        try:
            r = _S.get(url, headers={"Range": rng} if rng else None, timeout=120)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.content
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 ** (i + 1))


def chunk_slices(sv_key, cy, cx):
    """Slices SL0..SL1-1 of chunk (cy, cx) via an HTTP Range read; None if the chunk is absent."""
    b = _get(f"{BUCKET}/{sv_key}/0/0/{cy}/{cx}", f"bytes={SL0 * PLANE}-{SL1 * PLANE - 1}")
    if b is None:
        return None
    assert len(b) == (SL1 - SL0) * PLANE, (cy, cx, len(b))
    return np.frombuffer(b, np.uint8).reshape(SL1 - SL0, CH, CH)


def verify_range_read(sv_key, cy, cx):
    """One full-chunk GET vs the Range read of the same chunk: the slab bytes must be identical."""
    full = _get(f"{BUCKET}/{sv_key}/0/0/{cy}/{cx}", None)
    part = _get(f"{BUCKET}/{sv_key}/0/0/{cy}/{cx}", f"bytes={SL0 * PLANE}-{SL1 * PLANE - 1}")
    if full is None:
        return {"chunk": [cy, cx], "absent": True}
    assert len(full) == N_SLICES * PLANE
    return {"chunk": [cy, cx], "full_sha256": hashlib.sha256(full).hexdigest(),
            "range_equal_full_slices": full[SL0 * PLANE:SL1 * PLANE] == part}


def fetch_slab(sv_key, H, W, y0, y1, x0, x1, threads=64):
    """uint8 (17, y1-y0, x1-x0) of L0 canvas region; zero outside the canvas and in absent chunks."""
    out = np.zeros((SL1 - SL0, y1 - y0, x1 - x0), np.uint8)
    cys = range(max(y0, 0) // CH, (min(y1, H) - 1) // CH + 1)
    cxs = range(max(x0, 0) // CH, (min(x1, W) - 1) // CH + 1)
    keys = [(cy, cx) for cy in cys for cx in cxs]
    n_abs = 0

    def job(k):
        return k, chunk_slices(sv_key, *k)

    with cf.ThreadPoolExecutor(threads) as ex:
        for (cy, cx), a in ex.map(job, keys):
            if a is None:
                n_abs += 1
                continue
            ay0, ax0 = cy * CH, cx * CH
            hh, ww = min(CH, H - ay0), min(CH, W - ax0)
            sy0, sy1 = max(y0, ay0), min(y1, ay0 + hh)
            sx0, sx1 = max(x0, ax0), min(x1, ax0 + ww)
            if sy1 > sy0 and sx1 > sx0:
                out[:, sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = a[:, sy0 - ay0:sy1 - ay0, sx0 - ax0:sx1 - ax0]
    return out, {"chunks": len(keys), "absent": n_abs}


def mesh_valid_canvas(grid_valid, s, y0, y1, x0, x1):
    """Canvas px (i, j) -> grid (i // s, j // s); outside the grid is not valid (M2b / E1 rule)."""
    gh, gw = grid_valid.shape
    ii = np.arange(y0, y1) // s
    jj = np.arange(x0, x1) // s
    m = np.zeros((y1 - y0, x1 - x0), bool)
    oi, oj = (ii >= 0) & (ii < gh), (jj >= 0) & (jj < gw)
    m[np.ix_(oi, oj)] = grid_valid[np.ix_(ii[oi], jj[oj])]
    return m


def fetch_tile(sv_key, H, W, T, r, c, threads=64):
    """L0 slab of tile (r, c) with a HALO px margin (uint8, 17 x (T+2H) x (T+2H))."""
    y0, x0 = r * T, c * T
    t0 = time.time()
    slab, finfo = fetch_slab(sv_key, H, W, y0 - HALO, y0 + T + HALO, x0 - HALO, x0 + T + HALO, threads)
    finfo["fetch_secs"] = round(time.time() - t0, 1)
    return slab, finfo


def compute_tile(slab, grid_valid, s, T, r, c):
    """Crackle channel of tile (r, c) from its slab. Returns (energy1068 float32, pos1068 bool,
    meshvalid1068 bool, info). Past the canvas: zero padded, not mesh-valid (M2b edge-tile rule)."""
    t1 = time.time()
    y0, x0 = r * T, c * T
    ctpos = slab[:, HALO:HALO + T, HALO:HALO + T].sum(0, dtype=np.uint32) > 0
    en = np.ascontiguousarray(dog_energy(slab)[HALO:HALO + T, HALO:HALO + T])
    mv = mesh_valid_canvas(grid_valid, s, y0, y0 + T, x0, x0 + T)
    e1068 = cv2.resize(en, (OUT_SIDE, OUT_SIDE), interpolation=cv2.INTER_AREA)
    posf = cv2.resize((mv & ctpos).astype(np.float32), (OUT_SIDE, OUT_SIDE), interpolation=cv2.INTER_AREA)
    mvf = cv2.resize(mv.astype(np.float32), (OUT_SIDE, OUT_SIDE), interpolation=cv2.INTER_AREA)
    nmv = int(mv.sum())
    info = dict(compute_secs=round(time.time() - t1, 1), valid_fraction_L0=float(mv.mean()),
                frac_valid_ct_zero_L0=float((mv & ~ctpos).sum() / max(1, nmv)))
    return e1068, posf >= 1 - POS_EPS, mvf >= 1 - POS_EPS, info


def display_u8(e1068, pos):
    """DECL-P4-5-A1 stretch over pos px; 0 elsewhere."""
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src"))
    from hercules.display.builder import linear_window_ct
    u8, (lo, hi) = linear_window_ct(e1068, pos)
    u8[~pos] = 0
    return u8, lo, hi


# ---------------- AUC helpers ----------------
def auc_hist(hi_, hb_):
    """Mann-Whitney AUC (ties 0.5) from integer-value histograms of ink and background."""
    hi_, hb_ = np.asarray(hi_, np.float64), np.asarray(hb_, np.float64)
    ni, nb = hi_.sum(), hb_.sum()
    if ni == 0 or nb == 0:
        return float("nan")
    below = np.concatenate([[0.0], np.cumsum(hb_)[:-1]])
    return float((hi_ * (below + 0.5 * hb_)).sum() / (ni * nb))


def auc_float(xi, xb):
    from scipy.stats import rankdata
    ni, nb = len(xi), len(xb)
    if ni == 0 or nb == 0:
        return float("nan")
    rk = rankdata(np.concatenate([xi, xb]))
    return float((rk[:ni].sum() - ni * (ni + 1) / 2.0) / (ni * nb))


def class_masks(pred, amask, p90, p50, px_um, excl_um=50.0):
    """ink = pred >= p90, bg = pred <= p50 within amask; keep px whose distance to the nearest
    non-class px (non-class includes px outside amask) is > excl_um."""
    from scipy.ndimage import distance_transform_edt
    ink = amask & (pred >= p90)
    bg = amask & (pred <= p50)
    # padded with non-class so the tile edge also counts as a boundary (conservative)
    dk = distance_transform_edt(np.pad(ink, 1))[1:-1, 1:-1] * px_um
    db = distance_transform_edt(np.pad(bg, 1))[1:-1, 1:-1] * px_um
    return ink & (dk > excl_um), bg & (db > excl_um)
