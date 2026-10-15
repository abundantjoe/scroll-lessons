# Provenance: Project HERCULES | owner the owner | [id removed]
"""Method C6: register a 9 um CT volume onto a ~2.4 um rescan of the same scroll.

Model
-----
For a 9 um voxel coordinate p = (x9, y9, z9) the rescan voxel coordinate is

    q = F * (p + t(p) - z0 * e_z),      t(p) = M (p - Pm) + b

in the *canonical* rescan frame, where F = voxel_9 / voxel_r comes from the two
volumes' metadata (use ``scale_factor``; never assume it), z0 is the 9 um z at
which the rescan starts, M (3x3) holds small tilts / scale errors, Pm is the
mean of the fit patch centres and b = t(Pm).  A remount can flip or rotate
axes; that is an ``Orientation`` between the canonical frame and the raw
(stored) rescan array: raw axis perm[i] carries canonical axis i, reversed
over its extent (N - 1 - q) when flip[i].  In matrix form
q_raw = G q_can + offset with G a signed permutation (e.g. diag(+1,-1,-1)).
z0 and b_z are degenerate (only b_z - z0 is identifiable): z0 is held at the
caller's guess and the fit absorbs any error into b_z.

Conventions
-----------
* Points and transform parameters (p, q, M, b, Pm, patch centres, offsets,
  residuals) are (x, y, z).
* Array shapes, boxes (lo, hi), ``block`` sizes and the shifts returned by
  ``phase_correlate_3d`` are numpy (z, y, x) order.
* Voxel coordinates refer to voxel centres; voxel k covers [k - 0.5, k + 0.5).

Readers
-------
A reader is a callable ``reader(lo, hi) -> ndarray`` returning the block
``vol[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]`` (zyx), with voxels outside the
volume set to NaN.  The rescan reader must also expose ``.shape`` (or pass
``volr_shape``) so axis flips can be expressed.  ``ArrayReader`` wraps any
sliceable array with ``.shape`` (numpy, memmap, zarr).
"""
from __future__ import annotations

import itertools
import math
import time
from dataclasses import dataclass, field

import numpy as np
from scipy import fft as sfft
from scipy import ndimage as ndi

BAR_MEDIAN_R = 0.85
BAR_RMS_VOX = 1.5
FFT_WORKERS = 2
PC_LOWPASS = 0.15  # cycles/voxel; see phase_correlate_3d

_EZ = np.array([0.0, 0.0, 1.0])  # unit z in (x, y, z)


# --------------------------------------------------------------------------
# metadata / readers / orientation
# --------------------------------------------------------------------------
def scale_factor(voxel_9_um: float, voxel_r_um: float) -> float:
    """F = voxel_9 / voxel_r from the two volumes' metadata (e.g. 9.366/2.403)."""
    v9, vr = float(voxel_9_um), float(voxel_r_um)
    if not (v9 > 0 and vr > 0 and math.isfinite(v9) and math.isfinite(vr)):
        raise ValueError(f"voxel sizes must be positive, got {v9}, {vr}")
    F = v9 / vr
    if F <= 1.0:
        raise ValueError(f"F = {F:.5f} <= 1: arguments swapped? (voxel_9, voxel_r)")
    return F


class ArrayReader:
    """Box reader over an array-like with numpy slicing and ``.shape``.

    ``reader(lo, hi)`` returns the zyx box [lo, hi).  A box inside the
    volume comes back in the array's native dtype (e.g. uint16, no float copy
    of a ~1e8-voxel rescan block); a box that leaves the volume comes back as
    float32 with the outside set to ``fill`` (NaN by default, i.e. invalid).
    """

    def __init__(self, arr, fill: float = np.nan):
        self.arr = arr
        self.shape = tuple(int(s) for s in arr.shape)
        self.fill = fill

    def __call__(self, lo, hi) -> np.ndarray:
        lo = [int(v) for v in lo]
        hi = [int(v) for v in hi]
        src = tuple(slice(max(l, 0), min(h, n)) for l, h, n in zip(lo, hi, self.shape))
        if all(s.start == l and s.stop == h for s, l, h in zip(src, lo, hi)):
            return np.asarray(self.arr[src])
        out = np.full([h - l for l, h in zip(lo, hi)], self.fill, np.float32)
        if all(s.stop > s.start for s in src):
            dst = tuple(slice(s.start - l, s.stop - l) for s, l in zip(src, lo))
            out[dst] = np.asarray(self.arr[src], dtype=np.float32)
        return out


