"""p4-purple-mo: colour-agnostic morphology features on the control strip (RULES.md DECL-P4-16 item 4).

Provenance: Project HERCULES | owner the owner | [id removed]

Protocol: logs/sib/p4-purple/mo/PROTOCOL.md (pushed at 7e8ab53 before any feature number).
Numbers only: CT chunks are streamed, reduced to per-cell numbers and discarded; nothing is displayed or printed.
Control strip 20260701183125-w028-037 ONLY. This module has no code path for any other segment.
"""
import concurrent.futures as cf
import hashlib
import io
import json
import os
import subprocess
import threading
import time
import zlib

import cv2
import numpy as np
import requests
from scipy.ndimage import gaussian_filter, gaussian_filter1d, gaussian_laplace, uniform_filter

PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
BUCKET = "https://vesuvius-challenge-open-data.s3.amazonaws.com"
SEG = "20260701183125-w028-037"
assert SEG.endswith("w028-037")  # fence: control strip only
SV = f"PHercParis4/segments/{SEG}/surface-volumes/2.4um-0.22m-78keV-volume-20260411134726.zarr"
PRED = (f"PHercParis4/segments/{SEG}/ink-detection/PHercParis4-20260701183125-2.4um-0.22m-78keV-volume-"
        "20260411134726-20260417190342-new_canon_autoresearch_recipe-tile256-stride128.tif")
MESH = f"PHercParis4/segments/{SEG}/mesh/20260701183125-on-20260411134726-2.4um.tifxyz"
TB = "origin/claude/gifted-bell-gavnl5-sib-p4-tiles-b"
NZ, CENTRE, UM = 109, 54, 2.4
H, W = 71600, 174640
T = 8301
CH = 128
GRID_S = 20
MAXOFF_UM = 120.0
DOG_S1, DOG_S2 = 1.5 * 2.258 / 2.4, 6.0 * 2.258 / 2.4
DEV = [(2, 3), (4, 6), (4, 17), (6, 9)]
GATE = [(0, 20), (1, 9), (2, 9), (2, 14), (2, 17), (3, 6), (3, 12), (3, 17), (4, 7), (5, 1), (5, 8), (5, 15),
        (5, 17), (6, 15), (7, 16), (7, 18)]

_tl = threading.local()


def _sess():
    s = getattr(_tl, "s", None)
    if s is None:
        s = _tl.s = requests.Session()
    return s


def get(url, rng=None, tries=7):
    h = {"Range": f"bytes={rng[0]}-{rng[1]}"} if rng else {}
    for i in range(tries):
        try:
            r = _sess().get(url, headers=h, timeout=120)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.content
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(min(30, 2 ** (i + 1)))


def git_bytes(ref_path, cwd=None):
    return subprocess.run(["git", "show", ref_path], capture_output=True, check=True, cwd=cwd).stdout


