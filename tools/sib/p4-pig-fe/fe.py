"""p4-pig-fe: weak-contrast FE-family (ochre / green earth) detector (RULES.md DECL-P4-10, family FE).

Provenance: Project HERCULES | owner the owner | [id removed]

Numbers only. CT bytes are reduced to clipped band excesses, block means, filter responses and scores. Nothing is
displayed, printed as an image, or written as an image.

Detector (parameters in logs/sib/p4-pig-fe/params.json):
  per voxel   x = clip(v, B_lo, B_hi) - B_lo                       (intensity band, clipped excess)
  per px      e = mean_S(x) - mean_I(x)                            (recto surface layer minus sheet interior)
  per block   block mean of e over valid px (8x8 px at 2.258 um = 18.06 um; 4x4 px at 4.8 um = 19.2 um)
  stroke MF   r = mean(e, bar) - mean(e, flanks); bar 0.45 x 1.8 mm, flanks 0.45 mm each side; 4 orientations
  z           r / sigma0 (sigma0 = 1.4826 MAD of r over the control strip); tile score = max z
"""
import concurrent.futures as cf
import hashlib
import json
import os
import subprocess
import threading
import time

import cv2
import numpy as np
import requests

PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
BUCKET = "https://vesuvius-challenge-open-data.s3.amazonaws.com"
HERE = os.path.dirname(os.path.abspath(__file__))
PARAMS = os.path.join(HERE, "..", "..", "..", "logs", "sib", "p4-pig-fe", "params.json")

# Material geometry (fixed; see params.json "materials").
MAT = {
    "E1": {"seg": "20260623141924-w010-027", "sv": "1.129um-0.23m-78keV-volume-20260608103018-L1.zarr", "level": 0,
           "um_z": 2.258, "um_xy": 2.258, "centre": 58, "blk": 8, "family": "1129"},
    "C": {"seg": "20260623142658-w028-037", "sv": "1.129um-0.23m-78keV-volume-20260608103018-L1.zarr", "level": 0,
          "um_z": 2.258, "um_xy": 2.258, "centre": 58, "blk": 8, "family": "1129"},
    "E2": {"seg": "20260701183124-w010-027", "sv": "2.4um-0.22m-78keV-volume-20260411134726.zarr", "level": 1,
           "um_z": 2.4, "um_xy": 4.8, "centre": 54, "blk": 4, "family": "24"},
    "C2": {"seg": "20260701183125-w028-037", "sv": "2.4um-0.22m-78keV-volume-20260411134726.zarr", "level": 1,
           "um_z": 2.4, "um_xy": 4.8, "centre": 54, "blk": 4, "family": "24"},
}
CH = 128
PLANE = CH * CH

_tl = threading.local()


def session():
    s = getattr(_tl, "s", None)
    if s is None:
        s = _tl.s = requests.Session()
    return s


def get(url, rng=None, tries=7):
    h = {"Range": f"bytes={rng[0]}-{rng[1]}"} if rng else {}
    for i in range(tries):
        try:
            r = session().get(url, headers=h, timeout=120)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.content
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(min(30, 2 ** (i + 1)))


def url_level(name):
    """Prefix of the level's arrays: .zarray at <prefix>/.zarray, chunks at <prefix>/0/<y>/<x> (z-chunk 0)."""
    m = MAT[name]
    return f"{BUCKET}/PHercParis4/segments/{m['seg']}/surface-volumes/{m['sv']}/{m['level']}"


def url_chunks(name):
    return url_level(name) + "/0"


def bands(name):
    """Slice index ranges [lo, hi) for S (recto surface layer), I (interior), D (deep null), and the fetch range."""
    m = MAT[name]
    c = m["centre"]
    n20 = int(np.floor(20.5 / m["um_z"]))           # 9 slices at 2.258 um (20.3 um); 8 at 2.4 um (19.2 um)
    n7 = int(np.ceil(6.5 / m["um_z"]))              # 3 slices (6.8 / 7.2 um)
    n40 = int(np.floor(41.0 / m["um_z"]))           # 18 (40.6 um) / 17 (40.8 um)
    S = (c, c + n20 + 1)
    I = (c - n20, c - n7 + 1)
    D = (c - n40, c - n20)
    F = (D[0], S[1])
    return {"S": S, "I": I, "D": D, "F": F}