@dataclass(frozen=True)
class Orientation:
    """Canonical <-> raw rescan axes (zyx array order).

    Canonical array axis i is raw axis ``perm[i]``, reversed when ``flip[i]``.
    """

    perm: tuple = (0, 1, 2)
    flip: tuple = (False, False, False)

    def can_shape(self, raw_shape):
        return tuple(int(raw_shape[a]) for a in self.perm)

    def raw_box(self, lo, hi, raw_shape):
        rlo, rhi = [0, 0, 0], [0, 0, 0]
        for i, a in enumerate(self.perm):
            if self.flip[i]:
                rlo[a], rhi[a] = raw_shape[a] - int(hi[i]), raw_shape[a] - int(lo[i])
            else:
                rlo[a], rhi[a] = int(lo[i]), int(hi[i])
        return rlo, rhi

    def orient_block(self, raw_block):
        blk = np.transpose(raw_block, self.perm)
        for i in range(3):
            if self.flip[i]:
                blk = np.flip(blk, i)
        return blk

    def can_to_raw(self, q_zyx, raw_shape):
        q = np.asarray(q_zyx, float)
        r = np.empty_like(q)
        for i, a in enumerate(self.perm):
            r[..., a] = (raw_shape[a] - 1 - q[..., i]) if self.flip[i] else q[..., i]
        return r

    def raw_to_can(self, r_zyx, raw_shape):
        r = np.asarray(r_zyx, float)
        q = np.empty_like(r)
        for i, a in enumerate(self.perm):
            q[..., i] = (raw_shape[a] - 1 - r[..., a]) if self.flip[i] else r[..., a]
        return q

    # (x, y, z) descriptions for reports
    def perm_xyz(self):
        return [2 - self.perm[2 - k] for k in range(3)]

    def flip_signs_xyz(self):
        return [-1 if self.flip[2 - k] else 1 for k in range(3)]

    def G_xyz(self):
        """Signed permutation with q_raw = G q_can + offset, (x, y, z)."""
        G = np.zeros((3, 3), int)
        for k, (a, s) in enumerate(zip(self.perm_xyz(), self.flip_signs_xyz())):
            G[a, k] = s
        return G

    def to_json(self, raw_shape=None):
        d = {
            "perm_zyx": [int(v) for v in self.perm],
            "flip_zyx": [bool(v) for v in self.flip],
            "perm_xyz": self.perm_xyz(),
            "flip_signs_xyz": self.flip_signs_xyz(),
            "G_xyz": self.G_xyz().tolist(),
        }
        if raw_shape is not None:
            d["rescan_shape_zyx"] = [int(v) for v in raw_shape]
        return d

    @classmethod
    def from_json(cls, d):
        return cls(tuple(int(v) for v in d["perm_zyx"]), tuple(bool(v) for v in d["flip_zyx"]))


def candidate_orientations(mode: str = "flips"):
    """'flips': the 8 axis-sign flips; 'flips+xy': also x<->y swapped (16);
    'all': every axis permutation (48)."""
    perms = {
        "flips": [(0, 1, 2)],
        "flips+xy": [(0, 1, 2), (0, 2, 1)],
        "all": list(itertools.permutations(range(3))),
    }[mode]
    return [Orientation(p, f) for p in perms for f in itertools.product((False, True), repeat=3)]


class OrientedReader:
    """Reads canonical-frame boxes from a raw rescan reader."""

    def __init__(self, reader, raw_shape, orientation: Orientation):
        self.reader = reader
        self.raw_shape = tuple(int(v) for v in raw_shape)
        self.orientation = orientation
        self.shape = orientation.can_shape(self.raw_shape)

    def __call__(self, lo, hi):
        rlo, rhi = self.orientation.raw_box(lo, hi, self.raw_shape)
        return self.orientation.orient_block(self.reader(rlo, rhi))

    def read_downsampled(self, lo, hi, F, origin, out_shape):
        """== downsample_area(self(lo, hi), F, origin, out_shape), but reduced in
        the raw frame (contiguous, BLAS-friendly) and oriented afterwards."""
        rlo, rhi = self.orientation.raw_box(lo, hi, self.raw_shape)
        return _downsample_oriented(self.reader(rlo, rhi), self.orientation,
                                    np.asarray(hi) - np.asarray(lo), F, origin, out_shape)


def _downsample_oriented(raw_block, ori: Orientation, n_in_can, F, origin, out_shape):
    """downsample_area(ori.orient_block(raw_block), F, origin, out_shape) computed
    on the raw block (output j <-> n_out-1-j and c <-> n_in-1-c on flipped axes)."""
    r_origin, r_shape = np.zeros(3), [0, 0, 0]
    for i, a in enumerate(ori.perm):
        o = float(origin[i])
        if ori.flip[i]:
            o = n_in_can[i] - 1 - o - F * (out_shape[i] - 1)
        r_origin[a], r_shape[a] = o, int(out_shape[i])
    D = downsample_area(raw_block, F, r_origin, r_shape)
    return np.ascontiguousarray(ori.orient_block(D))


# --------------------------------------------------------------------------
# transform
# --------------------------------------------------------------------------
@dataclass
class C6Transform:
    F: float
    z0: float
    M: np.ndarray = field(default_factory=lambda: np.zeros((3, 3)))
    b: np.ndarray = field(default_factory=lambda: np.zeros(3))
    Pm: np.ndarray = field(default_factory=lambda: np.zeros(3))
    orientation: Orientation = Orientation()
    raw_shape: tuple | None = None

    def __post_init__(self):
        self.M = np.asarray(self.M, float).reshape(3, 3)
        self.b = np.asarray(self.b, float).reshape(3)
        self.Pm = np.asarray(self.Pm, float).reshape(3)

    def t(self, p):
        p = np.asarray(p, float)
        return (p - self.Pm) @ self.M.T + self.b

    def with_offset(self, offset_xyz):
        return C6Transform(self.F, self.z0, self.M.copy(), self.b + np.asarray(offset_xyz, float),
                           self.Pm.copy(), self.orientation, self.raw_shape)

    @classmethod
    def from_fit(cls, fit):
        if isinstance(fit, C6Transform):
            return fit
        o = fit.get("orientation")
        ori = Orientation.from_json(o) if o else Orientation()
        raw = tuple(o["rescan_shape_zyx"]) if o and "rescan_shape_zyx" in o else None
        return cls(float(fit["F"]), float(fit["z0"]), fit["M"], fit["b"], fit["Pm"], ori, raw)


