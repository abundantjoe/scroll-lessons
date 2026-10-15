# Provenance: Project HERCULES | owner the owner | [id removed]
"""Pre-read planted-fault checks (DECL-EMPNULL TRIBUNAL: "planted faults caught by code
100 %"). The pipeline calls :func:`preread_gate` (or :func:`require_clean`) on every
render record before any image derived from it reaches a reader.

Faults and the check that catches each
--------------------------------------
======================  ==========================  ===================================
fault                   check                       evidence
======================  ==========================  ===================================
8 px window offset      ``window_offset``           surface slice registered against an
                                                    independent reference render of the
                                                    declared window (integer shifts)
mirrored render         ``mirror``                  same registration over the dihedral
                                                    transforms (id, flip_lr, flip_ud,
                                                    rot180 [+ transposes if square])
swapped depth order     ``depth_order``             slice-by-slice NCC matrix vs the
                                                    reference: forward vs reversed
                                                    correspondence; for maps also
                                                    ``map_order`` (hash provenance)
off-by-one slice        ``slice_index``             same matrix: lag of the winning
                                                    correspondence must be 0
re-traced by training   ``retrace``                 3-D KD-tree same-papyrus rule on
                                                    meshes densified 5 x 5
wrong voxel size        ``voxel_size``              value used == metadata.json value
                                                    (hash-pinned file), everywhere it
                                                    is used (command, display key)
======================  ==========================  ===================================

Every check FAILS CLOSED: if the evidence cannot decide (reference and delivered do not
correlate, or two hypotheses score within the declared margin) the check fails with
reason ``unverifiable`` / ``ambiguous`` and nothing is read.

The reference render is computed here from the volume and the tifxyz mesh with the
renderer's own canvas and normal conventions (hercules.pipeline.canvas.emulate_gen:
pixel P samples grid (P + 0.5) s; slice k lies at (k - (n - 1)/2) * step along
+-normalize(du x dv), minus with --flip-normals). Only the block of the volume that the
window touches is read (works on a lazily indexed zarr / S3 array).
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
from scipy.ndimage import map_coordinates
from scipy.spatial import cKDTree

from hercules.geometry.contamination import same_papyrus
from hercules.geometry.tifxyz import densify, read_tifxyz, valid_mask
from hercules.pipeline import canvas as C
from hercules.pipeline.window import ncc, voxel_size_from_metadata

from . import TRIBUNAL_VERSION

# ----------------------------------------------------------------------------- constants
# Every threshold is fixed here and recorded in each gate report.
SHIFT_SEARCH_PX = 12          # integer shift search radius (> the 8 px planted offset)
OFFSET_TOL_PX = 1             # PASS iff Chebyshev |shift| <= 1 px
MIN_REF_NCC = 0.5             # below: reference and delivered do not correlate -> unverifiable
MIRROR_MARGIN = 0.05          # identity must beat every other dihedral transform by this NCC
LAG_SEARCH = 3                # slice lags evaluated in each direction family
DEPTH_MARGIN = 0.02           # forward must beat reversed by this mean-diagonal NCC
SLICE_MARGIN = 0.02           # lag 0 must beat every other lag by this mean-diagonal NCC
MAX_CROP_PX = 256             # central crop (per side) used for registration
VOXEL_REL_TOL = 1e-6          # voxel size equality tolerance (relative)
RETRACE_DENSIFY = 5           # "densify meshes 5x5"
RETRACE_MIN_WITHIN_2 = 1000   # ">= 1000 points lie within 2 vox"
RETRACE_RATIO = 2.0           # "count in [0,1) >= 2x count in [2,3)"
DIHEDRAL_ALWAYS = ("identity", "flip_lr", "flip_ud", "rot180")
DIHEDRAL_SQUARE = ("transpose", "anti_transpose", "rot90", "rot270")


class TribunalFault(RuntimeError):
    """Raised by :func:`require_clean` when any pre-read check fails."""


@dataclass
class CheckResult:
    name: str
    passed: bool
    reason: str
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ----------------------------------------------------------------------------- hashing / IO

def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_sha256(path: str | Path) -> str:
    """Hash of a directory: sorted relative paths and file bytes (tifxyz mesh identity)."""
    root = Path(path)
    h = hashlib.sha256()
    for f in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = f.relative_to(root).as_posix()
        h.update(rel.encode() + b"\0")
        h.update(file_sha256(f).encode() + b"\0")
    return h.hexdigest()


def array_sha256(a: np.ndarray) -> str:
    a = np.ascontiguousarray(a)
    h = hashlib.sha256()
    h.update(f"{a.dtype.str}|{','.join(map(str, a.shape))}|".encode())
    h.update(a.tobytes())
    return h.hexdigest()


def load_stack(path: str | Path) -> np.ndarray:
    """(n, h, w) render stack from a zarr array or a group holding array '0'."""
    import zarr

    z = zarr.open(str(path), mode="r")
    if hasattr(z, "array_keys"):
        z = z["0"]
    a = np.asarray(z[...])
    if a.ndim != 3:
        raise ValueError(f"render stack must be (n, h, w), got {a.shape}")
    return a


# ----------------------------------------------------------------------------- reference render

def slice_offsets_ext(n: int, step: float, lag: int) -> np.ndarray:
    """Offsets of slices j = -lag .. n-1+lag (the official formula, extended)."""
    j = np.arange(-lag, n + lag, dtype=np.float64)
    return np.array([np.float32((k - 0.5 * (n - 1)) * float(step)) for k in j], dtype=np.float64)


def reference_stack(volume, points: np.ndarray, scale, origin_yx: tuple[int, int], shape_hw: tuple[int, int],
                    offsets: Sequence[float], flip_normals: bool, *, zero_is_invalid: bool = True) -> np.ndarray:
    """Independent reference render (len(offsets), h, w) float64, NaN where empty.

    ``origin_yx`` is the canvas pixel (row, col) of output pixel (0, 0) on the canvas of
    ``points`` rendered at --scale 1. ``volume`` is indexed vol[z, y, x]; only the block
    covering the samples is materialised.
    """
    cv = C.canvas_for(np.asarray(points), scale).with_origin(int(origin_yx[0]), int(origin_yx[1]))
    coords, normals = C.emulate_gen(points, cv, (int(shape_hw[0]), int(shape_hw[1])))
    ok = C.render_valid(coords, normals)
    sgn = C.slice_normal_sign(flip_normals)
    offs = np.asarray(offsets, dtype=np.float64)
    out = np.full((len(offs), *shape_hw), np.nan)
    if not ok.any():
        return out
    pc, nc = coords[ok], normals[ok] * sgn
    reach = float(np.max(np.abs(offs))) + 2.0
    lo = np.floor(pc.min(axis=0) - reach).astype(int)
    hi = np.ceil(pc.max(axis=0) + reach).astype(int) + 1
    Z, Y, X = volume.shape
    lo = np.maximum(lo, 0)
    hi = np.minimum(hi, [X, Y, Z])
    if np.any(hi <= lo):
        return out
    block = np.asarray(volume[lo[2]:hi[2], lo[1]:hi[1], lo[0]:hi[0]], dtype=np.float32)
    for i, o in enumerate(offs):
        q = pc + o * nc - lo[None, :]
        vals = map_coordinates(block, np.stack([q[:, 2], q[:, 1], q[:, 0]]), order=1, mode="constant", cval=np.nan)
        s = out[i]
        s[ok] = vals
        if zero_is_invalid:
            s[s == 0] = np.nan
    return out


# ----------------------------------------------------------------------------- registration

def _dihedral(img: np.ndarray, name: str) -> np.ndarray:
    f = {
        "identity": lambda a: a,
        "flip_lr": lambda a: a[..., :, ::-1],
        "flip_ud": lambda a: a[..., ::-1, :],
        "rot180": lambda a: a[..., ::-1, ::-1],
        "transpose": lambda a: np.swapaxes(a, -1, -2),
        "anti_transpose": lambda a: np.swapaxes(a, -1, -2)[..., ::-1, ::-1],
        "rot90": lambda a: np.rot90(a, 1, axes=(-2, -1)),
        "rot270": lambda a: np.rot90(a, 3, axes=(-2, -1)),
    }[name]
    return f(img)


def central_crop(h: int, w: int, max_side: int = MAX_CROP_PX) -> tuple[int, int, int, int]:
    ch, cw = min(h, max_side), min(w, max_side)
    return (h - ch) // 2, (w - cw) // 2, ch, cw


@dataclass
class Registration:
    transform: str
    shift: tuple[int, int]
    best_ncc: float
    per_transform_best: dict
    identity_zero_ncc: float
    slice_matrix_hyp: dict        # "fwd:+0" -> mean diagonal NCC
    winner_hyp: str
    crop: tuple[int, int, int, int]
    n_valid: int


def register(delivered: np.ndarray, volume, points: np.ndarray, scale, origin_yx, n_slices: int, slice_step: float,
             flip_normals: bool, *, search_px: int = SHIFT_SEARCH_PX, lag: int = LAG_SEARCH,
             max_crop: int = MAX_CROP_PX) -> Registration:
    """Register a delivered (n, h, w) stack against the reference render of the declared
    window: first the surface slice over dihedral transforms x integer shifts, then the
    slice correspondence (forward/reversed x lag) at the winning transform and shift."""
    d = np.asarray(delivered, dtype=np.float64)
    n, h, w = d.shape
    d = np.where(d == 0, np.nan, d)
    cy, cx, ch, cw = central_crop(h, w, max_crop)
    S = int(search_px)
    offs = slice_offsets_ext(n, slice_step, lag)
    big_origin = (int(origin_yx[0]) + cy - S, int(origin_yx[1]) + cx - S)
    ref = reference_stack(volume, points, scale, big_origin, (ch + 2 * S, cw + 2 * S), offs, flip_normals)
    k = n // 2
    surf = ref[k + lag]
    names = list(DIHEDRAL_ALWAYS) + (list(DIHEDRAL_SQUARE) if ch == cw else [])
    dcrop = d[:, cy:cy + ch, cx:cx + cw]
    per: dict[str, dict] = {}
    for t in names:
        dk = _dihedral(dcrop[k], t)
        grid = np.full((2 * S + 1, 2 * S + 1), np.nan)
        for dy in range(-S, S + 1):
            for dx in range(-S, S + 1):
                grid[dy + S, dx + S] = ncc(dk, surf[S + dy:S + dy + ch, S + dx:S + dx + cw])[0]
        if np.all(np.isnan(grid)):
            per[t] = {"ncc": math.nan, "shift": [0, 0]}
            continue
        bi = np.unravel_index(np.nanargmax(grid), grid.shape)
        per[t] = {"ncc": float(grid[bi]), "shift": [int(bi[0] - S), int(bi[1] - S)]}
    finite = {t: v for t, v in per.items() if math.isfinite(v["ncc"])}
    if not finite:
        return Registration("none", (0, 0), math.nan, per, math.nan, {}, "none", (cy, cx, ch, cw), 0)
    best_t = max(finite, key=lambda t: (finite[t]["ncc"], t == "identity"))
    dy, dx = per[best_t]["shift"]
    id0, nvalid = ncc(dcrop[k], surf[S:S + ch, S:S + cw])
    # slice correspondence at the winning transform/shift
    J = n + 2 * lag
    M = np.full((n, J), np.nan)
    dT = _dihedral(dcrop, best_t)
    for kk in range(n):
        for j in range(J):
            M[kk, j] = ncc(dT[kk], ref[j][S + dy:S + dy + ch, S + dx:S + dx + cw])[0]
    hyp = {}
    ks = np.arange(n)
    for fam in ("fwd", "rev"):
        for L in range(-lag, lag + 1):
            j = (ks + L + lag) if fam == "fwd" else (n - 1 - ks + L + lag)
            vals = M[ks, j]
            hyp[f"{fam}:{L:+d}"] = float(np.nanmean(vals)) if np.isfinite(vals).any() else math.nan
    fin = {k2: v for k2, v in hyp.items() if math.isfinite(v)}
    winner = max(fin, key=lambda k2: (fin[k2], k2 == "fwd:+0")) if fin else "none"
    return Registration(best_t, (int(dy), int(dx)), float(per[best_t]["ncc"]), per, float(id0), hyp, winner,
                        (cy, cx, ch, cw), int(nvalid))


DEFAULT_THRESHOLDS = {"MIN_REF_NCC": MIN_REF_NCC, "OFFSET_TOL_PX": OFFSET_TOL_PX, "MIRROR_MARGIN": MIRROR_MARGIN,
                      "DEPTH_MARGIN": DEPTH_MARGIN, "SLICE_MARGIN": SLICE_MARGIN}


def _t(thresholds: Mapping[str, float] | None) -> dict:
    """Thresholds in force: the declared defaults, overridden key by key (never rounded)."""
    t = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        unknown = set(thresholds) - set(t)
        if unknown:
            raise ValueError(f"unknown thresholds {sorted(unknown)}")
        t.update({k: float(v) for k, v in thresholds.items()})
    return t


def _unverifiable(reg: Registration, t: Mapping[str, float] | None = None) -> bool:
    thr = _t(t)["MIN_REF_NCC"]
    return not (math.isfinite(reg.best_ncc) and reg.best_ncc >= thr)


def _result(name: str, reasons: list[str], det: dict) -> CheckResult:
    """All conditions were evaluated; ``reason`` is the first failure (or ok), ``details.reasons`` lists all."""
    det["reasons"] = list(reasons)
    return CheckResult(name, not reasons, reasons[0] if reasons else "ok", det)


def check_window_offset(reg: Registration, thresholds: Mapping[str, float] | None = None) -> CheckResult:
    t = _t(thresholds)
    det = {"shift_yx": list(reg.shift), "best_ncc": reg.best_ncc, "tol_px": t["OFFSET_TOL_PX"],
           "identity_zero_shift_ncc": reg.identity_zero_ncc, "search_px": SHIFT_SEARCH_PX,
           "min_ref_ncc": t["MIN_REF_NCC"]}
    reasons = []
    if _unverifiable(reg, t):
        reasons.append("unverifiable")
    if max(abs(reg.shift[0]), abs(reg.shift[1])) > t["OFFSET_TOL_PX"]:
        reasons.append("offset")
    return _result("window_offset", reasons, det)


def check_mirror(reg: Registration, thresholds: Mapping[str, float] | None = None) -> CheckResult:
    t = _t(thresholds)
    per = {k: v["ncc"] for k, v in reg.per_transform_best.items()}
    idn = per.get("identity", math.nan)
    others = [v for k, v in per.items() if k != "identity" and math.isfinite(v)]
    margin = (idn - max(others)) if (others and math.isfinite(idn)) else math.nan
    det = {"transform": reg.transform, "per_transform_ncc": per, "identity_margin": margin,
           "margin_min": t["MIRROR_MARGIN"], "min_ref_ncc": t["MIN_REF_NCC"]}
    reasons = []
    if _unverifiable(reg, t):
        reasons.append("unverifiable")
    if reg.transform != "identity":
        reasons.append(f"transform:{reg.transform}")
    if not (math.isfinite(margin) and margin >= t["MIRROR_MARGIN"]):
        reasons.append("ambiguous")
    return _result("mirror", reasons, det)


def _best(hyp: Mapping[str, float], fam: str | None = None, lag: int | None = None, exclude: str | None = None):
    items = [(k, v) for k, v in hyp.items() if math.isfinite(v) and (fam is None or k.startswith(fam))
             and (lag is None or int(k.split(":")[1]) == lag) and k != exclude]
    return max(items, key=lambda kv: kv[1]) if items else (None, math.nan)


def check_depth_order(reg: Registration, thresholds: Mapping[str, float] | None = None) -> CheckResult:
    t = _t(thresholds)
    bf, vf = _best(reg.slice_matrix_hyp, "fwd")
    br, vr = _best(reg.slice_matrix_hyp, "rev")
    margin = vf - vr if (math.isfinite(vf) and math.isfinite(vr)) else math.nan
    det = {"winner": reg.winner_hyp, "best_fwd": [bf, vf], "best_rev": [br, vr], "fwd_minus_rev": margin,
           "margin_min": t["DEPTH_MARGIN"], "min_ref_ncc": t["MIN_REF_NCC"]}
    reasons = []
    if _unverifiable(reg, t):
        reasons.append("unverifiable")
    if reg.winner_hyp.startswith("rev"):
        reasons.append("reversed")
    if not (math.isfinite(margin) and margin >= t["DEPTH_MARGIN"]):
        reasons.append("ambiguous")
    return _result("depth_order", reasons, det)


def check_slice_index(reg: Registration, thresholds: Mapping[str, float] | None = None) -> CheckResult:
    """Lag of the winning correspondence within its own direction family must be 0."""
    t = _t(thresholds)
    fam = reg.winner_hyp.split(":")[0] if ":" in reg.winner_hyp else "fwd"
    k0, v0 = _best(reg.slice_matrix_hyp, fam, 0)
    others = [(k, v) for k, v in reg.slice_matrix_hyp.items()
              if k.startswith(fam) and k != k0 and math.isfinite(v)]
    ko, vo = max(others, key=lambda kv: kv[1]) if others else (None, math.nan)
    margin = v0 - vo if (math.isfinite(v0) and math.isfinite(vo)) else math.nan
    lag = int(reg.winner_hyp.split(":")[1]) if ":" in reg.winner_hyp else None
    det = {"winner": reg.winner_hyp, "lag": lag, "lag0_ncc": v0, "best_other": [ko, vo], "margin": margin,
           "margin_min": t["SLICE_MARGIN"], "min_ref_ncc": t["MIN_REF_NCC"]}
    reasons = []
    if _unverifiable(reg, t):
        reasons.append("unverifiable")
    if lag != 0:
        reasons.append(f"lag:{lag:+d}" if lag is not None else "none")
    if not (math.isfinite(margin) and margin >= t["SLICE_MARGIN"]):
        reasons.append("ambiguous")
    return _result("slice_index", reasons, det)


# ----------------------------------------------------------------------------- voxel size

def _parse_cmd_voxel(cmd: Sequence[str]) -> float | None:
    cmd = list(cmd)
    for i, a in enumerate(cmd):
        if a == "--voxel-size" and i + 1 < len(cmd):
            return float(cmd[i + 1])
        if a.startswith("--voxel-size="):
            return float(a.split("=", 1)[1])
    return None


def check_voxel_size(manifest: Mapping[str, Any]) -> CheckResult:
    """The voxel size used anywhere in the record equals the value in the volume's
    metadata.json, whose sha256 is pinned in the record (never assumed)."""
    vol = manifest.get("volume", {})
    path = vol.get("metadata_json")
    det: dict[str, Any] = {"metadata_json": path, "rel_tol": VOXEL_REL_TOL}
    if not path or not Path(path).is_file():
        return CheckResult("voxel_size", False, "no_metadata_json", det)
    url = str(vol.get("url", "")).rstrip("/")
    det["volume_url"] = url
    det["metadata_source"] = vol.get("metadata_source")
    if not url or vol.get("metadata_source") != url + "/metadata.json":
        return CheckResult("voxel_size", False, "metadata_not_of_this_volume", det)
    sha = file_sha256(path)
    det["metadata_sha256"] = sha
    if vol.get("metadata_sha256") != sha:
        return CheckResult("voxel_size", False, "metadata_hash_mismatch", det)
    true_um = voxel_size_from_metadata(path)
    det["metadata_voxel_um"] = true_um
    used: dict[str, float] = {}
    if "voxel_size_um" in manifest:
        used["manifest"] = float(manifest["voxel_size_um"])
    else:
        return CheckResult("voxel_size", False, "no_declared_voxel", det)
    cmd = manifest.get("render_command")
    if cmd:
        v = _parse_cmd_voxel(cmd)
        if v is None:
            return CheckResult("voxel_size", False, "command_lacks_voxel", det)
        used["render_command"] = v
    disp = manifest.get("display")
    if disp and "px_per_mm_image" in disp:
        # px_per_mm_image = (1000 / voxel_um) * display_scale  (display.builder key)
        used["display_key"] = 1000.0 * float(disp["scale"]) / float(disp["px_per_mm_image"])
    if manifest.get("stack_attrs_voxel_um") is not None:
        used["stack_attrs"] = float(manifest["stack_attrs_voxel_um"])
    det["used"] = used
    bad = {k: v for k, v in used.items() if abs(v - true_um) > VOXEL_REL_TOL * true_um + 1e-9}
    det["mismatch"] = bad
    if bad:
        return CheckResult("voxel_size", False, "wrong_voxel_size", det)
    return CheckResult("voxel_size", True, "ok", det)


# ----------------------------------------------------------------------------- re-trace (KD-tree)

def _closest_on_triangles(p: np.ndarray, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Distance from points p (N, 3) to triangles (a, b, c) (N, 3) each (Ericson 5.1.5)."""
    ab, ac, ap = b - a, c - a, p - a
    d1 = np.einsum("ij,ij->i", ab, ap)
    d2 = np.einsum("ij,ij->i", ac, ap)
    bp = p - b
    d3 = np.einsum("ij,ij->i", ab, bp)
    d4 = np.einsum("ij,ij->i", ac, bp)
    cp = p - c
    d5 = np.einsum("ij,ij->i", ab, cp)
    d6 = np.einsum("ij,ij->i", ac, cp)
    va = d3 * d6 - d5 * d4
    vb = d5 * d2 - d1 * d6
    vc = d1 * d4 - d3 * d2
    res = np.empty_like(p)
    done = np.zeros(len(p), dtype=bool)

    def put(mask, val):
        m = mask & ~done
        res[m] = val[m]
        done[m] = True

    put((d1 <= 0) & (d2 <= 0), a)
    put((d3 >= 0) & (d4 <= d3), b)
    with np.errstate(divide="ignore", invalid="ignore"):
        v = d1 / (d1 - d3)
        put((vc <= 0) & (d1 >= 0) & (d3 <= 0), a + v[:, None] * ab)
        put((d6 >= 0) & (d5 <= d6), c)
        w = d2 / (d2 - d6)
        put((vb <= 0) & (d2 >= 0) & (d6 <= 0), a + w[:, None] * ac)
        w2 = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        put((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), b + w2[:, None] * (c - b))
        den = 1.0 / (va + vb + vc)
        vv, ww = vb * den, vc * den
        inner = a + ab * vv[:, None] + ac * ww[:, None]
    put(np.ones(len(p), dtype=bool), inner)
    return np.linalg.norm(p - res, axis=1)