def load_params():
    return json.load(open(PARAMS))


def reduce_chunk(a, B_lo, B_hi, bd, blk, mesh=None):
    """a: (nF, 128, 128) uint8 over the fetch range. Returns per-block sums (e, s, d) and valid px counts.

    A px is valid if (mesh is None or mesh) and no voxel in F is 0 (0 = outside scan / masked / absent)."""
    F0 = bd["F"][0]
    ok = (a > 0).all(0)
    if mesh is not None:
        ok &= mesh
    x = np.clip(a, B_lo, B_hi).astype(np.float32) - np.float32(B_lo)
    sl = lambda r: x[r[0] - F0:r[1] - F0].mean(0)
    s, i, d = sl(bd["S"]), sl(bd["I"]), sl(bd["D"])
    e = s - i
    okf = ok.astype(np.float32)
    nb = CH // blk
    bs = lambda q: (q * okf).reshape(nb, blk, nb, blk).sum((1, 3))
    return bs(e), bs(s), bs(d), okf.reshape(nb, blk, nb, blk).sum((1, 3))


# ---------------- matched filter ----------------

def bar_kernels(blk_um, width_mm, length_mm, flank_mm):
    """Bar and flank masks (float32, normalised to sum 1) at orientations 0, 45, 90, 135 degrees."""
    w, L, f = width_mm * 1000 / blk_um, length_mm * 1000 / blk_um, flank_mm * 1000 / blk_um
    R = int(np.ceil(np.hypot(L / 2, w / 2 + f))) + 1
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float64)
    out = []
    for ang in (0, 45, 90, 135):
        t = np.deg2rad(ang)
        u = xx * np.cos(t) + yy * np.sin(t)      # along the bar
        v = -xx * np.sin(t) + yy * np.cos(t)     # across the bar
        along = np.abs(u) <= L / 2
        bar = (along & (np.abs(v) <= w / 2)).astype(np.float32)
        fl = (along & (np.abs(v) > w / 2) & (np.abs(v) <= w / 2 + f)).astype(np.float32)
        out.append((ang, bar, fl))
    return out


def mf_response(E, V, kernels, min_bar_valid=0.8, min_flank_valid=0.5):
    """E: block sums of e over valid px; V: valid px count per block. Returns max-over-orientation response map
    r = mean(e | bar) - mean(e | flanks), weighted by valid px, NaN where coverage is insufficient; and the
    argmax orientation index."""
    E = E.astype(np.float32)
    V = V.astype(np.float32)
    Vb = (V > 0).astype(np.float32)
    best = np.full(E.shape, -np.inf, np.float32)
    arg = np.zeros(E.shape, np.int8)
    for k, (ang, bar, fl) in enumerate(kernels):
        f2 = lambda img, ker: cv2.filter2D(img, cv2.CV_32F, ker, borderType=cv2.BORDER_CONSTANT)
        nb, vb = f2(E, bar), f2(V, bar)
        nf, vf = f2(E, fl), f2(V, fl)
        cb, cf_ = f2(Vb, bar) / bar.sum(), f2(Vb, fl) / fl.sum()
        with np.errstate(invalid="ignore", divide="ignore"):
            r = nb / vb - nf / vf
        r[(cb < min_bar_valid) | (cf_ < min_flank_valid) | (vb <= 0) | (vf <= 0)] = -np.inf
        upd = r > best
        best[upd] = r[upd]
        arg[upd] = k
    best[~np.isfinite(best)] = np.nan
    return best, arg


# ---------------- misc ----------------

def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git_show(ref, path):
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=os.path.join(HERE, "..", "..", ".."))


def hist_pct(h, q):
    c = np.cumsum(h, dtype=np.float64)
    return int(np.searchsorted(c, q * c[-1], side="left"))