# --------------------------------------------------------------------------
# 1. area downsampling
# --------------------------------------------------------------------------
def _box_weights(n_in, F, origin, n_out):
    """Exact overlap weights W[i, k] of input voxel k with output footprint i."""
    lo = origin + F * np.arange(n_out) - F / 2.0 + 0.5  # edge coords: voxel k spans [k, k+1]
    hi = lo + F
    k = np.arange(n_in)
    W = np.clip(np.minimum(k[None, :] + 1, hi[:, None]) - np.maximum(k[None, :], lo[:, None]),
                0.0, None) / F
    bad = (lo < -1e-6) | (hi > n_in + 1e-6)
    return W, bad


def _box_axis(arr, axis, F, origin, n_out, chunk=16):
    """Exact box-mean resampling along one axis (piecewise-constant input).

    Banded matrix product applied in chunks of ``chunk`` outputs, each against
    only its ~chunk*F+2 input support (BLAS; ~12x faster than per-tap gathers).
    """
    W, bad = _box_weights(arr.shape[axis], F, origin, n_out)
    fdt = np.float64 if arr.dtype == np.float64 else np.float32
    W = W.astype(fdt)
    cast = arr.dtype != fdt  # e.g. uint16: cast chunk-wise, never the whole block
    last = axis == arr.ndim - 1
    src = arr if last else np.moveaxis(arr, axis, -2)
    oshape = list(src.shape)
    oshape[-1 if last else -2] = n_out
    out = np.zeros(oshape, fdt)
    for o0 in range(0, n_out, chunk):
        o1 = min(o0 + chunk, n_out)
        sup = np.nonzero(W[o0:o1].any(0))[0]
        if sup.size == 0:
            continue
        k0, k1 = int(sup[0]), int(sup[-1]) + 1
        Wc = W[o0:o1, k0:k1]
        if last:
            x = src[..., k0:k1]
            np.matmul(x.astype(fdt) if cast else x, Wc.T, out=out[..., o0:o1])
        else:
            x = src[..., k0:k1, :]
            np.matmul(Wc, x.astype(fdt) if cast else x, out=out[..., o0:o1, :])
    if not last:
        out = np.moveaxis(out, -2, axis)
    if bad.any():
        idx = [slice(None)] * arr.ndim
        idx[axis] = np.nonzero(bad)[0]
        out[tuple(idx)] = np.nan
    return out


def downsample_area(vol, F, origin=None, out_shape=None):
    """Area-mean downsampling of a high-res block onto the 9 um grid.

    Output voxel i (zyx) is the mean of ``vol`` over the axis-aligned cube of
    side F (high-res voxels) centred at block coordinate ``origin + F * i``,
    with ``vol`` treated as piecewise constant over its voxels.  This is
    *exact box integration*: separable, each output weights ceil(F)+1 input
    voxels per axis by their exact overlap length.  Chosen over zoom+Gaussian
    prefilter because it is the exact 9 um voxel footprint (no ringing, no
    sigma to tune) and handles a fractional ``origin`` exactly, so the pipeline
    applies translations without interpolating.  Output voxels whose footprint
    leaves the block or touches a NaN input are NaN.

    Defaults: origin = (F - 1) / 2 (first footprint starts at the block edge),
    out_shape = floor(shape / F).
    """
    vol = np.asarray(vol)
    if vol.dtype.kind not in "fiu" or vol.dtype == np.float16:
        vol = vol.astype(np.float32)
    F = float(F)
    if origin is None:
        origin = np.full(vol.ndim, (F - 1.0) / 2.0)
    origin = np.broadcast_to(np.asarray(origin, float), (vol.ndim,))
    if out_shape is None:
        out_shape = [int(math.floor(n / F)) for n in vol.shape]
    nan = ~np.isfinite(vol) if vol.dtype.kind == "f" else None
    has_nan = nan is not None and bool(nan.any())
    data = np.where(nan, 0, vol).astype(vol.dtype) if has_nan else vol
    # reduce the last (contiguous, largest) axis first
    for ax in reversed(range(vol.ndim)):
        data = _box_axis(data, ax, F, origin[ax], int(out_shape[ax]))
    if has_nan:
        cov = (~nan).astype(np.float32)
        for ax in reversed(range(vol.ndim)):
            cov = _box_axis(cov, ax, F, origin[ax], int(out_shape[ax]))
        data[~(cov > 1.0 - 1e-4)] = np.nan
    return data


# --------------------------------------------------------------------------
# 2. phase correlation, 3. NCC
# --------------------------------------------------------------------------
def _hann_1d(n, shift=0.0):
    """Hann window strictly > 0 on [0, n-1], zero at -1 and n, moved by ``shift``."""
    x = np.arange(n) - float(shift)
    w = np.sin(np.pi * (x + 1.0) / (n + 1.0)) ** 2
    w[(x <= -1.0) | (x >= n)] = 0.0
    return w