def surface_distances(A_dense: np.ndarray, B_dense_grid: np.ndarray, max_dist: float = 3.0, k_nn: int = 4,
                      workers: int = 1) -> np.ndarray:
    """Distance from each valid point of A (N, 3 or grid) to the triangulated surface of
    the densified grid B; inf beyond ``max_dist`` (plus a circumradius bound)."""
    from hercules.geometry.contamination import cloud

    a = cloud(A_dense)
    g = np.asarray(B_dense_grid, dtype=np.float64)
    vb = valid_mask(g)
    Hb, Wb = vb.shape
    idx_grid = np.full((Hb, Wb), -1, dtype=np.int64)
    idx_grid[vb] = np.arange(int(vb.sum()))
    bpts = g[vb]
    rc, cc = np.nonzero(vb)
    out = np.full(len(a), np.inf)
    if len(bpts) == 0 or len(a) == 0:
        return out
    # circumradius bound: any surface point is within half the longest quad diagonal of a vertex
    du = np.linalg.norm(g[:, 1:] - g[:, :-1], axis=-1)[vb[:, 1:] & vb[:, :-1]]
    dv = np.linalg.norm(g[1:] - g[:-1], axis=-1)[vb[1:] & vb[:-1]]
    hmax = float(max(du.max() if du.size else 0.0, dv.max() if dv.size else 0.0))
    reach = max_dist + hmax * math.sqrt(2.0) / 2.0 + 1e-6
    tree = cKDTree(bpts)
    d, nn = tree.query(a, k=k_nn, distance_upper_bound=reach, workers=workers)
    d = np.atleast_2d(d.reshape(len(a), -1))
    nn = np.atleast_2d(nn.reshape(len(a), -1))
    cand = np.isfinite(d[:, 0])
    qi = np.flatnonzero(cand)
    if qi.size == 0:
        return out
    best = np.full(qi.size, np.inf)
    for kk in range(nn.shape[1]):
        vid = nn[qi, kk]
        okv = vid < len(bpts)
        r0 = np.where(okv, rc[np.minimum(vid, len(rc) - 1)], 0)
        c0 = np.where(okv, cc[np.minimum(vid, len(cc) - 1)], 0)
        for dr in (-1, 0):
            for dc in (-1, 0):
                r, c = r0 + dr, c0 + dc
                inq = okv & (r >= 0) & (c >= 0) & (r + 1 < Hb) & (c + 1 < Wb)
                rr, cc2 = np.where(inq, r, 0), np.where(inq, c, 0)
                qv = inq & vb[rr, cc2] & vb[rr + 1, cc2] & vb[rr, cc2 + 1] & vb[rr + 1, cc2 + 1]
                if not qv.any():
                    continue
                sel = np.flatnonzero(qv)
                p = a[qi[sel]]
                p00, p01 = g[rr[sel], cc2[sel]], g[rr[sel], cc2[sel] + 1]
                p10, p11 = g[rr[sel] + 1, cc2[sel]], g[rr[sel] + 1, cc2[sel] + 1]
                for tri in ((p00, p01, p10), (p11, p10, p01)):
                    dd = _closest_on_triangles(p, *tri)
                    best[sel] = np.minimum(best[sel], dd)
    out[qi] = best
    out[out > max_dist] = np.inf
    return out


