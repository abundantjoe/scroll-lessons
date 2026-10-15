# Provenance: Project HERCULES | owner the owner | [id removed]
"""Task pairs0814 stage A (DECL-D2 pairs, PHerc0814): per organizer segment, fetch the 9.362 um and 2.399 um
tifxyz meshes and the official 2.399 um ink map, and fit the 2-D canvas affine c9 = M c2 + t "from meshes in both
frames". Numbers only; the ink map is read as an array and never displayed.

Correspondence: every k-th valid vertex of the 2.399 um mesh (3-D point q2, 2.399 um volume voxels) is mapped into
the 9.362 um volume by the organizer landmark affine of the root index (20260309142202 -> 20250804134230), then
projected onto the 9.362 um mesh surface (nearest vertex, then Gauss-Newton on the bilinear surface). Grid
coordinates become canvas pixels by the renderer's rule P = g / s - 0.5 (src/hercules/pipeline/canvas.py).
The affine is fitted by least squares with 3 rounds of 4-MAD trimming. Reported: residuals (9 um px), the
normal (off-surface) distance of the mapped 2.4 um points (9 um voxels), quadrant biases, and the difference from
the separable rule c9 = (c2 + 10.5) N9/N2 - 10.5 used for PHerc0841.

Then ref9 = the ink map area-averaged onto the 9 um canvas (exact integral-image average over the mapped pixel
footprint's bounding rectangle, piecewise-constant pixels), cov9 = fraction of that footprint covered by valid
2.4 um canvas pixels (nearest-vertex rule), both stored as npy on local disk.

Usage: stage_a.py SEG_ID|all
"""
import hashlib
import json
import os
import subprocess
import sys
import time

import numpy as np
import tifffile
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
from hercules.geometry.tifxyz import read_tifxyz, valid_mask  # noqa: E402

B = "https://vesuvius-challenge-open-data.s3.amazonaws.com"
SC = "PHerc0814"
V9, V2 = "20250804134230", "20260309142202"
WORK = "/work/sib/seg"
OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "logs", "sib", "pairs0814", "stage_a"))
ROOT_INDEX = "/work/sib/meta/root_metadata.json"
TARGET_PTS = 250_000


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def fetch(key, dst):
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    for i in range(5):
        r = subprocess.run(["curl", "-sSf", "-o", dst + ".part", f"{B}/{key}"])
        if r.returncode == 0:
            os.replace(dst + ".part", dst)
            return
        time.sleep(2 ** (i + 1))
    raise RuntimeError(f"fetch failed: {key}")


def index_affine():
    d = json.load(open(ROOT_INDEX))["samples"][SC]["sample"]["properties"]["volume_transforms"]
    for vt in d:
        if vt["from_volume_id"] == V2:
            for t in vt["transforms"]:
                if t["to_volume_id"] == V9:
                    return np.array(t["matrix"], float), t["derivation_path"]
    raise KeyError("affine not found")


def bilinear_eval(P, r, c):
    """Surface point and derivatives of the bilinear grid P (H, W, 3) at (r, c); r, c inside [0, H-1] x [0, W-1]."""
    H, W = P.shape[:2]
    j = np.clip(np.floor(r).astype(np.int64), 0, H - 2)
    i = np.clip(np.floor(c).astype(np.int64), 0, W - 2)
    t = (r - j)[:, None]
    s = (c - i)[:, None]
    p00, p01, p10, p11 = P[j, i], P[j, i + 1], P[j + 1, i], P[j + 1, i + 1]
    S = (1 - s) * (1 - t) * p00 + s * (1 - t) * p01 + (1 - s) * t * p10 + s * t * p11
    dc = (1 - t) * (p01 - p00) + t * (p11 - p10)
    dr = (1 - s) * (p10 - p00) + s * (p11 - p01)
    return S, dr, dc, j, i