def _window3(shape, shift=(0.0, 0.0, 0.0)):
    w = [_hann_1d(n, s) for n, s in zip(shape, shift)]
    return w[0][:, None, None] * w[1][None, :, None] * w[2][None, None, :]


def _prep(x, window, shift=(0.0, 0.0, 0.0)):
    x = np.asarray(x, dtype=np.float64)
    fin = np.isfinite(x)
    if not fin.all():
        x = np.where(fin, x, x[fin].mean() if fin.any() else 0.0)
    if window:
        w = _window3(x.shape, shift)
        return (x - (x * w).sum() / w.sum()) * w
    return x - x.mean()


def _upsampled_corr(X, centre, upsample, region=1.5):
    """(1/N) sum_k X(k) exp(2 pi i f.s) on a 1/upsample grid around ``centre``."""
    n_up = int(math.ceil(region * upsample)) | 1
    offs = (np.arange(n_up) - n_up // 2) / float(upsample)
    grids = []
    out = X
    for ax in reversed(range(X.ndim)):
        s = centre[ax] + offs
        E = np.exp(2j * np.pi * np.outer(s, sfft.fftfreq(X.shape[ax])))
        out = np.moveaxis(np.tensordot(E, out, axes=([1], [ax])), 0, ax)
        grids.insert(0, s)
    return out.real / X.size, grids


def _pc_core(a, b, upsample, window, lowpass, wshift):
    half = 0.5 * np.asarray(wshift, float)
    A = sfft.fftn(_prep(a, window, -half), workers=FFT_WORKERS)
    B = sfft.fftn(_prep(b, window, half), workers=FFT_WORKERS)
    X = np.conj(A) * B
    del A, B
    mag = np.abs(X)
    X /= np.maximum(mag, 1e-12 * mag.max() + 1e-300)
    del mag
    norm = 1.0
    if lowpass:
        f2 = sum(np.meshgrid(*[sfft.fftfreq(n) ** 2 for n in X.shape], indexing="ij", sparse=True))
        w = np.exp(-0.5 * f2 / float(lowpass) ** 2)
        X *= w
        norm = float(w.mean())
    corr = sfft.ifftn(X, workers=FFT_WORKERS).real / norm
    idx = np.unravel_index(int(np.argmax(corr)), corr.shape)
    shape = np.array(corr.shape)
    s0 = np.array(idx, float)
    wrap = s0 > shape // 2
    s0[wrap] -= shape[wrap]
    if not upsample or upsample <= 1:
        return s0, float(corr[idx])
    del corr
    up, grids = _upsampled_corr(X, s0, upsample)
    up /= norm
    j = np.unravel_index(int(np.argmax(up)), up.shape)
    shift = np.array([grids[ax][j[ax]] for ax in range(3)])
    for ax in range(3):
        if 0 < j[ax] < up.shape[ax] - 1:
            jm, jp = list(j), list(j)
            jm[ax] -= 1
            jp[ax] += 1
            cm, c0, cp = up[tuple(jm)], up[j], up[tuple(jp)]
            den = cm - 2 * c0 + cp
            if den < 0:
                shift[ax] += 0.5 * (cm - cp) / den / upsample
    return shift, float(up[j])


def phase_correlate_3d(a, b, upsample=10, window=True, lowpass=PC_LOWPASS, refine=3):
    """3-D phase correlation with sub-voxel peak refinement.

    Returns ``(shift, peak)`` with shift = (dz, dy, dx) such that
    b(x) ~= a(x - shift) (i.e. b is a moved by +shift), and peak the
    normalised correlation at the peak (1 for identical content).

    Both inputs are mean-removed and Hann-windowed (``window``); NaNs are
    replaced by the mean.  Peak: integer argmax, then an upsampled DFT
    (Guizar-Sicairos) over a 1.5-voxel neighbourhood at 1/``upsample``
    resolution, then a per-axis parabolic fit.  A fixed window common to both
    inputs biases the estimate towards zero (~20% of the shift on a 32-voxel
    axis), so ``refine`` passes remove the integer shift by cropping both to
    their overlap and move the two windows with the content (a at -f/2, b at
    +f/2): at the true f the windowed inputs are exact shifts of each other,
    so the fixed point is unbiased.  ``lowpass`` (cycles/voxel, Gaussian
    sigma on the whitened cross-power spectrum; None = pure phase
    correlation) down-weights frequencies where whitening amplifies noise or
    window/interpolation aliasing; 0.15 gave <= 0.035 vox error on smooth
    and noisy synthetic textures versus up to 0.2 vox unweighted.
    """
    a = np.asarray(a)
    b = np.asarray(b)
    if a.shape != b.shape or a.ndim != 3:
        raise ValueError(f"need two 3-D arrays of equal shape, got {a.shape}, {b.shape}")
    s, peak = _pc_core(a, b, upsample, window, lowpass, (0.0, 0.0, 0.0))
    if not (window and refine):
        return s, peak
    N = np.array(a.shape)
    n = np.round(s).astype(int)
    lo, hi = np.maximum(0, -n), np.minimum(N, N - n)
    if np.any(hi - lo < np.minimum(8, N)):
        return s, peak
    if n.any():
        a = a[tuple(slice(l, h) for l, h in zip(lo, hi))]
        b = b[tuple(slice(l + k, h + k) for l, h, k in zip(lo, hi, n))]
    f = s - n
    for _ in range(int(refine)):
        f_new, peak = _pc_core(a, b, upsample, window, lowpass, f)
        step = float(np.max(np.abs(f_new - f)))
        f = f_new
        if step < 2e-3:
            break
    return n + f, peak


def ncc(a, b, mask=None):
    """Pearson normalised cross-correlation over voxels finite in both (and in mask)."""
    a = np.asarray(a, np.float64)
    b = np.asarray(b, np.float64)
    v = np.isfinite(a) & np.isfinite(b)
    if mask is not None:
        v &= np.asarray(mask, bool)
    if v.sum() < 2:
        return float("nan")
    x = a[v] - a[v].mean()
    y = b[v] - b[v].mean()
    den = math.sqrt(float((x * x).sum()) * float((y * y).sum()))
    return float((x * y).sum() / den) if den > 0 else float("nan")


# --------------------------------------------------------------------------
# 4. affine fit of the translation field
# --------------------------------------------------------------------------
def fit_affine(patch_centres, measured_shifts, weights=None, Pm=None, ridge=1e-9):
    """Least squares t(p) = M (p - Pm) + b from per-patch translations (x, y, z).

    Pm defaults to the mean of ``patch_centres``.  A tiny ridge on M keeps
    degenerate (e.g. coplanar) layouts finite; with fewer than 4 patches only
    b is fitted (M = 0).  Returns M, b, Pm, per-patch residuals and their RMS
    (3-D norm, 9 um voxels).
    """
    P = np.asarray(patch_centres, float).reshape(-1, 3)
    T = np.asarray(measured_shifts, float).reshape(-1, 3)
    n = len(P)
    if n == 0:
        raise ValueError("no patches to fit")
    Pm = P.mean(0) if Pm is None else np.asarray(Pm, float).reshape(3)
    w = np.ones(n) if weights is None else np.asarray(weights, float).reshape(n)
    if n < 4:  # translation only
        M = np.zeros((3, 3))
        b = (w[:, None] * T).sum(0) / w.sum()
    else:
        X = np.hstack([P - Pm, np.ones((n, 1))])
        XtW = X.T * w
        A = XtW @ X
        lam = ridge * max(float(np.trace(A[:3, :3])) / 3.0, 1.0)
        A[:3, :3] += lam * np.eye(3)
        beta = np.linalg.solve(A, XtW @ T)
        M = beta[:3].T
        b = beta[3]
    pred = (P - Pm) @ M.T + b
    res = T - pred
    rms = float(np.sqrt(np.mean(np.sum(res ** 2, axis=1))))
    return {"M": M, "b": b, "Pm": Pm, "residuals": res, "rms": rms, "n": n}


# --------------------------------------------------------------------------
# resampling the rescan onto the 9 um grid
# --------------------------------------------------------------------------
def _sample_rescan(reader_can, tr: C6Transform, lo9_zyx, shape_zyx, warp=True, warp_order=3):
    """Rescan (canonical reader) area-resampled onto the 9 um box [lo9, lo9+shape).

    The translation t(p_c) at the block centre is applied exactly through the
    fractional origin of ``downsample_area``; the differential part
    M (p - p_c) (tilts, ~<1 voxel across a block) is applied afterwards on the
    9 um grid by an affine resample of order ``warp_order``.
    """
    F = tr.F
    shape = np.asarray(shape_zyx, int)
    lo9 = np.asarray(lo9_zyx, float)
    pc_zyx = lo9 + (shape - 1) / 2.0
    tc_zyx = tr.t(pc_zyx[::-1])[::-1]
    Mz = tr.M[::-1, ::-1]
    do_warp = bool(warp) and bool(np.any(tr.M != 0))
    m = int(math.ceil(float((np.abs(Mz) @ ((shape - 1) / 2.0)).max()))) + 1 if do_warp else 0
    lo_e = lo9 - m
    shape_e = shape + 2 * m
    q_lo = F * (lo_e + tc_zyx - np.array([tr.z0, 0.0, 0.0]))
    r_lo = np.floor(q_lo - F / 2.0 + 0.5).astype(int) - 1
    r_hi = np.ceil(q_lo + F * (shape_e - 1) + F / 2.0 + 0.5).astype(int) + 1
    if hasattr(reader_can, "read_downsampled"):
        D = reader_can.read_downsampled(r_lo, r_hi, F, q_lo - r_lo, shape_e)
    else:
        D = downsample_area(reader_can(r_lo, r_hi), F, origin=q_lo - r_lo, out_shape=shape_e)
    if not do_warp:
        return D
    offset = m + Mz @ (lo9 - pc_zyx)
    mat = np.eye(3) + Mz
    valid = np.isfinite(D)
    if not valid.all():
        D = np.where(valid, D, D[valid].mean() if valid.any() else 0.0).astype(np.float32)
    out = ndi.affine_transform(D, mat, offset=offset, output_shape=tuple(shape),
                               order=warp_order, mode="nearest")
    if not valid.all():
        vw = ndi.affine_transform(valid.astype(np.float32), mat, offset=offset,
                                  output_shape=tuple(shape), order=1, mode="constant", cval=0.0)
        out[vw < 0.999] = np.nan
    return out


def _block_lo(centre_xyz, block):
    c = np.asarray(centre_xyz, float)[::-1]
    return np.floor(c - (np.asarray(block) - 1) / 2.0 + 0.5).astype(int)


def _measure_patch(r9, rr_can, tr, centre_xyz, block, upsample, warp, lowpass=PC_LOWPASS):
    t0 = time.perf_counter()
    block = np.asarray(block, int)
    lo9 = _block_lo(centre_xyz, block)
    A = r9(lo9, lo9 + block)
    D = _sample_rescan(rr_can, tr, lo9, block, warp=warp)
    valid = float(np.mean(np.isfinite(A) & np.isfinite(D)))
    pc = (lo9 + (block - 1) / 2.0)[::-1]
    if valid < 0.5:
        return {"centre": pc, "valid_frac": valid, "ok": False, "r": float("nan"),
                "peak": 0.0, "delta": np.full(3, np.nan), "t_est": tr.t(pc),
                "t_meas": np.full(3, np.nan), "seconds": time.perf_counter() - t0}
    d, peak = phase_correlate_3d(D, A, upsample=upsample, lowpass=lowpass)
    delta = -d[::-1]  # A(x) = D(x + delta)  =>  t_true = t_est + delta
    r = ncc(A, D)
    t_est = tr.t(pc)
    return {"centre": pc, "valid_frac": valid, "ok": True, "r": r, "peak": peak,
            "delta": delta, "t_est": t_est, "t_meas": t_est + delta,
            "seconds": time.perf_counter() - t0}


def _bin(x, k):
    if k <= 1:
        return x
    x = np.asarray(x, np.float32)
    fin = np.isfinite(x)
    if not fin.all():
        x = np.where(fin, x, x[fin].mean() if fin.any() else 0.0)
    s = [n // k for n in x.shape]
    x = x[: s[0] * k, : s[1] * k, : s[2] * k]
    return x.reshape(s[0], k, s[1], k, s[2], k).mean(axis=(1, 3, 5))


# --------------------------------------------------------------------------
# 5. registration pipeline
# --------------------------------------------------------------------------
def _coarse_orientation(r9, volr_reader, raw_shape, F, z0, cands, cblock, cbin,
                        centre_xyz, upsample):
    cblock = np.asarray(cblock, int)
    L = np.ceil(F * cblock).astype(int) + 4  # canonical rescan extent to read
    cache = {}
    rows = []
    for ori in cands:
        can_shape = np.array(ori.can_shape(raw_shape))
        if centre_xyz is None:
            # centred on the rescan: the raw box is flip-invariant, read once
            Lc = np.minimum(L + ((can_shape - L) % 2), can_shape)
            c_lo = (can_shape - Lc) // 2
            c_hi = c_lo + Lc
        else:
            qc = F * (np.asarray(centre_xyz, float)[::-1] - np.array([z0, 0.0, 0.0]))
            c_lo = np.floor(qc - (L - 1) / 2.0 + 0.5).astype(int)
            c_hi = c_lo + L
        rlo, rhi = ori.raw_box(c_lo, c_hi, raw_shape)
        key = (tuple(rlo), tuple(rhi))
        if key not in cache:
            cache[key] = volr_reader(rlo, rhi)
        raw_blk = cache[key]
        # 9 um grid points whose footprint (b = 0) lies inside the block
        zoff = np.array([z0, 0.0, 0.0])
        p_lo = np.ceil((c_lo - 0.5 + F / 2.0) / F + zoff - 1e-9).astype(int)
        p_hi = np.floor((c_hi - 0.5 - F / 2.0) / F + zoff + 1e-9).astype(int) + 1
        shape = np.minimum(p_hi - p_lo, cblock)
        D = _downsample_oriented(raw_blk, ori, c_hi - c_lo, F, F * (p_lo - zoff) - c_lo, shape)
        A = r9(p_lo, p_lo + shape)
        Db, Ab = _bin(D, cbin), _bin(A, cbin)
        d, peak = phase_correlate_3d(Db, Ab, upsample=upsample)
        delta_zyx = -d * cbin
        Ds = ndi.shift(Db, d, order=1, mode="constant", cval=np.nan)
        r = ncc(Ab, Ds)
        rows.append({"orientation": ori, "ncc": r, "peak": peak,
                     "b0": delta_zyx[::-1].copy(),
                     "centre": (p_lo + (shape - 1) / 2.0)[::-1]})
    return rows


def evaluate_patches(vol9_reader, volr_reader, fit, centres, block=(48, 256, 256),
                     offset=None, upsample=10, warp=True, volr_shape=None):
    """Per-patch NCC r and residual shift (x, y, z) at ``centres`` under ``fit``.

    ``volr_reader`` is the raw rescan reader; the fit's orientation is applied.
    ``offset`` (x, y, z, 9 um voxels) displaces the transform (controls).
    """
    tr = C6Transform.from_fit(fit)
    if offset is not None:
        tr = tr.with_offset(offset)
    raw_shape = volr_shape or tr.raw_shape or getattr(volr_reader, "shape")
    rr = OrientedReader(volr_reader, raw_shape, tr.orientation)
    rows = [_measure_patch(vol9_reader, rr, tr, c, block, upsample, warp) for c in centres]
    return _jsonify(_summarise_check(rows))


def _summarise_check(rows):
    ok = [x for x in rows if x["ok"]]
    rs = np.array([x["r"] for x in ok]) if ok else np.array([np.nan])
    res = np.array([x["delta"] for x in ok]) if ok else np.full((1, 3), np.nan)
    return {
        "patches": [{"centre": x["centre"], "r": x["r"], "residual": x["delta"],
                     "peak": x["peak"], "valid_frac": x["valid_frac"], "ok": x["ok"]}
                    for x in rows],
        "n_ok": len(ok),
        "median_r": float(np.median(rs)),
        "rms": float(np.sqrt(np.mean(np.sum(res ** 2, axis=1)))),
        "median_abs_residual": np.median(np.abs(res), axis=0),
        "seconds_per_patch": float(np.mean([x["seconds"] for x in rows])) if rows else 0.0,
    }


def register(vol9_reader, volr_reader, F, z0_guess, patch_centres_fit, patch_centres_check,
             block=(48, 256, 256), *, volr_shape=None, orientations="flips",
             coarse_block=None, coarse_bin=2, coarse_centre=None, max_iter=3, tol=0.05,
             upsample=10, warp=True, min_peak=0.0, reject_sigma=3.0, reject_floor=1.0,
             log=None):
    """C6 registration of a 9 um volume onto a ~2.4 um rescan.

    Pipeline: orientation (flip) test on a coarse level -> coarse translation
    -> per-patch 3-D phase correlation of ``block`` (zyx, 9 um grid; the
    rescan is read at ~F x the size and area-downsampled) at the fit patches
    -> affine fit of t(p), iterated (patches re-sampled under the current
    transform) until the update < ``tol`` voxels -> check on the NEW check
    patches: per-patch NCC r at the fitted transform and residual shift RMS.

    ``F`` must come from metadata (``scale_factor``).  ``coarse_block``
    defaults to ``block``; ``coarse_centre`` (x, y, z) defaults to the rescan
    centre (one rescan read shared by all flips).  Patch centres are (x, y, z)
    in 9 um voxels.  Bars (median r >= 0.85, RMS <= 1.5 vox) are reported,
    not enforced.  Returns a JSON-serialisable dict.
    """
    t_start = time.perf_counter()
    say = log or (lambda *a: None)
    F = float(F)
    if not (1.0 < F < 50.0):
        raise ValueError(f"implausible F = {F}; compute it with scale_factor(voxel_9, voxel_r)")
    z0 = float(z0_guess)
    block = tuple(int(v) for v in block)
    raw_shape = tuple(int(v) for v in (volr_shape or getattr(volr_reader, "shape")))
    Pf = np.asarray(patch_centres_fit, float).reshape(-1, 3)
    Pc = np.asarray(patch_centres_check, float).reshape(-1, 3)
    Pm = Pf.mean(0)
    cands = candidate_orientations(orientations) if isinstance(orientations, str) else list(orientations)

    # --- orientation test + coarse translation
    rows = _coarse_orientation(vol9_reader, volr_reader, raw_shape, F, z0, cands,
                               coarse_block or block, coarse_bin, coarse_centre, upsample)
    order = sorted(range(len(rows)), key=lambda i: -np.nan_to_num(rows[i]["ncc"], nan=-2))
    best = rows[order[0]]
    ori = best["orientation"]
    margin = best["ncc"] - rows[order[1]]["ncc"] if len(rows) > 1 else float("nan")
    say(f"orientation flips_xyz={ori.flip_signs_xyz()} perm_xyz={ori.perm_xyz()} "
        f"ncc={best['ncc']:.3f} margin={margin:.3f} b0={np.round(best['b0'], 2)}")
    rr = OrientedReader(volr_reader, raw_shape, ori)
    tr = C6Transform(F, z0, np.zeros((3, 3)), best["b0"], Pm, ori, raw_shape)

    # --- per-patch phase correlation + affine, iterated
    history = []
    fit_rows = []
    used = np.zeros(len(Pf), bool)
    af = None
    for it in range(max_iter):
        fit_rows = [_measure_patch(vol9_reader, rr, tr, c, block, upsample, warp) for c in Pf]
        ok = np.array([x["ok"] and x["peak"] >= min_peak for x in fit_rows])
        if ok.sum() == 0:
            raise RuntimeError("no fit patch overlaps both volumes")
        C = np.array([x["centre"] for x in fit_rows])
        T = np.array([x["t_meas"] for x in fit_rows])
        used = ok.copy()
        af = fit_affine(C[used], T[used], Pm=Pm)
        if used.sum() > 5:
            e = np.linalg.norm(T - ((C - Pm) @ af["M"].T + af["b"]), axis=1)
            thr = max(reject_floor, reject_sigma * 1.4826 * float(np.median(e[used])))
            keep = used & (e <= thr)
            if keep.sum() >= 4 and keep.sum() < used.sum():
                used = keep
                af = fit_affine(C[used], T[used], Pm=Pm)
        new = C6Transform(F, z0, af["M"], af["b"], Pm, ori, raw_shape)
        change = float(np.max(np.linalg.norm(new.t(C[used]) - tr.t(C[used]), axis=1)))
        history.append({"iteration": it + 1, "change": change, "residual_rms": af["rms"],
                        "n_used": int(used.sum()),
                        "median_r": float(np.median([x["r"] for x in fit_rows if x["ok"]]))})
        say(f"iter {it + 1}: change={change:.3f} rms={af['rms']:.3f} used={int(used.sum())}")
        tr = new
        if change < tol:
            break

    # residuals of the final measurement set against the final fit
    C = np.array([x["centre"] for x in fit_rows])
    T = np.array([x["t_meas"] for x in fit_rows])
    fres = T - tr.t(C)

    # --- check on NEW patches
    chk_rows = [_measure_patch(vol9_reader, rr, tr, c, block, upsample, warp) for c in Pc]
    chk = _summarise_check(chk_rows)
    if len(Pc) and len(Pf):  # check patches should be NEW locations, not fit patches
        chk["min_distance_to_fit"] = float(np.min(np.linalg.norm(Pc[:, None] - Pf[None], axis=2)))
    say(f"check: median r={chk['median_r']:.3f} rms={chk['rms']:.3f} n={chk['n_ok']}")

    all_secs = [x["seconds"] for x in fit_rows + chk_rows]
    out = {
        "method": "C6",
        "conventions": "points/M/b/Pm/residuals (x,y,z) in 9um voxels; block/boxes (z,y,x); "
                       "q_can = F*(p + M(p-Pm) + b - z0*e_z); q_raw = G q_can + offset",
        "F": F,
        "z0": z0,
        "flips": ori.flip_signs_xyz(),
        "orientation": ori.to_json(raw_shape),
        "M": tr.M,
        "b": tr.b,
        "Pm": Pm,
        "block": list(block),
        "coarse": {
            "block": list(coarse_block or block), "bin": coarse_bin,
            "candidates": [{"flip_signs_xyz": r["orientation"].flip_signs_xyz(),
                            "perm_xyz": r["orientation"].perm_xyz(), "ncc": r["ncc"],
                            "peak": r["peak"], "b0": r["b0"], "centre": r["centre"]}
                           for r in rows],
            "best_ncc": best["ncc"], "ncc_margin": margin, "b0": best["b0"],
        },
        "fit": {
            "patches": [{"centre": x["centre"], "t_meas": x["t_meas"], "residual": fres[i],
                         "r": x["r"], "peak": x["peak"], "valid_frac": x["valid_frac"],
                         "used": bool(used[i])} for i, x in enumerate(fit_rows)],
            "residual_rms": af["rms"],
            "n_used": int(used.sum()),
            "median_r": float(np.median([x["r"] for x in fit_rows if x["ok"]])),
            "history": history,
        },
        "check": chk,
        "median_r": chk["median_r"],
        "rms": chk["rms"],
        "bars": {
            "median_r_min": BAR_MEDIAN_R, "rms_max": BAR_RMS_VOX,
            "median_r_ok": bool(chk["median_r"] >= BAR_MEDIAN_R),
            "rms_ok": bool(chk["rms"] <= BAR_RMS_VOX),
            "pass": bool(chk["median_r"] >= BAR_MEDIAN_R and chk["rms"] <= BAR_RMS_VOX),
        },
        "timing": {"seconds_per_patch": float(np.mean(all_secs)),
                   "total_seconds": time.perf_counter() - t_start},
    }
    return _jsonify(out)


def _jsonify(x):
    if isinstance(x, dict):
        return {str(k): _jsonify(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonify(v) for v in x]
    if isinstance(x, np.ndarray):
        return _jsonify(x.tolist())
    if isinstance(x, (np.bool_, bool)):
        return bool(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        v = float(x)
        return v if math.isfinite(v) else None
    return x


# --------------------------------------------------------------------------
# 6. forward / inverse maps
# --------------------------------------------------------------------------
def map_9_to_r(p, fit, frame="raw"):
    """9 um voxel coords p (..., 3; x, y, z) -> rescan voxel coords (x, y, z).

    ``frame='raw'`` gives coordinates in the stored rescan array (orientation
    applied; needs the rescan shape in ``fit``), ``'canonical'`` before it.
    """
    tr = C6Transform.from_fit(fit)
    p = np.asarray(p, float)
    q = tr.F * (p + tr.t(p) - tr.z0 * _EZ)
    if frame == "canonical":
        return q
    if tr.raw_shape is None:
        raise ValueError("fit has no rescan shape; use frame='canonical'")
    return tr.orientation.can_to_raw(q[..., ::-1], tr.raw_shape)[..., ::-1]


def map_r_to_9(q, fit, frame="raw", tol=1e-10, max_iter=100):
    """Inverse of ``map_9_to_r`` by fixed-point iteration p <- u - t(p),
    u = q_can / F + z0 e_z (converges for |M| << 1)."""
    tr = C6Transform.from_fit(fit)
    q = np.asarray(q, float)
    if frame != "canonical":
        if tr.raw_shape is None:
            raise ValueError("fit has no rescan shape; use frame='canonical'")
        q = tr.orientation.raw_to_can(q[..., ::-1], tr.raw_shape)[..., ::-1]
    u = q / tr.F + tr.z0 * _EZ
    p = u - tr.b
    for _ in range(max_iter):
        p_new = u - tr.t(p)
        if np.max(np.abs(p_new - p), initial=0.0) < tol:
            return p_new
        p = p_new
    return p