def same_papyrus_surface(A_dense, B_dense_grid, *, min_within_2: int = RETRACE_MIN_WITHIN_2,
                         ratio: float = RETRACE_RATIO, workers: int = 1) -> dict:
    """The declared rule with point-to-SURFACE distance (density-independent form)."""
    d = surface_distances(A_dense, B_dense_grid, 3.0, workers=workers)
    c0 = int(np.sum(d < 1.0))
    c1 = int(np.sum((d >= 1.0) & (d < 2.0)))
    c2 = int(np.sum((d >= 2.0) & (d < 3.0)))
    w2 = c0 + c1
    return {"counts": [c0, c1, c2], "n_within_2": w2, "same": bool(w2 >= min_within_2 and c0 >= ratio * c2),
            "n_a": int(np.isfinite(d).size)}


def check_retrace(window_points: np.ndarray, training: Mapping[str, np.ndarray], *,
                  densify_k: int = RETRACE_DENSIFY, workers: int = 1) -> CheckResult:
    """3-D KD-tree same-papyrus test of the window mesh against every training segment.

    Both meshes are densified k x k (declared k = 5). SAME if >= 1000 window points lie
    within 2 vox and count[0,1) >= 2 count[2,3). Two distance forms are evaluated and a
    segment is SAME if EITHER says so (fail closed):
      * ``vertex``: nearest densified B vertex (the literal rule, contamination.same_papyrus);
      * ``surface``: nearest point of B's triangulated densified surface (the literal
        rule under-calls when the densified spacing exceeds ~1 vox, see REPORT.md).
    """
    A = densify(window_points, densify_k)
    per: dict[str, Any] = {}
    hits: list[str] = []
    for sid, pts in training.items():
        B = densify(pts, densify_k)
        lit = same_papyrus(A, B, workers=workers)
        surf = same_papyrus_surface(A, B, workers=workers)
        same = bool(lit.same or surf["same"])
        per[str(sid)] = {"vertex": {"counts": list(lit.counts), "n_within_2": lit.n_within_2, "same": bool(lit.same)},
                         "surface": surf, "same": same}
        if same:
            hits.append(str(sid))
    det = {"densify_k": densify_k, "min_within_2": RETRACE_MIN_WITHIN_2, "ratio": RETRACE_RATIO,
           "n_training": len(training), "per_segment": per, "same_as": hits}
    return CheckResult("retrace", not hits, "ok" if not hits else "retraced_by_training", det)


