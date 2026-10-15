# Provenance: Project HERCULES | owner the owner | [id removed]
"""Geometry-only handedness rule (SG item 12, task ``handed``).

Physical facts used (no reader):

F1  Recto inward. The written face (recto) of a rolled papyrus is rolled
    facing the umbilicus (organizer docs, villa scrollprize.org
    docs/37_2026_open_problems.md: "it's always rolled facing inward, toward
    the center of the scroll"). A reader must therefore look at the sheet
    from the umbilicus side.
F2  Display parity. With u to the right and v downward on screen,
    dP/du x dP/dv points INTO the screen (right x down = into, in a
    right-handed frame). Hence the viewer is on the umbilicus side iff
    dP/du x dP/dv points outward, i.e. iff det[dP/du, dP/dv, r_out] > 0 in a
    right-handed physical frame. (Official renderer comment, villa
    vc_render_tifxyz.cpp: standard readable orientation has N = dP/dU x dP/dV
    pointing to the OUTSIDE of the scroll.)
F3  Frame parity. The chirality is computed in index coordinates (x, y, z) =
    (array axis named x, y, z). If that frame is left-handed with respect to
    physical space, every determinant changes sign. The parity comes from
    the root catalogue flag ``left_handed_coordinates`` of the volume
    (False -> +1) together with the zarr axis names (must be a permutation of
    z, y, x that names every axis; the mesh stores (x, y, z) by NAME).
F4  Fragments. A detached fragment has no umbilicus; the organizer
    ``text_side`` (e.g. "-y") names the direction the inked face points to.
    The viewer must be on that side, so the rule is the scroll rule with
    n_out := -text_side.

Rule: convention_sign (orient_for_reading) = parity. The z direction
(``z_direction_is_top_to_bottom``) only decides up/down (a 180 degree
rotation, not a mirror): image top = low z iff the flag is True.

Consistency check that needs no reader (F5, weaker, reported not used for the
rule): rolls start outside and end at the core, and text runs left to right,
so moving along the sheet in reading direction goes INWARD (also the villa
renderer comment: "U winding outside->inside"). With text-up N and outward
r, reading direction = r x N, so inward motion rotates about -N. In a frame
of parity P, the measured inward rotation sense w about +z (w = +1: inward is
counter-clockwise x -> y) predicts text-top at low z iff w * P = +1.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict, field
from typing import Any

import numpy as np

from hercules.geometry import level_mesh as L
from hercules.geometry.tifxyz import valid_mask, vertex_normals

# ---------------------------------------------------------------------------
# frame parity and predicted convention from metadata
# ---------------------------------------------------------------------------

AXIS_VEC = {"x": np.array([1.0, 0, 0]), "y": np.array([0, 1.0, 0]), "z": np.array([0, 0, 1.0])}


@dataclass
class FrameInfo:
    parity: int  # +1 right-handed (x, y, z) index frame, -1 left-handed, 0 unknown
    axes: list[str]
    axes_ok: bool
    left_handed_flag: Any
    z_top_to_bottom: Any  # True / False / None (unknown)
    z_ascending_display: Any  # image top = low z (True), high z (False), None unknown
    notes: list[str] = field(default_factory=list)


def frame_info(zattrs: dict | None, props: dict | None) -> FrameInfo:
    """Parity of the named (x, y, z) index frame from the volume's zarr axes
    and the root-catalogue volume properties."""
    notes = []
    axes = []
    if zattrs:
        try:
            axes = [a["name"] for a in zattrs["multiscales"][0]["axes"]]
        except (KeyError, IndexError, TypeError):
            notes.append("zattrs has no multiscales axes")
    axes_ok = sorted(axes) == ["x", "y", "z"]
    if axes and not axes_ok:
        notes.append(f"axis names {axes} are not a permutation of x, y, z")
    if axes_ok and axes != ["z", "y", "x"]:
        notes.append(f"axis order {axes} differs from z,y,x; mesh (x, y, z) is mapped by name")
    lh = (props or {}).get("left_handed_coordinates", None)
    if lh is True:
        parity = -1
    elif lh is False:
        parity = 1
    else:
        parity = 0
        notes.append("left_handed_coordinates missing: parity unknown")
    if not axes_ok:
        parity = 0
    tb = (props or {}).get("z_direction_is_top_to_bottom", None)
    return FrameInfo(parity=parity, axes=axes, axes_ok=axes_ok, left_handed_flag=lh, z_top_to_bottom=tb,
                     z_ascending_display=(None if tb is None else bool(tb)), notes=notes)


def text_side_vector(text_side: str | None) -> np.ndarray | None:
    """'-y' -> (0, -1, 0) etc.; None if absent or unparsable."""
    if not text_side or not isinstance(text_side, str):
        return None
    s = text_side.strip().lower()
    sign = -1.0 if s.startswith("-") else 1.0
    ax = s.lstrip("+-")
    if ax not in AXIS_VEC:
        return None
    return sign * AXIS_VEC[ax]


def predicted_convention(fi: FrameInfo) -> int:
    """convention_sign for orient_for_reading in the index frame (F1-F3): the
    parity itself (0 if unknown)."""
    return int(fi.parity)


# ---------------------------------------------------------------------------
# centre curves from mask slices (CT-mask centroid)
# ---------------------------------------------------------------------------

def slice_centroid_stats(mask: np.ndarray) -> dict:
    """Centroid, area and second-moment shape of one binary slice (y, x)."""
    yy, xx = np.nonzero(mask)
    n = yy.size
    if n == 0:
        return dict(n=0, cx=math.nan, cy=math.nan, ecc=math.nan, fill=math.nan)
    cx, cy = float(xx.mean()), float(yy.mean())
    C = np.cov(np.stack([xx - cx, yy - cy])) if n > 2 else np.eye(2)
    ev = np.sort(np.linalg.eigvalsh(C))
    ratio = float(math.sqrt(max(ev[0], 1e-12) / max(ev[1], 1e-12)))  # minor/major axis ratio, 1 = round
    # fill: mask area over area of the second-moment ellipse (4 pi sqrt(det C)); ~1 for a filled ellipse
    fill = float(n / (4 * math.pi * math.sqrt(max(ev[0] * ev[1], 1e-12))))
    return dict(n=int(n), cx=cx, cy=cy, axis_ratio=ratio, fill=fill)


def gauss_smooth(z: np.ndarray, v: np.ndarray, sigma: float) -> np.ndarray:
    if sigma <= 0 or v.size < 3:
        return v.copy()
    w = np.exp(-0.5 * ((z[:, None] - z[None, :]) / sigma) ** 2)
    return (w @ v) / w.sum(axis=1)


@dataclass
class CentroidTrack:
    z: np.ndarray  # level-0 z of each sampled slice
    cx: np.ndarray  # raw centroids (level-0 voxels), NaN where too small
    cy: np.ndarray
    area: np.ndarray  # pixels at the sampled level
    axis_ratio: np.ndarray
    sx: np.ndarray  # smoothed
    sy: np.ndarray
    level: int
    sigma: float

    @property
    def curve(self) -> L.CentreCurve:
        ok = np.isfinite(self.sx)
        return L.CentreCurve(z=self.z[ok], x=self.sx[ok], y=self.sy[ok])

    def jitter_vox(self) -> float:
        """Median |raw - smoothed| centroid distance (level-0 voxels)."""
        ok = np.isfinite(self.cx)
        if not ok.any():
            return math.nan
        return float(np.median(np.hypot(self.cx[ok] - self.sx[ok], self.cy[ok] - self.sy[ok])))


def centroid_track(planes: dict[float, np.ndarray], level: int, *, thresh: float = 0, sigma: float = 256.0,
                   min_area_frac: float = 0.002, exclude: dict[float, np.ndarray] | None = None) -> CentroidTrack:
    """Centroid per slice of ``planes`` {level-0 z: 2-D level-k array (y, x)}.
    A pixel counts as scroll if > thresh. ``exclude`` {z: bool mask} removes
    pixels (e.g. sealed-window neighbourhoods) BEFORE anything is computed.
    Level-k index i maps to level-0 i*2^k + (2^k - 1)/2."""
    f = 2 ** level
    zs = np.array(sorted(planes))
    cx, cy, area, ar = [], [], [], []
    for z in zs:
        m = np.asarray(planes[z]) > thresh
        if exclude is not None and z in exclude:
            m &= ~exclude[z]
        st = slice_centroid_stats(m)
        area.append(st["n"])
        if st["n"] >= min_area_frac * m.size:
            cx.append(st["cx"] * f + (f - 1) / 2)
            cy.append(st["cy"] * f + (f - 1) / 2)
            ar.append(st["axis_ratio"])
        else:
            cx.append(math.nan)
            cy.append(math.nan)
            ar.append(math.nan)
    cx, cy = np.array(cx), np.array(cy)
    ok = np.isfinite(cx)
    sx = np.full_like(cx, np.nan)
    sy = np.full_like(cy, np.nan)
    if ok.sum():
        sx[ok] = gauss_smooth(zs[ok].astype(float), cx[ok], sigma)
        sy[ok] = gauss_smooth(zs[ok].astype(float), cy[ok], sigma)
    return CentroidTrack(z=zs.astype(float), cx=cx, cy=cy, area=np.array(area), axis_ratio=np.array(ar),
                         sx=sx, sy=sy, level=level, sigma=sigma)


# ---------------------------------------------------------------------------
# per-mesh evaluation
# ---------------------------------------------------------------------------

def chirality_stats(points: np.ndarray, outward, *, min_abs: float = 0.1, keep: np.ndarray | None = None) -> dict:
    """Vote of sign(det[dP/du, dP/dv, r_out]) over vertices with |normalised
    det| > min_abs (and ``keep``). Returns sign, agreement, counts."""
    c = L.chirality_map(points, outward)
    ok = np.isfinite(c)
    if keep is not None:
        ok &= keep
    n_def = int(ok.sum())
    clear = ok & (np.abs(np.nan_to_num(c)) > min_abs)
    n_clear = int(clear.sum())
    if n_clear == 0:
        return dict(sign=0, agreement=math.nan, frac_clear=0.0 if n_def else math.nan, n_clear=0, n_defined=n_def)
    pos = float((c[clear] > 0).mean())
    sign = 1 if pos > 0.5 else (-1 if pos < 0.5 else 0)
    return dict(sign=sign, agreement=max(pos, 1 - pos), frac_clear=n_clear / max(n_def, 1), n_clear=n_clear,
                n_defined=n_def, median_abs=float(np.median(np.abs(c[clear]))))


def sign_agreement(points: np.ndarray, centre_a, centre_b, *, keep: np.ndarray | None = None,
                   cos_thresh: float = 0.3) -> dict:
    """Per-vertex agreement of sign(n . r_out) between two centre curves, on
    vertices clear (|cos| > cos_thresh) under both."""
    n = vertex_normals(points)
    ca = np.einsum("...k,...k->...", n, L.outward_directions(points, centre_a))
    cb = np.einsum("...k,...k->...", n, L.outward_directions(points, centre_b))
    ok = np.isfinite(ca) & np.isfinite(cb) & (np.abs(np.nan_to_num(ca)) > cos_thresh) & (np.abs(np.nan_to_num(cb)) > cos_thresh)
    if keep is not None:
        ok &= keep
    if not ok.any():
        return dict(n=0, agree=math.nan)
    return dict(n=int(ok.sum()), agree=float((np.sign(ca[ok]) == np.sign(cb[ok])).mean()))


def winding_sense(points: np.ndarray, centre, *, keep: np.ndarray | None = None, min_pairs: int = 20) -> dict:
    """Inward rotation sense about +z measured along mesh rows (u direction).

    Along each row, the azimuth phi about c(z) is unwrapped; wherever a row
    covers more than one turn, the vertex at phi + 2 pi (same row) is compared
    with the vertex at phi: its radius must differ by one winding. w = +1 if
    r DEcreases with increasing phi (inward = counter-clockwise, x -> y).
    Returns w = 0 when no row spans a full turn (then only a local slope is
    reported, which ovality makes unreliable)."""
    p = np.asarray(points, np.float64)
    ok = valid_mask(p)
    if keep is not None:
        ok &= keep
    cx, cy = centre(p[..., 2])
    dx, dy = p[..., 0] - cx, p[..., 1] - cy
    r = np.hypot(dx, dy)
    phi = np.arctan2(dy, dx)
    dr_turn = []
    slopes = []
    span_max = 0.0
    for i in range(p.shape[0]):
        cols = np.nonzero(ok[i])[0]
        if cols.size < 3:
            continue
        # contiguous runs only
        breaks = np.nonzero(np.diff(cols) > 1)[0]
        for run in np.split(cols, breaks + 1):
            if run.size < 3:
                continue
            ph = np.unwrap(phi[i, run])
            rr = r[i, run]
            span = ph.max() - ph.min()
            span_max = max(span_max, span)
            if np.ptp(ph) > 1e-6:
                A = np.stack([ph, np.ones_like(ph)], 1)
                slopes.append(np.linalg.lstsq(A, rr, rcond=None)[0][0])
            if span <= 2 * np.pi:
                continue
            # ph is monotone for a spiral row; pair each vertex with the one a turn later
            order = np.argsort(ph)
            phs, rs = ph[order], rr[order]
            tgt = phs + 2 * np.pi
            j = np.searchsorted(phs, tgt)
            m = j < phs.size
            if m.any():
                jj = j[m]
                # linear interpolation of r at exactly phi + 2 pi
                j0 = np.clip(jj - 1, 0, phs.size - 1)
                t = (tgt[m] - phs[j0]) / np.maximum(phs[jj] - phs[j0], 1e-12)
                r2 = rs[j0] + t * (rs[jj] - rs[j0])
                dr_turn.extend(list(r2 - rs[m]))
    dr_turn = np.array(dr_turn)
    out = dict(max_row_span_turns=span_max / (2 * np.pi), n_pairs=int(dr_turn.size),
               local_slope_median=(float(np.median(slopes)) if slopes else math.nan))
    if dr_turn.size >= min_pairs:
        frac_neg = float((dr_turn < 0).mean())
        out.update(w=(1 if frac_neg > 0.5 else -1), agreement=max(frac_neg, 1 - frac_neg),
                   dr_per_turn_median=float(np.median(dr_turn)))
    else:
        out.update(w=0, agreement=math.nan, dr_per_turn_median=math.nan)
    return out


@dataclass
class MeshPrediction:
    name: str
    convention_sign: int  # predicted legible chirality in the index frame (= parity), 0 unknown
    native_chirality: dict  # chirality stats of the ORGANIZER (u, v) grid vs r_out
    native_legible: Any  # True: organizer grid displayed as stored (u right, v down) reads unmirrored
    mirror_u_needed: Any  # after putting low/high z on top, must u be mirrored? (per orient_for_reading)
    flip_v_needed: Any
    z_ascending_display: Any
    r_out_source: str
    flags: list[str]
    extra: dict

    def to_json(self) -> dict:
        return asdict(self)


def predict_mesh(name: str, points: np.ndarray, outward, fi: FrameInfo, *, r_out_source: str,
                 keep: np.ndarray | None = None, min_agreement: float = 0.9, min_clear: float = 0.5,
                 extra: dict | None = None) -> MeshPrediction:
    """Predicted mirror state of an organizer mesh from geometry and metadata.
    ``outward`` is a CentreCurve (scrolls) or a fixed (3,) vector (fragments:
    -text_side). ``keep`` restricts the vertices that may vote."""
    flags = []
    conv = predicted_convention(fi)
    if conv == 0:
        flags.append("parity unknown")
    cs = chirality_stats(points, outward, keep=keep)
    if cs["sign"] == 0:
        flags.append("chirality undetermined (r_out undetermined)")
    elif cs["agreement"] < min_agreement:
        flags.append(f"chirality vote agreement {cs['agreement']:.3f} < {min_agreement}")
    if cs.get("frac_clear", 0) == cs.get("frac_clear", 0) and cs.get("frac_clear", 0) < min_clear:
        flags.append(f"clear fraction {cs.get('frac_clear', 0):.3f} < {min_clear}")
    native_legible = None
    mirror_u = None
    flip_v = None
    if conv and cs["sign"]:
        native_legible = bool(cs["sign"] == conv)
        # orient_for_reading logic without touching pixels: flip_v from the z trend of rows
        p = np.asarray(points, np.float64)
        ok = valid_mask(p) if keep is None else valid_mask(p) & keep
        dzv = (p[1:, :, 2] - p[:-1, :, 2])[ok[1:] & ok[:-1]]
        trend_v = float(np.median(dzv)) if dzv.size else 0.0
        if fi.z_ascending_display is not None and trend_v != 0.0:
            flip_v = bool((trend_v > 0) != bool(fi.z_ascending_display))
            current = -cs["sign"] if flip_v else cs["sign"]
            mirror_u = bool(current != conv)
        else:
            flags.append("up/down unknown (z_direction_is_top_to_bottom null) or rows not z-graded")
    return MeshPrediction(name=name, convention_sign=conv, native_chirality=cs, native_legible=native_legible,
                          mirror_u_needed=mirror_u, flip_v_needed=flip_v, z_ascending_display=fi.z_ascending_display,
                          r_out_source=r_out_source, flags=flags, extra=dict(extra or {}))


def confidence(pred: MeshPrediction, source_agreements: list[float]) -> str:
    """HIGH: parity known, chirality agreement >= 0.98 and every independent
    r_out source agrees on >= 0.95 of clear vertices; MEDIUM: parity known,
    agreement >= 0.9 and sources (if any) >= 0.8; else FLAG."""
    cs = pred.native_chirality
    if pred.convention_sign == 0 or cs["sign"] == 0:
        return "FLAG"
    ag = [a for a in source_agreements if a == a]
    if cs["agreement"] >= 0.98 and ag and min(ag) >= 0.95:
        return "HIGH"
    if cs["agreement"] >= 0.9 and (not ag or min(ag) >= 0.8):
        return "MEDIUM"
    return "FLAG"