def project(P9, q):
    """Project 3-D points q onto the 9 um mesh; returns (r, c, dist, ok)."""
    H, W = P9.shape[:2]
    v = valid_mask(P9)
    qv = np.zeros((H - 1, W - 1), bool)
    qv[:] = v[:-1, :-1] & v[1:, :-1] & v[:-1, 1:] & v[1:, 1:]
    rr, cc = np.nonzero(v)
    tree = cKDTree(P9[rr, cc].astype(np.float64))
    _, k = tree.query(q, k=1, workers=3)
    r = rr[k].astype(np.float64)
    c = cc[k].astype(np.float64)
    P = P9.astype(np.float64)
    for _ in range(8):
        r = np.clip(r, 0, H - 1)
        c = np.clip(c, 0, W - 1)
        S, dr, dc, _, _ = bilinear_eval(P, r, c)
        e = q - S
        a11 = (dr * dr).sum(1); a12 = (dr * dc).sum(1); a22 = (dc * dc).sum(1)
        b1 = (dr * e).sum(1); b2 = (dc * e).sum(1)
        det = a11 * a22 - a12 * a12
        det = np.where(np.abs(det) < 1e-12, np.nan, det)
        r = r + (a22 * b1 - a12 * b2) / det
        c = c + (a11 * b2 - a12 * b1) / det
    inside = np.isfinite(r) & np.isfinite(c) & (r >= 0) & (r <= H - 1) & (c >= 0) & (c <= W - 1)
    r2 = np.where(inside, r, 0.0); c2 = np.where(inside, c, 0.0)
    S, dr, dc, j, i = bilinear_eval(P, r2, c2)
    e = q - S
    n = np.cross(dc, dr)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    tang = np.linalg.norm(e - (e * n).sum(1, keepdims=True) * n, axis=1)
    ok = inside & qv[j, i] & (tang < 0.05)
    return r, c, np.abs((e * n).sum(1)), ok


def fit_affine(src, dst, rounds=3):
    keep = np.ones(len(src), bool)
    X = np.c_[src, np.ones(len(src))]
    for _ in range(rounds + 1):
        A, *_ = np.linalg.lstsq(X[keep], dst[keep], rcond=None)
        res = np.linalg.norm(X @ A - dst, axis=1)
        med = np.median(res[keep]); mad = np.median(np.abs(res[keep] - med)) + 1e-9
        keep = res <= med + 4 * 1.4826 * mad
    return A.T, res, keep  # (2, 3): [x9, y9] = A @ [x2, y2, 1]


def area_average(img, valid_rows, A, shape9, band=64):
    """Integral-image average of img (and of valid) over each 9 um pixel's footprint in the 2.4 um canvas."""
    M, t = A[:, :2], A[:, 2]
    Mi = np.linalg.inv(M)
    ti = -Mi @ t
    hx = 0.5 * (abs(Mi[0, 0]) + abs(Mi[0, 1]))
    hy = 0.5 * (abs(Mi[1, 0]) + abs(Mi[1, 1]))
    H9, W9 = shape9
    H2, W2 = img.shape[:2]
    ref = np.zeros(shape9, np.float32)
    cov = np.zeros(shape9, np.float32)
    xs = np.arange(W9, dtype=np.float64)
    for y0 in range(0, H9, band):
        ys = np.arange(y0, min(H9, y0 + band), dtype=np.float64)
        X, Y = np.meshgrid(xs, ys)
        cx = Mi[0, 0] * X + Mi[0, 1] * Y + ti[0]
        cy = Mi[1, 0] * X + Mi[1, 1] * Y + ti[1]
        x0, x1 = cx - hx, cx + hx
        yA, yB = cy - hy, cy + hy
        rlo = int(max(0, np.floor(np.nanmin(yA)) - 2)); rhi = int(min(H2, np.ceil(np.nanmax(yB)) + 3))
        if rhi <= rlo:
            continue
        for src, dst in ((None, ref), (valid_rows, cov)):
            blk = (np.asarray(img[rlo:rhi], np.float64) if src is None else src(rlo, rhi).astype(np.float64))
            I = np.zeros((blk.shape[0] + 1, W2 + 1))
            I[1:, 1:] = blk.cumsum(0).cumsum(1)

            def Ival(xx, yy):
                # integral over [-0.5, xx] x [-0.5, yy] of the piecewise-constant image (pixel k on [k-.5, k+.5))
                u = np.clip(xx + 0.5, 0, W2); v = np.clip(yy + 0.5 - rlo, 0, rhi - rlo)
                u0 = np.floor(u).astype(np.int64); v0 = np.floor(v).astype(np.int64)
                u1 = np.minimum(u0 + 1, W2); v1 = np.minimum(v0 + 1, rhi - rlo)
                fu = u - u0; fv = v - v0
                return ((1 - fu) * (1 - fv) * I[v0, u0] + fu * (1 - fv) * I[v0, u1]
                        + (1 - fu) * fv * I[v1, u0] + fu * fv * I[v1, u1])
            s = Ival(x1, yB) - Ival(x0, yB) - Ival(x1, yA) + Ival(x0, yA)
            dst[y0:y0 + len(ys)] = (s / ((x1 - x0) * (yB - yA))).astype(np.float32)
    return ref, cov