# ---------------------------------------------------------------- mesh validity (grid, 20 canvas px per vertex)
def mesh_valid_grid(scratch):
    p = os.path.join(scratch, "mesh_valid.npy")
    if os.path.exists(p):
        return np.load(p), json.load(open(p + ".json"))
    import tifffile
    v, rec = None, []
    for a in "xyz":
        b = get(f"{BUCKET}/{MESH}/{a}.tif")
        rec.append({"key": f"{MESH}/{a}.tif", "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
        x = tifffile.imread(io.BytesIO(b))
        del b
        m = (x != -1) & np.isfinite(x)
        del x
        v = m if v is None else (v & m)
    np.save(p, v)
    json.dump(rec, open(p + ".json", "w"))
    return v, rec


def valid4(vg, i0, i1, j0, j1):
    """mesh-valid of 9.6 um cells (4x4 px blocks) with block rows i0..i1-1, cols j0..j1-1 (a 4x4 block lies in one
    grid cell since 4 | 20); blocks beyond the canvas are invalid."""
    ii, jj = np.arange(i0, i1), np.arange(j0, j1)
    gi = np.minimum(ii * 4 // GRID_S, vg.shape[0] - 1)
    gj = np.minimum(jj * 4 // GRID_S, vg.shape[1] - 1)
    v = vg[gi][:, gj].copy()
    v &= ((ii * 4 + 4) <= H)[:, None] & ((jj * 4 + 4) <= W)[None, :]
    return v


# ---------------------------------------------------------------- chunk streaming
def fetch_window(cy0, cy1, cx0, cx1, threads=48):
    """uint8 (109, (cy1-cy0)*128, (cx1-cx0)*128) and a chunk-present mask."""
    ny, nx = cy1 - cy0, cx1 - cx0
    arr = np.zeros((NZ, ny * CH, nx * CH), np.uint8)
    present = np.zeros((ny, nx), bool)

    def job(k):
        a, b = k
        raw = get(f"{BUCKET}/{SV}/0/0/{cy0 + a}/{cx0 + b}")
        if raw is None:
            return
        assert len(raw) == NZ * CH * CH, len(raw)
        arr[:, a * CH:(a + 1) * CH, b * CH:(b + 1) * CH] = np.frombuffer(raw, np.uint8).reshape(NZ, CH, CH)
        present[a, b] = True

    with cf.ThreadPoolExecutor(threads) as ex:
        list(ex.map(job, [(a, b) for a in range(ny) for b in range(nx)]))
    return arr, present


# ---------------------------------------------------------------- profile and faces (PROTOCOL section 3)
def block_profile(arr):
    """4x4 px block mean per slice, smoothed along z with sigma 1 slice. -> float32 (109, ny, nx)."""
    z, y, x = arr.shape
    P = arr.reshape(z, y // 4, 4, x // 4, 4).mean(axis=(2, 4), dtype=np.float32)
    return gaussian_filter1d(P, 1.0, axis=0, mode="nearest").astype(np.float32)


def faces(P, tf, anchor=True):
    """P (109, ...) smoothed profile. Returns h_plus, h_minus (um from the mesh slice 54, positive outward, signed;
    NaN if missing), the sub-voxel crossings z_plus, z_minus (slice units) and the analysable mask.
    anchor=True: PROTOCOL amendment A1 (search outward from k* = argmax P over |k-54| <= 12);
    anchor=False: the original section 3 rule (search outward from slice 54)."""
    shp = P.shape[1:]
    P2 = P.reshape(NZ, -1)
    n = P2.shape[1]
    idx = np.arange(n)
    if anchor:
        ks = CENTRE - 12 + P2[CENTRE - 12:CENTRE + 13].argmax(0)
    else:
        ks = np.full(n, CENTRE)
    ok_c = P2[ks, idx] >= tf
    below = P2 < tf
    kk = np.arange(NZ)[:, None]
    # '+': first k > k* (k <= 107) with below[k] & below[k+1]
    cp = np.zeros_like(below)
    cp[:NZ - 1] = below[:NZ - 1] & below[1:]
    cp &= kk > ks[None, :]
    anyp = cp.any(0)
    kp = np.where(anyp, cp.argmax(0), CENTRE + 1)
    # '-': last k < k* (k >= 1) with below[k] & below[k-1]
    cm = np.zeros_like(below)
    cm[1:] = below[1:] & below[:NZ - 1]
    cm &= kk < ks[None, :]
    anym = cm.any(0)
    km = np.where(anym, NZ - 1 - cm[::-1].argmax(0), CENTRE - 1)
    a, b = P2[kp - 1, idx], P2[kp, idx]
    with np.errstate(invalid="ignore", divide="ignore"):
        zp = (kp - 1) + (a - tf) / np.where(a - b > 0, a - b, np.nan)
    a2, b2 = P2[km + 1, idx], P2[km, idx]
    with np.errstate(invalid="ignore", divide="ignore"):
        zm = (km + 1) - (a2 - tf) / np.where(a2 - b2 > 0, a2 - b2, np.nan)
    zp = np.where(ok_c & anyp, zp, np.nan)
    zm = np.where(ok_c & anym, zm, np.nan)
    hp = (zp - CENTRE) * UM
    hm = (CENTRE - zm) * UM
    with np.errstate(invalid="ignore"):
        okp, okm = np.abs(hp) <= MAXOFF_UM, np.abs(hm) <= MAXOFF_UM
    zp, hp = np.where(okp, zp, np.nan), np.where(okp, hp, np.nan)
    zm, hm = np.where(okm, zm, np.nan), np.where(okm, hm, np.nan)
    return (hp.reshape(shp).astype(np.float32), hm.reshape(shp).astype(np.float32),
            zp.reshape(shp).astype(np.float32), zm.reshape(shp).astype(np.float32), ok_c.reshape(shp))


def _ks(s):
    return 2 * int(np.ceil(3 * s)) + 1


def dog_energy_blocks(arr):
    """Per slice: DoG (sigma 1.411 / 5.645 px, BORDER_REFLECT), squared, 4x4 block mean. -> float32 (109, ny, nx)."""
    z, y, x = arr.shape
    out = np.empty((z, y // 4, x // 4), np.float32)
    k1, k2 = _ks(DOG_S1), _ks(DOG_S2)
    for k in range(z):
        s = arr[k].astype(np.float32)
        d = (cv2.GaussianBlur(s, (k1, k1), DOG_S1, borderType=cv2.BORDER_REFLECT)
             - cv2.GaussianBlur(s, (k2, k2), DOG_S2, borderType=cv2.BORDER_REFLECT))
        out[k] = (d * d).reshape(y // 4, 4, x // 4, 4).mean(axis=(1, 3))
    return out


def energy_at(E, z):
    """Mean of E over slices round(z)-4..round(z)+4 (clipped to 0..108) per cell; NaN where z is NaN."""
    E2 = E.reshape(NZ, -1)
    zz = z.reshape(-1)
    ok = np.isfinite(zz)
    zc = np.where(ok, np.rint(zz), CENTRE).astype(int)
    cs = np.concatenate([np.zeros((1, E2.shape[1]), np.float64), np.cumsum(E2, 0, dtype=np.float64)], 0)
    lo = np.clip(zc - 4, 0, NZ - 1)
    hi = np.clip(zc + 4, 0, NZ - 1) + 1
    idx = np.arange(E2.shape[1])
    m = (cs[hi, idx] - cs[lo, idx]) / (hi - lo)
    return np.where(ok, m, np.nan).reshape(z.shape).astype(np.float32)


# ---------------------------------------------------------------- features (PROTOCOL section 4), 9.6 um grid
def nconv_gauss(v, sigma):
    m = np.isfinite(v)
    a = gaussian_filter(np.where(m, v, 0).astype(np.float64), sigma, mode="constant")
    b = gaussian_filter(m.astype(np.float64), sigma, mode="constant")
    with np.errstate(invalid="ignore", divide="ignore"):
        return a / b


def features(hp, hm, ep, em, cell_um=9.6):
    s_tr = 500.0 / cell_um
    s_lg = 150.0 / cell_um
    F = {}
    res = {}
    for nm, h in (("+", hp), ("-", hm)):
        m = np.isfinite(h)
        tr = nconv_gauss(h, s_tr)
        r = np.where(m, h - tr, np.nan)
        res[nm] = r
        F["F1" + nm] = r
        hf = np.where(m, h, tr)
        hf = np.where(np.isfinite(hf), hf, np.nanmean(h) if m.any() else 0.0)
        F["F3" + nm] = np.where(m, s_lg ** 2 * gaussian_laplace(hf.astype(np.float64), s_lg, mode="nearest"), np.nan)
        rm = np.where(m, r, 0.0)
        mf = m.astype(np.float64)
        n = uniform_filter(mf, 11, mode="constant") * 121
        s1 = uniform_filter(rm, 11, mode="constant") * 121
        s2 = uniform_filter(rm * rm, 11, mode="constant") * 121
        with np.errstate(invalid="ignore", divide="ignore"):
            var = (s2 - s1 * s1 / n) / (n - 1)
        F["F4" + nm] = np.where(m & (np.rint(n) >= 61), np.sqrt(np.maximum(var, 0)), np.nan)
    t = hp + hm
    F["F2"] = np.where(np.isfinite(t), t - nconv_gauss(t, s_tr), np.nan)
    F["F5+"] = ep
    F["F5-"] = em
    return {k: v.astype(np.float32) for k, v in F.items()}


def pool2(v):
    """9.6 um -> 19.2 um: mean of 2x2 children, finite only if all 4 are finite."""
    y, x = v.shape
    return v[:y // 2 * 2, :x // 2 * 2].reshape(y // 2, 2, x // 2, 2).mean(axis=(1, 3))


# ---------------------------------------------------------------- tile geometry (19.2 um cells I, 9.6 um cells i)
def tile_cells(r, c):
    I0, I1 = -(-(r * T) // 8), min((r + 1) * T, H) // 8
    J0, J1 = -(-(c * T) // 8), min((c + 1) * T, W) // 8
    return I0, I1, J0, J1


# ---------------------------------------------------------------- prediction TIFF, range reads
class PredTiff:
    def __init__(self):
        import tifffile

        class RF(io.RawIOBase):
            def __init__(s, url, size):
                s.url, s.size, s.pos = url, size, 0

            def seekable(s):
                return True

            def readable(s):
                return True

            def seek(s, off, wh=0):
                s.pos = off if wh == 0 else (s.pos + off if wh == 1 else s.size + off)
                return s.pos

            def tell(s):
                return s.pos

            def readinto(s, b):
                n = min(len(b), s.size - s.pos)
                if n <= 0:
                    return 0
                d = get(s.url, (s.pos, s.pos + n - 1))
                b[:len(d)] = d
                s.pos += len(d)
                return len(d)

        url = f"{BUCKET}/{PRED}"
        size = int(requests.head(url, timeout=60).headers["Content-Length"])
        assert size == 1207687349, size
        self.url = url
        tf = tifffile.TiffFile(io.BufferedReader(RF(url, size), 1 << 20))
        pg = tf.pages[0]
        assert pg.shape == (H, W) and pg.dtype == np.uint8 and pg.is_tiled and pg.compression == 32946
        assert (pg.tilelength, pg.tilewidth) == (1024, 1024) and pg.predictor == 1
        self.off = np.asarray(pg.dataoffsets, np.int64)
        self.cnt = np.asarray(pg.databytecounts, np.int64)
        self.ntx = -(-W // 1024)
        self._cache = {}

    def tile(self, ty, tx):
        k = (ty, tx)
        if k not in self._cache:
            i = ty * self.ntx + tx
            b = get(self.url, (int(self.off[i]), int(self.off[i] + self.cnt[i] - 1)))
            self._cache[k] = np.frombuffer(zlib.decompress(b), np.uint8).reshape(1024, 1024)
        return self._cache[k]

    def region_mean8(self, I0, I1, J0, J1):
        """Mean of 8x8 px per 19.2 um cell for cells I0..I1-1, J0..J1-1 (float32)."""
        y0, y1, x0, x1 = I0 * 8, I1 * 8, J0 * 8, J1 * 8
        out = np.zeros((y1 - y0, x1 - x0), np.uint8)
        tys = range(y0 // 1024, (y1 - 1) // 1024 + 1)
        txs = range(x0 // 1024, (x1 - 1) // 1024 + 1)
        keys = [(a, b) for a in tys for b in txs]
        with cf.ThreadPoolExecutor(16) as ex:
            list(ex.map(lambda k: self.tile(*k), keys))
        for a, b in keys:
            t = self.tile(a, b)
            ya, yb = max(y0, a * 1024), min(y1, (a + 1) * 1024)
            xa, xb = max(x0, b * 1024), min(x1, (b + 1) * 1024)
            out[ya - y0:yb - y0, xa - x0:xb - x0] = t[ya - a * 1024:yb - a * 1024, xa - b * 1024:xb - b * 1024]
        self._cache.clear()
        return out.reshape(I1 - I0, 8, J1 - J0, 8).mean(axis=(1, 3), dtype=np.float32)


# ---------------------------------------------------------------- statistics
def auc_float(xi, xb):
    from scipy.stats import rankdata
    ni, nb = len(xi), len(xb)
    if ni == 0 or nb == 0:
        return float("nan")
    rk = rankdata(np.concatenate([xi, xb]))
    return float((rk[:ni].sum() - ni * (ni + 1) / 2.0) / (ni * nb))


def auc_hist(hi_, hb_):
    hi_, hb_ = np.asarray(hi_, np.float64), np.asarray(hb_, np.float64)
    ni, nb = hi_.sum(), hb_.sum()
    if ni == 0 or nb == 0:
        return float("nan")
    cb = np.cumsum(hb_) - hb_
    return float((hi_ * (cb + 0.5 * hb_)).sum() / (ni * nb))


def class_masks(pred, amask, p90, p50, px_um=19.2, excl_um=50.0):
    """p4-crackle class_masks (DECL-P4-9 recipe) on the 19.2 um cell grid."""
    from scipy.ndimage import distance_transform_edt
    ink = amask & (pred >= p90)
    bg = amask & (pred <= p50)
    dk = distance_transform_edt(np.pad(ink, 1))[1:-1, 1:-1] * px_um
    db = distance_transform_edt(np.pad(bg, 1))[1:-1, 1:-1] * px_um
    return ink & (dk > excl_um), bg & (db > excl_um)


def tface_from_hist(h):
    """PROTOCOL 3.2: midpoint of the two highest local maxima >= 20 levels apart (histogram smoothed sigma 2 bins);
    else Otsu."""
    hs = gaussian_filter1d(np.asarray(h, np.float64), 2.0, mode="nearest")
    loc = [k for k in range(1, 255) if hs[k] > hs[k - 1] and hs[k] >= hs[k + 1]]
    loc.sort(key=lambda k: -hs[k])
    if loc:
        a = loc[0]
        for b in loc[1:]:
            if abs(b - a) >= 20:
                return {"rule": "mode_midpoint", "modes": sorted([int(a), int(b)]), "T_face": (a + b) / 2.0,
                        "mode_heights": [float(hs[min(a, b)]), float(hs[max(a, b)])]}
    p = np.asarray(h, np.float64) / max(1, np.sum(h))
    om = np.cumsum(p)
    mu = np.cumsum(p * np.arange(256))
    with np.errstate(invalid="ignore", divide="ignore"):
        sb = (mu[-1] * om - mu) ** 2 / (om * (1 - om))
    t = int(np.nanargmax(sb))
    return {"rule": "otsu", "T_face": t + 0.5}