# ----------------------------------------------------------------------------- map provenance

def check_map_order(maps: Mapping[str, Mapping[str, Any]], text_direction: str,
                    inference_log: Sequence[Mapping[str, Any]]) -> CheckResult:
    """Each ink map shown to a reader is labelled with an order ("text"/"nontext"). The
    map file's sha256 must be recorded in the inference log as the output of the
    direction that order implies (text_direction = "forward" or "reverse")."""
    if text_direction not in ("forward", "reverse"):
        raise ValueError("text_direction must be 'forward' or 'reverse'")
    other = "reverse" if text_direction == "forward" else "forward"
    want = {"text": text_direction, "nontext": other}
    by_sha = {}
    for e in inference_log:
        by_sha.setdefault(e["output_sha256"], []).append(e)
    per, bad = {}, []
    for label, m in maps.items():
        sha = file_sha256(m["path"])
        entries = by_sha.get(sha, [])
        dirs = sorted({e["direction"] for e in entries})
        stack_ok = all(e.get("input_stack_sha256") == m.get("stack_sha256") for e in entries) if entries else False
        ok = bool(entries) and dirs == [want[m["order"]]] and stack_ok
        per[label] = {"order": m["order"], "sha256": sha, "logged_directions": dirs, "stack_match": stack_ok, "ok": ok}
        if not ok:
            bad.append(label)
    det = {"text_direction": text_direction, "maps": per, "bad": bad}
    return CheckResult("map_order", not bad, "ok" if not bad else "order_provenance_mismatch", det)