class TiledRows:
    """Row-band reader of a tiled single-page uint8 TIFF (decodes only the tiles a band touches)."""

    def __init__(self, path):
        self.tf = tifffile.TiffFile(path)
        self.pg = self.tf.pages[0]
        assert self.pg.is_tiled and self.pg.samplesperpixel == 1, "expected a tiled single-sample page"
        self.shape = self.pg.shape
        self.dtype = self.pg.dtype
        self.th, self.tw = self.pg.tilelength, self.pg.tilewidth
        self.nx = -(-self.shape[1] // self.tw)
        self.fh = self.tf.filehandle

    def __getitem__(self, sl):
        a, b = sl.start or 0, min(sl.stop, self.shape[0])
        out = np.zeros((b - a, self.shape[1]), self.dtype)
        for ty in range(a // self.th, -(-b // self.th)):
            for tx in range(self.nx):
                k = ty * self.nx + tx
                off, n = self.pg.dataoffsets[k], self.pg.databytecounts[k]
                if n == 0:
                    continue
                self.fh.seek(off)
                tile, _, _ = self.pg.decode(self.fh.read(n), k)
                tile = np.asarray(tile).reshape(-1, self.th, self.tw)[0] if np.asarray(tile).ndim != 2 else tile
                y0, x0 = ty * self.th, tx * self.tw
                ya, yb = max(a, y0), min(b, y0 + self.th)
                xb = min(self.shape[1], x0 + self.tw)
                out[ya - a:yb - a, x0:xb] = tile[ya - y0:yb - y0, :xb - x0]
        return out


def canvas_valid(P, scale, shape, rows=None):
    """Renderer rule: canvas pixel valid iff its nearest grid vertex is valid and not on the grid border / next to
    an invalid N/S/E/W neighbour (normal defined)."""
    v = valid_mask(P)
    nv = v.copy()
    nv[0, :] = nv[-1, :] = nv[:, 0] = nv[:, -1] = False
    nv[1:-1, 1:-1] &= v[:-2, 1:-1] & v[2:, 1:-1] & v[1:-1, :-2] & v[1:-1, 2:]
    Hc, Wc = shape
    rr = np.arange(Hc) if rows is None else np.arange(rows[0], rows[1])
    gr = np.rint((rr + 0.5) * scale[1]).astype(np.int64).clip(0, P.shape[0] - 1)
    gc = np.rint((np.arange(Wc) + 0.5) * scale[0]).astype(np.int64).clip(0, P.shape[1] - 1)
    return nv[np.ix_(gr, gc)]


def run(seg):
    sid = seg.split("-", 1)[0]
    d = f"{WORK}/{sid}"
    os.makedirs(d, exist_ok=True)
    pre = f"{SC}/segments/{seg}"
    files = {}
    for tag, vol, um in (("mesh9", V9, "9.362um"), ("mesh24", V2, "2.399um")):
        for f in ("x.tif", "y.tif", "z.tif", "meta.json"):
            key = f"{pre}/mesh/{sid}-on-{vol}-{um}.tifxyz/{f}"
            fetch(key, f"{d}/{tag}/{f}")
            files[key] = sha256(f"{d}/{tag}/{f}")
    inkkey = (f"{pre}/ink-detection/{SC}-{sid}-2.399um-0.22m-78keV-volume-{V2}-20260417190342-"
              f"new_canon_autoresearch_recipe-tile256-stride128.tif")
    fetch(inkkey, f"{d}/ink24.tif")
    files[inkkey] = sha256(f"{d}/ink24.tif")
    m9 = read_tifxyz(f"{d}/mesh9")
    m2 = read_tifxyz(f"{d}/mesh24")
    A3, path = index_affine()
    v2 = valid_mask(m2.points)
    k = max(1, int(np.sqrt(v2.sum() / TARGET_PTS)))
    rr, cc = np.nonzero(v2[::k, ::k])
    rr *= k; cc *= k
    q2 = m2.points[rr, cc].astype(np.float64)
    q9 = q2 @ A3[:, :3].T + A3[:, 3]
    r9, c9, dn, ok = project(m9.points, q9)
    s2 = 1.0 / np.float32(m2.scale[0]), 1.0 / np.float32(m2.scale[1])
    s9 = 1.0 / np.float32(m9.scale[0]), 1.0 / np.float32(m9.scale[1])
    src = np.c_[cc[ok] * s2[0] - 0.5, rr[ok] * s2[1] - 0.5]          # 2.4 um canvas (x, y)
    dst = np.c_[c9[ok] * s9[0] - 0.5, r9[ok] * s9[1] - 0.5]          # 9 um canvas (x, y)
    A, res, keep = fit_affine(src, dst)
    H9, W9 = int(round(m9.points.shape[0] * s9[1])), int(round(m9.points.shape[1] * s9[0]))
    H2, W2 = int(round(m2.points.shape[0] * s2[1])), int(round(m2.points.shape[1] * s2[0]))
    # separable 0841 rule for comparison
    sep = np.c_[(src[:, 0] + 10.5) * W9 / W2 - 10.5, (src[:, 1] + 10.5) * H9 / H2 - 10.5]
    sep_res = np.linalg.norm(sep - dst, axis=1)
    # quadrant biases of the affine residual vector
    rv = (np.c_[src, np.ones(len(src))] @ A.T) - dst
    qb = {}
    mx, my = np.median(src[:, 0]), np.median(src[:, 1])
    for nm, m in (("x<med,y<med", (src[:, 0] < mx) & (src[:, 1] < my)), ("x>=med,y<med", (src[:, 0] >= mx) & (src[:, 1] < my)),
                  ("x<med,y>=med", (src[:, 0] < mx) & (src[:, 1] >= my)), ("x>=med,y>=med", (src[:, 0] >= mx) & (src[:, 1] >= my))):
        qb[nm] = [float(np.median(rv[m, 0])), float(np.median(rv[m, 1]))] if m.any() else None
    # labels onto the 9 um canvas
    ink = TiledRows(f"{d}/ink24.tif")
    assert tuple(ink.shape) == (H2, W2) and ink.dtype == np.uint8, (ink.shape, ink.dtype, (H2, W2))
    val2 = lambda a, b: canvas_valid(m2.points, m2.scale, (H2, W2), rows=(a, b))
    ref9, cov9 = area_average(ink, val2, A, (H9, W9))
    np.save(f"{d}/ref9.npy", np.clip(np.rint(ref9), 0, 255).astype(np.uint8))
    np.save(f"{d}/cov9.npy", np.clip(np.rint(cov9 * 255), 0, 255).astype(np.uint8))
    val9 = canvas_valid(m9.points, m9.scale, (H9, W9))
    np.save(f"{d}/val9.npy", val9)
    both = val9 & (cov9 >= 0.999)
    q = lambda a, p: float(np.percentile(a, p))
    out = dict(
        provenance="Project HERCULES | owner the owner | [id removed]", segment=seg,
        utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), files_sha256=files,
        index_affine_2p399_to_9p362=A3.tolist(), index_affine_path=path,
        n_trimmed_outliers=int(ok.sum() - keep.sum()), n_unprojected=int(len(q2) - ok.sum()),
        mesh9_grid=list(m9.points.shape[:2]), mesh24_grid=list(m2.points.shape[:2]), scale9=list(m9.scale),
        scale24=list(m2.scale), canvas9_hw=[H9, W9], canvas24_hw=[H2, W2], ink24_dtype=str(ink.dtype),
        vertex_stride=k, n_points=int(len(q2)), n_projected=int(ok.sum()), n_kept=int(keep.sum()),
        affine_c2_to_c9=A.tolist(),
        residual_px9=dict(median=q(res[keep], 50), p95=q(res[keep], 95), p99=q(res[keep], 99), max=float(res[keep].max()),
                          all_p99=q(res, 99), all_max=float(res.max())),
        normal_dist_vox9=dict(median=q(dn[ok], 50), p95=q(dn[ok], 95), p99=q(dn[ok], 99), max=float(dn[ok].max())),
        quadrant_median_residual_px9=qb,
        separable_rule_residual_px9=dict(median=q(sep_res, 50), p95=q(sep_res, 95), max=float(sep_res.max())),
        area=dict(valid9_px=int(val9.sum()), valid9_and_cov24_px=int(both.sum()),
                  valid9_cm2=float(val9.sum() * (9.362e-4) ** 2)),
        ref9_on_valid=dict(ink_ge150_frac=float((ref9[both] >= 149.5).mean()) if both.any() else None,
                           blank_le100_frac=float((ref9[both] <= 100.5).mean()) if both.any() else None),
        ref9_sha256=sha256(f"{d}/ref9.npy"), cov9_sha256=sha256(f"{d}/cov9.npy"), val9_sha256=sha256(f"{d}/val9.npy"),
    )
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(f"{OUT}/{sid}.json", "w"), indent=1)
    print(sid, "pts", out["n_kept"], "res p95", round(out["residual_px9"]["p95"], 3), "max", round(out["residual_px9"]["max"], 3),
          "dn p95", round(out["normal_dist_vox9"]["p95"], 3), "sep p95", round(out["separable_rule_residual_px9"]["p95"], 3),
          "cm2", round(out["area"]["valid9_cm2"], 2), flush=True)


if __name__ == "__main__":
    inv = json.load(open(os.path.join(os.path.dirname(OUT), "segment_inventory.json")))["inventory"][SC]["segments"]
    segs = sorted(inv) if sys.argv[1] == "all" else [s for s in inv if s.startswith(sys.argv[1])]
    for s in segs:
        if os.path.exists(f"{OUT}/{s.split('-', 1)[0]}.json"):
            print("done", s); continue
        run(s)