# ----------------------------------------------------------------------------- gate

def _mesh_points(manifest: Mapping[str, Any]):
    m = manifest["mesh"]
    return read_tifxyz(m["path"])


def preread_gate(manifest: Mapping[str, Any], *, volume, training: Mapping[str, np.ndarray] | None = None,
                 maps: Mapping[str, Mapping[str, Any]] | None = None, text_direction: str | None = None,
                 inference_log: Sequence[Mapping[str, Any]] | None = None, workers: int = 1,
                 thresholds: Mapping[str, float] | None = None) -> dict:
    """Run every pre-read check on one render record. Returns a JSON-able report;
    ``report["passed"]`` is True only if every check passed.

    manifest keys: window_id; volume {url, metadata_source (= url + "/metadata.json"),
    metadata_json (local copy), metadata_sha256}; voxel_size_um;
    mesh {path, sha256 (tree_sha256)}; crop {y0, x0, h, w} (canvas of that mesh);
    n_slices; slice_step; flip_normals; stack {path, sha256 (array_sha256)};
    optional render_command, display {scale, px_per_mm_image}, stack_attrs_voxel_um.
    ``training`` maps segment id -> (H, W, 3) grid; None means "no training list
    supplied" and FAILS (the re-trace check can never be skipped silently).
    """
    results: list[CheckResult] = []
    prov: dict[str, Any] = {}
    # provenance of the files the checks rely on
    mesh_sha = tree_sha256(manifest["mesh"]["path"])
    prov["mesh_sha256"] = mesh_sha
    mesh_ok = mesh_sha == manifest["mesh"].get("sha256")
    stack = load_stack(manifest["stack"]["path"])
    st_sha = array_sha256(stack)
    prov["stack_sha256"] = st_sha
    stack_ok = st_sha == manifest["stack"].get("sha256")
    shape_ok = (stack.shape[0] == int(manifest["n_slices"]) and
                stack.shape[1:] == (int(manifest["crop"]["h"]), int(manifest["crop"]["w"])))
    results.append(CheckResult("provenance", bool(mesh_ok and stack_ok and shape_ok),
                               "ok" if (mesh_ok and stack_ok and shape_ok) else "hash_or_shape_mismatch",
                               {"mesh_ok": mesh_ok, "stack_ok": stack_ok, "shape_ok": shape_ok,
                                "stack_shape": list(stack.shape), **prov}))
    results.append(check_voxel_size(manifest))
    mesh = _mesh_points(manifest)
    reg = register(stack, volume, mesh.points, mesh.scale, (int(manifest["crop"]["y0"]), int(manifest["crop"]["x0"])),
                   int(manifest["n_slices"]), float(manifest["slice_step"]), bool(manifest["flip_normals"]))
    results += [check_window_offset(reg, thresholds), check_mirror(reg, thresholds),
                check_depth_order(reg, thresholds), check_slice_index(reg, thresholds)]
    if training is None:
        results.append(CheckResult("retrace", False, "no_training_list", {}))
    else:
        results.append(check_retrace(mesh.points, training, workers=workers))
    if maps is not None:
        if text_direction is None or inference_log is None:
            results.append(CheckResult("map_order", False, "no_direction_or_log", {}))
        else:
            results.append(check_map_order(maps, text_direction, inference_log))
    passed = all(r.passed for r in results)
    return {
        "tribunal_version": TRIBUNAL_VERSION,
        "window_id": manifest.get("window_id"),
        "passed": passed,
        "failed": [r.name for r in results if not r.passed],
        "checks": [r.to_dict() for r in results],
        "thresholds": {
            **_t(thresholds), "SHIFT_SEARCH_PX": SHIFT_SEARCH_PX, "LAG_SEARCH": LAG_SEARCH,
            "MAX_CROP_PX": MAX_CROP_PX, "VOXEL_REL_TOL": VOXEL_REL_TOL,
            "RETRACE_DENSIFY": RETRACE_DENSIFY, "RETRACE_MIN_WITHIN_2": RETRACE_MIN_WITHIN_2,
            "RETRACE_RATIO": RETRACE_RATIO,
        },
    }


def require_clean(report: Mapping[str, Any]) -> None:
    """Raise TribunalFault unless every check passed (call before any reader job)."""
    if not report.get("passed"):
        raise TribunalFault(f"pre-read gate FAILED for {report.get('window_id')}: {report.get('failed')}")


def dumps(report: Mapping[str, Any]) -> str:
    return json.dumps(report, indent=1, sort_keys=True, default=float)


CHECKS: dict[str, Callable] = {
    "window_offset": check_window_offset,
    "mirror": check_mirror,
    "depth_order": check_depth_order,
    "slice_index": check_slice_index,
    "retrace": check_retrace,
    "voxel_size": check_voxel_size,
    "map_order": check_map_order,
}
