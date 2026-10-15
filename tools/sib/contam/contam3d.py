# Provenance: Project HERCULES | owner the owner | [id removed]
"""3-D contamination and fold/shell tools (sibling task "contam").

Builds on ``hercules.geometry.contamination`` (METRIC-HASH-0, left unchanged)
and adds what the FL-09 certificate (SG item 8) and integrity rule I7 need:

* ``DenseSurface``: a tifxyz grid densified k x k (default 5 x 5) with
  per-point normals, canvas coordinates, area weights and a RIGOROUS
  sampling bound ``h`` (every point of the bilinear surface lies within ``h``
  vox of some sample).
* ``same_papyrus_nd``: KD-tree same-sheet test on the NORMAL distance
  (point-to-tangent-plane), which does not depend on the sampling density.
* ``papyrus_units``: connected components of the same-papyrus graph; the
  grouping uses geometry only, never segment names or IDs.
* ``clearance``: min 3-D distance between an evaluation region and a set of
  training patches across all windings and re-traces, with a certified lower
  bound (raw min minus both sampling bounds) and the offending points.
* ``fl09_certificate``: SG item 8 for a candidate rectangle R against a
  checkpoint's training-patch registry.

Coordinates: mesh points are (x, y, z) in voxels of the canvas volume; a
canvas pixel (x, y) of a tifxyz with meta scale (su, sv) sits at grid
(row, col) = (y * sv, x * su). Voxel sizes come from the volume
metadata.json, never assumed.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from hercules.geometry.contamination import same_papyrus as same_papyrus_vertex
from hercules.geometry.tifxyz import TifxyzMesh, densify, quad_valid_mask, read_tifxyz, valid_mask, vertex_normals

import ref_surface as RS  # vendored CORR-RETRACE-RULE form (b), same directory

PROVENANCE = "Provenance: Project HERCULES | owner the owner | [id removed]"

# same-papyrus rule (task contam item 1; RCBANK-1 used the same bins)
SP_RADIUS_VOX = 6.0       # Euclidean search radius for the tangent-plane test
SP_MIN_WITHIN_2 = 1000    # points with normal distance < 2 vox
SP_RATIO = 2.0            # count[0,1) >= ratio * count[2,3)


# ---------------------------------------------------------------------------
# hashing helpers
# ---------------------------------------------------------------------------

def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(obj) -> str:
    """sha256 of the canonical JSON encoding (sorted keys, no spaces)."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def mesh_hashes(mesh_dir: str | Path) -> dict:
    d = Path(mesh_dir)
    return {n: sha256_file(d / n) for n in ("x.tif", "y.tif", "z.tif", "meta.json") if (d / n).exists()}


# ---------------------------------------------------------------------------
# dense surfaces
# ---------------------------------------------------------------------------

def quad_sampling_bounds(points: np.ndarray) -> np.ndarray:
    """(H-1, W-1) array: for each valid quad, the max distance from any point
    of its bilinear surface to the nearest of its four corners (0 for invalid
    quads).

    For a bilinear quad and a corner c with edge vectors e1, e2 and diagonal
    vector d from c, the points whose nearest parameter corner is c have
    s, t <= 1/2 and P - c = s(1-t) e1 + t(1-s) e2 + st d. For fixed t this is
    affine in s, so |P - c| is convex in s (and likewise in t); its maximum over
    [0, 1/2]^2 is therefore at a corner of that square:
    max(|e1|/2, |e2|/2, |e1 + e2 + d|/4). The quad bound is the max over its
    four corners (exact for a planar parallelogram: half its long diagonal).
    """
    p = np.asarray(points, dtype=np.float64)
    qv = quad_valid_mask(p)
    out = np.zeros(qv.shape)
    if not qv.any():
        return out
    c = [p[:-1, :-1][qv], p[:-1, 1:][qv], p[1:, :-1][qv], p[1:, 1:][qv]]  # 00 01 10 11
    best = np.zeros(c[0].shape[0])
    nrm = lambda v: np.linalg.norm(v, axis=-1)  # noqa: E731
    # (corner, u-neighbour, v-neighbour, diagonal)
    for k0, ku, kv, kd in ((0, 1, 2, 3), (1, 0, 3, 2), (2, 3, 0, 1), (3, 2, 1, 0)):
        e1, e2, dd = c[ku] - c[k0], c[kv] - c[k0], c[kd] - c[k0]
        best = np.maximum(best, np.maximum(np.maximum(nrm(e1) / 2, nrm(e2) / 2), nrm(e1 + e2 + dd) / 4))
    out[qv] = best
    return out


def quad_sampling_bound(points: np.ndarray) -> float:
    """Max of ``quad_sampling_bounds`` (0 for a grid without valid quads): every
    point of the grid's bilinear surface lies within this distance of a vertex."""
    q = quad_sampling_bounds(points)
    return float(q.max()) if q.size else 0.0


def vertex_sampling_bounds(points: np.ndarray) -> np.ndarray:
    """(H, W): per vertex, the max bound of the valid quads it is a corner of.
    Every point of a quad lies within that quad's bound of one of its corners,
    and each corner's value is >= that bound, so a surface point x is within
    hs[c] of some sample c."""
    q = quad_sampling_bounds(points)
    H, W = np.asarray(points).shape[:2]
    v = np.zeros((H, W))
    if q.size:
        v[:-1, :-1] = np.maximum(v[:-1, :-1], q)
        v[:-1, 1:] = np.maximum(v[:-1, 1:], q)
        v[1:, :-1] = np.maximum(v[1:, :-1], q)
        v[1:, 1:] = np.maximum(v[1:, 1:], q)
    return v


def vertex_area_weights(points: np.ndarray) -> np.ndarray:
    """(H, W) area weights: each valid quad's area (two triangles, as
    ``tifxyz.area_vox2``) split equally among its four corners. The weights sum
    to the mesh area."""
    p = np.asarray(points, dtype=np.float64)
    qv = quad_valid_mask(p)
    p00, p01, p10, p11 = p[:-1, :-1], p[:-1, 1:], p[1:, :-1], p[1:, 1:]
    qa = 0.5 * (np.linalg.norm(np.cross(p01 - p00, p10 - p00), axis=-1)
                + np.linalg.norm(np.cross(p01 - p11, p10 - p11), axis=-1))
    qa = np.where(qv, qa, 0.0) / 4.0
    w = np.zeros(p.shape[:2])
    w[:-1, :-1] += qa
    w[:-1, 1:] += qa
    w[1:, :-1] += qa
    w[1:, 1:] += qa
    return w


@dataclass
class DenseSurface:
    """Valid samples of a k x k densified tifxyz grid.

    points  (N, 3) float64 voxel coordinates
    normals (N, 3) unit normals (NaN rows where not computable)
    canvas  (N, 2) canvas pixel coordinates (x, y) of each sample
    area    (N,)   surface area represented by each sample (vox^2)
    h       sampling bound: every point of the bilinear surface of the selected
            dense quads lies within h vox of some sample
    """

    points: np.ndarray
    normals: np.ndarray
    canvas: np.ndarray
    area: np.ndarray
    h: float
    k: int
    name: str = ""
    meta: dict = field(default_factory=dict)
    hs: np.ndarray | None = None  # per-sample local bound (<= h); None -> h everywhere

    def local_h(self) -> np.ndarray:
        return np.full(self.n, self.h) if self.hs is None else self.hs

    @property
    def n(self) -> int:
        return int(self.points.shape[0])

    def subset(self, mask: np.ndarray, name: str | None = None) -> "DenseSurface":
        return DenseSurface(self.points[mask], self.normals[mask], self.canvas[mask], self.area[mask],
                            self.h, self.k, self.name if name is None else name, dict(self.meta),
                            None if self.hs is None else self.hs[mask])

    @staticmethod
    def concat(parts: Sequence["DenseSurface"], name: str = "") -> "DenseSurface":
        parts = [p for p in parts if p.n]
        if not parts:
            z = np.zeros((0, 3))
            return DenseSurface(z, z.copy(), np.zeros((0, 2)), np.zeros(0), 0.0, 0, name)
        return DenseSurface(np.concatenate([p.points for p in parts]), np.concatenate([p.normals for p in parts]),
                            np.concatenate([p.canvas for p in parts]), np.concatenate([p.area for p in parts]),
                            max(p.h for p in parts), max(p.k for p in parts), name,
                            hs=np.concatenate([p.local_h() for p in parts]))


def dense_surface(points: np.ndarray, scale: tuple[float, float] = (0.05, 0.05), k: int = 5, *,
                  rect_px: Sequence[float] | None = None, name: str = "") -> DenseSurface:
    """Densify an (H, W, 3) grid k x k (bilinear) and return its valid samples.

    ``rect_px`` = [x0, y0, x1, y1] (canvas pixels, half-open) restricts the
    result to the dense quads that intersect the rectangle (a superset of the
    rectangle's surface, so every distance computed from it is conservative).
    Only the grid quads touching the rectangle are densified.
    """
    p = np.asarray(points, dtype=np.float64)
    su, sv = float(scale[0]), float(scale[1])
    H, W = p.shape[:2]
    r0 = c0 = 0
    if rect_px is not None:
        x0, y0, x1, y1 = (float(v) for v in rect_px)
        # grid index range whose quads intersect [x0, x1) x [y0, y1)
        c0 = max(0, int(math.floor(x0 * su)))
        c1 = min(W - 1, int(math.ceil((x1 - 1) * su)) + 0)
        r0 = max(0, int(math.floor(y0 * sv)))
        r1 = min(H - 1, int(math.ceil((y1 - 1) * sv)))
        c1 = max(c1, c0 + 1) if W > 1 else c0
        r1 = max(r1, r0 + 1) if H > 1 else r0
        c1, r1 = min(c1, W - 1), min(r1, H - 1)
        p = p[r0:r1 + 1, c0:c1 + 1]
    if p.shape[0] < 2 or p.shape[1] < 2:
        z = np.zeros((0, 3))
        return DenseSurface(z, z.copy(), np.zeros((0, 2)), np.zeros(0), 0.0, k, name)
    d = densify(p, k).astype(np.float64)
    ok = valid_mask(d)
    nrm = vertex_normals(d)
    area = vertex_area_weights(d)
    rr, cc = np.nonzero(ok)
    canvas = np.stack([(c0 + cc / k) / su, (r0 + rr / k) / sv], axis=-1)
    pts = d[ok]
    keep = np.ones(pts.shape[0], dtype=bool)
    if rect_px is not None:
        step_x, step_y = 1.0 / (su * k), 1.0 / (sv * k)
        x0, y0, x1, y1 = (float(v) for v in rect_px)
        keep = ((canvas[:, 0] >= x0 - step_x) & (canvas[:, 0] <= (x1 - 1) + step_x)
                & (canvas[:, 1] >= y0 - step_y) & (canvas[:, 1] <= (y1 - 1) + step_y))
    a = area[ok]
    hs = vertex_sampling_bounds(d)[ok][keep]
    # h = max over the KEPT samples' local bounds (each kept sample bounds every
    # quad it is a corner of, and every quad meeting the selection has all four
    # corners kept)
    return DenseSurface(pts[keep], nrm[ok][keep], canvas[keep], a[keep], float(hs.max()) if hs.size else 0.0, k,
                        name, hs=hs)


def dense_from_mesh(mesh: TifxyzMesh, k: int = 5, rect_px=None, name: str = "") -> DenseSurface:
    return dense_surface(mesh.points, mesh.scale, k, rect_px=rect_px, name=name or mesh.uuid)


# ---------------------------------------------------------------------------
# same-papyrus test on the normal distance
# ---------------------------------------------------------------------------

@dataclass
class SamePapyrusND:
    counts: tuple[int, int, int]   # A samples with normal distance in [0,1), [1,2), [2,3)
    n_within_2: int                # A samples with normal distance < 2 (and a B sample within radius)
    area_within_2_vox2: float      # surface area of those A samples
    frac_of_a: float               # area fraction of A that is same-sheet with B
    same: bool
    n_a: int
    nd_median: float
    nd_p90: float
    mask: np.ndarray | None = None  # per-A-sample flag (normal distance < 2)

    def as_dict(self) -> dict:
        return dict(counts=list(self.counts), n_within_2=self.n_within_2,
                    area_within_2_vox2=self.area_within_2_vox2, frac_of_a=self.frac_of_a, same=self.same,
                    n_a=self.n_a, nd_median=self.nd_median, nd_p90=self.nd_p90)


def normal_distances(A: DenseSurface, B: DenseSurface, *, radius: float = SP_RADIUS_VOX, knn: int = 8,
                     workers: int = 1, tree_B: cKDTree | None = None) -> np.ndarray:
    """For every A sample: min over the B samples within ``radius`` (Euclidean,
    up to ``knn`` nearest) of |(a - b) . n_b|; inf where no B sample is within
    radius."""
    out = np.full(A.n, np.inf)
    if A.n == 0 or B.n == 0:
        return out
    tree = tree_B if tree_B is not None else cKDTree(B.points)
    kk = min(knn, B.n)
    d, idx = tree.query(A.points, k=kk, distance_upper_bound=radius, workers=workers)
    if kk == 1:
        d, idx = d[:, None], idx[:, None]
    hit = np.isfinite(d)
    nb_ok = np.isfinite(B.normals).all(-1)
    for j in range(kk):
        m = hit[:, j]
        if not m.any():
            continue
        ii = idx[m, j]
        good = nb_ok[ii]
        rows = np.nonzero(m)[0][good]
        ii = ii[good]
        nd = np.abs(np.einsum("ij,ij->i", A.points[rows] - B.points[ii], B.normals[ii]))
        out[rows] = np.minimum(out[rows], nd)
    return out


def same_papyrus_nd(A: DenseSurface, B: DenseSurface, *, radius: float = SP_RADIUS_VOX,
                    min_within_2: int = SP_MIN_WITHIN_2, ratio: float = SP_RATIO, workers: int = 1,
                    tree_B: cKDTree | None = None, keep_mask: bool = False) -> SamePapyrusND:
    """SAME iff (#A samples with normal distance < 2 vox to B, B within
    ``radius`` vox) >= ``min_within_2`` AND count[0,1) >= ``ratio`` * count[2,3).

    A crossing (different sheets that intersect) spreads its normal distances
    evenly over [0, 3) and fails the ratio; a parallel sheet 2-3 vox away fails
    it too; an adjacent winding (> radius away) has no candidates at all.
    """
    nd = normal_distances(A, B, radius=radius, workers=workers, tree_B=tree_B)
    c0 = int(np.sum(nd < 1.0))
    c1 = int(np.sum((nd >= 1.0) & (nd < 2.0)))
    c2 = int(np.sum((nd >= 2.0) & (nd < 3.0)))
    w2 = nd < 2.0
    area = float(A.area[w2].sum())
    tot = float(A.area.sum()) if A.n else 0.0
    fin = nd[np.isfinite(nd) & (nd < 3.0)]
    same = (c0 + c1) >= min_within_2 and c0 >= ratio * c2
    return SamePapyrusND((c0, c1, c2), c0 + c1, area, area / tot if tot > 0 else 0.0, bool(same), A.n,
                         float(np.median(fin)) if fin.size else math.nan,
                         float(np.percentile(fin, 90)) if fin.size else math.nan,
                         w2 if keep_mask else None)


# ---------------------------------------------------------------------------
# papyrus units
# ---------------------------------------------------------------------------

def _bbox(p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return p.min(0), p.max(0)


def bbox_gap(a: DenseSurface, b: DenseSurface) -> float:
    """Lower bound of the 3-D distance between two clouds from their bboxes."""
    if a.n == 0 or b.n == 0:
        return math.inf
    (alo, ahi), (blo, bhi) = _bbox(a.points), _bbox(b.points)
    gap = np.maximum(0.0, np.maximum(alo - bhi, blo - ahi))
    return float(np.linalg.norm(gap))


@dataclass
class PairResult:
    a: str
    b: str
    ab: SamePapyrusND
    ba: SamePapyrusND

    @property
    def same(self) -> bool:
        return self.ab.same or self.ba.same

    def as_dict(self) -> dict:
        return dict(a=self.a, b=self.b, same=self.same, a_in_b=self.ab.as_dict(), b_in_a=self.ba.as_dict())


def raw_vertices(points: np.ndarray) -> np.ndarray:
    """Valid vertices of an (H, W, 3) grid, float64 (N, 3)."""
    p = np.asarray(points, dtype=np.float64)
    return p[valid_mask(p)]


def near_mask(X: DenseSurface, raw_tree: cKDTree, bound: float, workers: int = 1) -> np.ndarray:
    """X samples within ``bound`` of any raw vertex in ``raw_tree``."""
    if X.n == 0:
        return np.zeros(0, dtype=bool)
    d, _ = raw_tree.query(X.points, k=1, distance_upper_bound=bound, workers=workers)
    return np.isfinite(d)


def pair_same_papyrus(A: DenseSurface, B: DenseSurface, rawA: np.ndarray, rawB: np.ndarray, hA: float, hB: float,
                      *, radius: float = SP_RADIUS_VOX, workers: int = 1, names=("A", "B"),
                      keep_mask: bool = False) -> PairResult | None:
    """Both-direction same-papyrus test with an exact prefilter.

    hA / hB are the sampling bounds of the RAW grids. Any B sample within
    ``radius`` of an A sample lies within radius + hA of a raw A vertex (and
    vice versa), so testing only those subsets gives the identical result.
    Returns None if the raw grids never come within radius + hA + hB.
    """
    if rawA.shape[0] == 0 or rawB.shape[0] == 0:
        return None
    tA, tB = cKDTree(rawA), cKDTree(rawB)
    d, _ = tB.query(rawA, k=1, distance_upper_bound=radius + hA + hB, workers=workers)
    if not np.isfinite(d).any():
        return None
    mA = near_mask(A, tB, radius + hB, workers)
    mB = near_mask(B, tA, radius + hA, workers)
    As, Bs = A.subset(mA), B.subset(mB)
    out = []
    for X, Xs, mX, Ys in ((A, As, mA, Bs), (B, Bs, mB, As)):
        r = same_papyrus_nd(Xs, Ys, radius=radius, workers=workers, keep_mask=keep_mask)
        tot = float(X.area.sum())
        r.frac_of_a = r.area_within_2_vox2 / tot if tot > 0 else 0.0
        r.n_a = X.n
        if keep_mask:
            full = np.zeros(X.n, dtype=bool)
            full[np.nonzero(mX)[0][r.mask]] = True
            r.mask = full
        out.append(r)
    return PairResult(names[0], names[1], out[0], out[1])


def pairwise_same_papyrus(surfaces: Mapping[str, DenseSurface], raw: Mapping[str, np.ndarray],
                          h_raw: Mapping[str, float], *, workers: int = 1, radius: float = SP_RADIUS_VOX,
                          log=None) -> list[PairResult]:
    """Test every unordered pair of surfaces (both directions). ``surfaces`` may
    be any mapping, including a lazy loader (only ``__getitem__`` is used for
    the pairs that pass the raw screen); ``raw`` holds the raw grid vertices
    and ``h_raw`` the raw sampling bounds. Pairs that never come within
    radius are omitted (they cannot be SAME)."""
    names = list(raw)
    res: list[PairResult] = []
    for i, na in enumerate(names):
        for nb in names[i + 1:]:
            ra, rb = raw[na], raw[nb]
            if ra.shape[0] == 0 or rb.shape[0] == 0:
                continue
            (alo, ahi), (blo, bhi) = _bbox(ra), _bbox(rb)
            gap = float(np.linalg.norm(np.maximum(0.0, np.maximum(alo - bhi, blo - ahi))))
            if gap > radius + h_raw[na] + h_raw[nb]:
                continue
            tA = cKDTree(ra)
            d, _ = tA.query(rb, k=1, distance_upper_bound=radius + h_raw[na] + h_raw[nb], workers=workers)
            if not np.isfinite(d).any():
                continue
            pr = pair_same_papyrus(surfaces[na], surfaces[nb], ra, rb, h_raw[na], h_raw[nb], radius=radius,
                                   workers=workers, names=(na, nb))
            if pr is None:
                continue
            if log is not None:
                log(pr)
            res.append(pr)
    return res


# ---------------------------------------------------------------------------
# CORR-RETRACE-RULE: SAME iff (a) vertex form OR (b) surface form (fail closed)
# ---------------------------------------------------------------------------

def _near_crop(G: np.ndarray, other_raw_tree: cKDTree, bound: float, workers: int = 1):
    """Rows/cols window of dense grid G containing every valid vertex within
    ``bound`` of the other mesh's raw vertices (1-cell margin); None if none."""
    v = valid_mask(G)
    rr, cc = np.nonzero(v)
    if rr.size == 0:
        return None
    d, _ = other_raw_tree.query(G[v], k=1, distance_upper_bound=bound, workers=workers)
    hit = np.isfinite(d)
    if not hit.any():
        return None
    r0, r1 = max(0, rr[hit].min() - 1), min(G.shape[0], rr[hit].max() + 2)
    c0, c1 = max(0, cc[hit].min() - 1), min(G.shape[1], cc[hit].max() + 2)
    near = np.zeros(G.shape[:2], dtype=bool)
    near[rr[hit], cc[hit]] = True
    return (r0, r1, c0, c1), near


def corrected_direction(A_grid: np.ndarray, B_grid: np.ndarray, workers: int = 1,
                        a_mask: np.ndarray | None = None) -> dict:
    """Both CORR-RETRACE-RULE forms for A tested against B, on dense grids.

    (a) vertex: hercules.geometry.contamination.same_papyrus (nearest densified
        B vertex, literal rule); (b) surface: vendored tribunal
        same_papyrus_surface (nearest point of B's triangulated dense surface).
    ``a_mask`` restricts A to the samples that can be within reach of B (the
    others have no B point within 3 vox, so the counts are unchanged).
    """
    A = A_grid[valid_mask(A_grid) & (a_mask if a_mask is not None else True)].astype(np.float64)
    if A.shape[0] == 0 or not valid_mask(B_grid).any():
        z = {"counts": [0, 0, 0], "n_within_2": 0, "same": False}
        return {"vertex": z, "surface": dict(z), "same": False}
    lit = same_papyrus_vertex(A, B_grid, workers=workers)
    surf = RS.same_papyrus_surface(A, B_grid, workers=workers)
    return {"vertex": {"counts": list(lit.counts), "n_within_2": lit.n_within_2, "same": bool(lit.same)},
            "surface": {"counts": surf["counts"], "n_within_2": surf["n_within_2"], "same": bool(surf["same"])},
            "same": bool(lit.same or surf["same"])}


def _tight(SX: np.ndarray, mX: np.ndarray, SY: np.ndarray, workers: int = 1) -> np.ndarray:
    vY = valid_mask(SY)
    vX = valid_mask(SX) & mX
    out = np.zeros(SX.shape[:2], dtype=bool)
    if not vY.any() or not vX.any():
        return out
    d, _ = cKDTree(SY[vY]).query(SX[vX], k=1, distance_upper_bound=3.0 + quad_sampling_bound(SY) + 1e-6,
                                 workers=workers)
    rr, cc = np.nonzero(vX)
    hit = np.isfinite(d)
    out[rr[hit], cc[hit]] = True
    return out


def corrected_pair(ptsA: np.ndarray, ptsB: np.ndarray, k: int = 5, *, workers: int = 1,
                   reach: float = SP_RADIUS_VOX, kB: int | None = None) -> dict | None:
    """Both directions of the corrected rule for two RAW (H, W, 3) grids,
    densified k x k. Exact prefilter: only the part of each dense grid within
    ``reach`` + the other's raw sampling bound of the other's raw vertices is
    used (every distance that can enter the 3 vox bins lies inside it).
    None if the meshes never come that close."""
    ra, rb = raw_vertices(ptsA), raw_vertices(ptsB)
    if ra.shape[0] == 0 or rb.shape[0] == 0:
        return None
    ha, hb = quad_sampling_bound(ptsA), quad_sampling_bound(ptsB)
    tA, tB = cKDTree(ra), cKDTree(rb)
    GA = densify(ptsA, k).astype(np.float64)
    GB = densify(ptsB, k if kB is None else kB).astype(np.float64)
    ca = _near_crop(GA, tB, reach + hb, workers)
    cb = _near_crop(GB, tA, reach + ha, workers)
    if ca is None or cb is None:
        return None
    (a0, a1, a2, a3), nA = ca
    (b0, b1, b2, b3), nB = cb
    SA, SB = GA[a0:a1, a2:a3], GB[b0:b1, b2:b3]
    mA, mB = nA[a0:a1, a2:a3], nB[b0:b1, b2:b3]
    # second exact mask: a point within 3 vox of the other's SURFACE lies within
    # 3 + h(other crop) of one of its dense vertices (both forms bin only < 3 vox)
    mA = _tight(SA, mA, SB, workers)
    mB = _tight(SB, mB, SA, workers)
    return {"a_in_b": corrected_direction(SA, SB, workers, mA),
            "b_in_a": corrected_direction(SB, SA, workers, mB),
            "n_a": int(valid_mask(GA).sum()), "n_b": int(valid_mask(GB).sum())}


def papyrus_units(names: Sequence[str], pairs: Iterable[PairResult]) -> list[list[str]]:
    """Connected components of the SAME graph (edge if SAME in either direction).
    Depends only on geometry: relabelling the inputs permutes the output names
    but never changes the partition. Units are sorted by their smallest
    member for a stable listing."""
    idx = {n: i for i, n in enumerate(names)}
    r, c = [], []
    for p in pairs:
        if p.same:
            r.append(idx[p.a])
            c.append(idx[p.b])
    n = len(names)
    g = coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n))
    _, lab = connected_components(g, directed=False)
    units: dict[int, list[str]] = {}
    for nm, l in zip(names, lab):
        units.setdefault(int(l), []).append(nm)
    return sorted((sorted(u) for u in units.values()), key=lambda u: u[0])


# ---------------------------------------------------------------------------
# clearance (fold/shell) certificate
# ---------------------------------------------------------------------------

@dataclass
class Clearance:
    raw_min: float                 # min sample-to-sample distance
    certified_min: float           # lower bound on the true surface distance
    threshold: float
    passed: bool                   # certified_min >= threshold
    h_region: float
    h_train: float
    per_patch: dict                # patch id -> dict(raw_min, certified_min, n_offending)
    offending: list                # up to max_offending closest (train, region) sample pairs below threshold
    n_offending_train_samples: int

    def as_dict(self) -> dict:
        return dict(raw_min=self.raw_min, certified_min=self.certified_min, threshold=self.threshold,
                    passed=self.passed, h_region=self.h_region, h_train=self.h_train, per_patch=self.per_patch,
                    n_offending_train_samples=self.n_offending_train_samples, offending=self.offending)


def clearance(region: DenseSurface, training: Mapping[str, DenseSurface], threshold: float = 128.0, *,
              workers: int = 1, max_offending: int = 50, approx_eps: float = 0.05) -> Clearance:
    """Certify that every point of the region's surface is >= ``threshold`` vox
    (3-D Euclidean) from every point of every training surface.

    3-D distance covers every winding and every re-trace: an adjacent winding
    20-40 vox away and a re-trace 0-2 vox away are both inside a 128 vox ball.
    Each training sample i carries its local sampling bound h_i (every point
    of the quads it is a corner of lies within h_i of a sample) and the region
    its bound h_R, so the true surface distance is >= min_i (d_i - h_i) - h_R
    (triangle inequality); PASS (certified_min >= threshold) is therefore
    rigorous for the bilinear surfaces. A training sample is "offending" when
    d_i - h_i - h_R < threshold (it cannot be certified). Distances below that bound are
    exact; when a patch has none, its min is reported from a (1+eps)-approximate
    query and certified from the rigorous lower bound max(bound, min/(1+eps)).
    """
    if region.n == 0:
        raise ValueError("region has no valid samples")
    tree = cKDTree(region.points)
    hR = float(region.h)
    per: dict = {}
    off_all = []
    n_off = 0
    raw_min = math.inf
    h_t = 0.0
    for pid, T in training.items():
        if T.n == 0:
            per[pid] = dict(raw_min=None, certified_min=None, n_offending=0, n_samples=0)
            continue
        hT = T.local_h()
        hmax = float(hT.max())
        h_t = max(h_t, hmax)
        ub = threshold + hmax + hR
        # exact for every pair closer than ub (all that can decide the verdict)
        d, j = tree.query(T.points, k=1, distance_upper_bound=ub, workers=workers)
        hit = np.isfinite(d)
        low = np.full(T.n, np.inf)
        low[hit] = d[hit] - hT[hit] - hR  # rigorous per-sample lower bound
        if hit.any():
            mn, exact = float(d[hit].min()), True
        else:
            # the approximate min is an upper bound of the true min, so an exact
            # query capped just above it recovers the exact min cheaply
            da, _ = tree.query(T.points, k=1, eps=approx_eps, workers=workers)
            cap = float(da.min()) * (1.0 + 1e-9) + 1e-9
            de, _ = tree.query(T.points, k=1, distance_upper_bound=cap, workers=workers)
            fin = np.isfinite(de)
            mn, exact = (float(de[fin].min()), True) if fin.any() else (float(da.min()), False)
        # samples without a pair < ub: d_i - h_i - hR >= ub - h_i - hR >= threshold
        cert_non = threshold + hmax - float(hT[~hit].max()) if (~hit).any() else math.inf
        if not hit.any():
            cert_non = max(cert_non, (mn if exact else mn / (1.0 + approx_eps)) - hmax - hR)
        cert = min(float(low.min()), cert_non)
        bad = low < threshold
        raw_min = min(raw_min, mn)
        n_off += int(bad.sum())
        per[pid] = dict(raw_min=mn, raw_min_exact=exact, certified_min=cert, n_offending=int(bad.sum()),
                        n_samples=T.n, h_max=hmax, h_region=hR)
        if bad.any():
            ii = np.nonzero(bad)[0]
            o = np.argsort(d[ii])[:max_offending]
            for t in ii[o]:
                off_all.append(dict(patch=pid, dist=float(d[t]), certified=float(low[t]),
                                    train_xyz=T.points[t].round(3).tolist(),
                                    train_canvas_px=T.canvas[t].round(2).tolist(),
                                    region_xyz=region.points[j[t]].round(3).tolist(),
                                    region_canvas_px=region.canvas[j[t]].round(2).tolist()))
    off_all.sort(key=lambda r: r["dist"])
    cert = min((v["certified_min"] for v in per.values() if v.get("certified_min") is not None), default=math.inf)
    return Clearance(raw_min, cert, float(threshold), bool(cert >= threshold), hR, h_t, per,
                     off_all[:max_offending], n_off)


def retrace_expansion(training: Mapping[str, DenseSurface], others: Mapping[str, DenseSurface], *,
                      workers: int = 1, nd_tol: float = 2.0, radius: float = SP_RADIUS_VOX) -> dict:
    """For each training patch, the samples of every other surface that are
    same-sheet with it (normal distance < nd_tol within radius): the patch's
    papyrus as re-traced elsewhere. Returned as extra training surfaces
    '<pid>@<other>'."""
    out = {}
    for pid, T in training.items():
        if T.n == 0:
            continue
        tree = cKDTree(T.points)
        lo, hi = _bbox(T.points)
        for on, O in others.items():
            m = np.all((O.points >= lo - radius) & (O.points <= hi + radius), axis=1)
            if not m.any():
                continue
            Os = O.subset(m)
            nd = normal_distances(Os, T, radius=radius, workers=workers, tree_B=tree)
            sel = nd < nd_tol
            if sel.any():
                out[f"{pid}@{on}"] = Os.subset(sel, name=f"{pid}@{on}")
    return out


# ---------------------------------------------------------------------------
# training-patch registry and FL-09 certificate
# ---------------------------------------------------------------------------

REGISTRY_KEYS = ("checkpoint", "frame", "patches")
PATCH_KEYS = ("id", "segment", "mesh_dir", "rect_px", "label_source")


def load_registry(path: str | Path) -> tuple[dict, str]:
    """Load and validate a training-patch registry; returns (registry, sha256 of
    the file bytes)."""
    raw = Path(path).read_bytes()
    reg = json.loads(raw)
    for k in REGISTRY_KEYS:
        if k not in reg:
            raise ValueError(f"registry lacks '{k}'")
    for k in ("scroll", "volume_id", "voxel_size_mm"):
        if k not in reg["frame"]:
            raise ValueError(f"registry frame lacks '{k}'")
    ids = set()
    for p in reg["patches"]:
        for k in PATCH_KEYS:
            if k not in p:
                raise ValueError(f"patch lacks '{k}': {p}")
        if p["id"] in ids:
            raise ValueError(f"duplicate patch id {p['id']}")
        ids.add(p["id"])
        if p["rect_px"] is not None and len(p["rect_px"]) != 4:
            raise ValueError(f"rect_px must be [x0, y0, x1, y1] or null: {p}")
    return reg, hashlib.sha256(raw).hexdigest()


def _resolve(base: Path, d: str) -> Path:
    q = Path(d)
    return q if q.is_absolute() else base / q


def _check_mesh_hash(mesh_dir: Path, expected: Mapping | None) -> dict:
    got = mesh_hashes(mesh_dir)
    if expected:
        for n, h in expected.items():
            if got.get(n) != h:
                raise ValueError(f"mesh hash mismatch {mesh_dir}/{n}: {got.get(n)} != {h}")
    return got


def grow_rect(rect: Sequence[float], halo: float) -> list[float]:
    x0, y0, x1, y1 = (float(v) for v in rect)
    return [x0 - halo, y0 - halo, x1 + halo, y1 + halo]


def fl09_certificate(registry_path: str | Path, region: Mapping, *, min_vox: float = 128.0, halo_px: float = 64.0,
                     k: int = 5, workers: int = 1, retrace_meshes: Mapping[str, str] | None = None,
                     base_dir: str | Path | None = None, max_offending: int = 50,
                     slab_region_vox: float = 0.0, slab_train_vox: float = 0.0) -> dict:
    """SG item 8 / FL-09 certificate for a candidate rectangle R.

    region = {"segment", "mesh_dir", "rect_px": [x0, y0, x1, y1], "volume_id",
              optional "mesh_sha256"}.
    PRIMARY rule (SG 8 as written, halo in R's canvas plane as in
    DECL-READCAL-A2): every surface point of R grown by ``halo_px`` canvas
    pixels is >= ``min_vox`` 3-D from every training patch surface. Reported
    as well: the scalar reading (R itself >= min_vox + halo_px, px taken as
    vox), which the orchestrator may declare instead.
    ``retrace_meshes`` (segment -> mesh dir): every other organizer mesh of the
    scroll; same-sheet samples of a training patch found on them are added to
    the training set (all re-traces; changes distances by <= 2 vox).
    ``slab_region_vox`` / ``slab_train_vox``: half-depth of the rendered slabs
    (e.g. 15 for an -n 31 render); the surface threshold becomes min_vox + both,
    so the rendered VOXELS (not only the surfaces) are >= min_vox apart. Default
    0 = SG 8 as written (surface points).
    """
    reg, reg_sha = load_registry(registry_path)
    base = Path(base_dir) if base_dir is not None else Path(registry_path).parent
    if str(region.get("volume_id")) != str(reg["frame"]["volume_id"]):
        raise ValueError("region and registry are not in the same voxel frame")
    rdir = _resolve(base, region["mesh_dir"])
    r_hash = _check_mesh_hash(rdir, region.get("mesh_sha256"))
    rmesh = read_tifxyz(rdir)
    R_halo = dense_from_mesh(rmesh, k, rect_px=grow_rect(region["rect_px"], halo_px), name="R+halo")
    R_core = dense_from_mesh(rmesh, k, rect_px=region["rect_px"], name="R")
    if R_core.n == 0:
        raise ValueError("R has no valid mesh samples")
    meshes: dict[str, TifxyzMesh] = {}
    train: dict[str, DenseSurface] = {}
    patch_hashes = {}
    for p in reg["patches"]:
        mdir = _resolve(base, p["mesh_dir"])
        key = str(mdir)
        if key not in meshes:
            patch_hashes[p["segment"]] = _check_mesh_hash(mdir, p.get("mesh_sha256"))
            meshes[key] = read_tifxyz(mdir)
        train[p["id"]] = dense_from_mesh(meshes[key], k, rect_px=p["rect_px"], name=p["id"])
    retr_hashes = {}
    if retrace_meshes:
        others = {}
        for seg, d in retrace_meshes.items():
            dd = _resolve(base, d)
            retr_hashes[seg] = mesh_hashes(dd)
            others[seg] = dense_from_mesh(read_tifxyz(dd), k, name=seg)
        train.update(retrace_expansion(train, others, workers=workers))
    slab = float(slab_region_vox) + float(slab_train_vox)
    prim = clearance(R_halo, train, min_vox + slab, workers=workers, max_offending=max_offending)
    scal = clearance(R_core, train, min_vox + halo_px + slab, workers=workers, max_offending=max_offending)
    return {
        "provenance": PROVENANCE,
        "rule": "SG item 8 / FL-09: every pixel of R >= %g vox + %g px halo from every training patch, "
                "all windings and re-traces" % (min_vox, halo_px),
        "registry_sha256": reg_sha,
        "registry_checkpoint": reg["checkpoint"],
        "frame": reg["frame"],
        "region": {k2: v for k2, v in region.items() if k2 != "mesh_sha256"} | {"mesh_sha256": r_hash},
        "training_mesh_sha256": patch_hashes,
        "retrace_mesh_sha256": retr_hashes,
        "densify_k": k,
        "slab_vox": {"region": slab_region_vox, "train": slab_train_vox},
        "surface_threshold_vox": min_vox + slab,
        "n_samples": {"R": R_core.n, "R_halo": R_halo.n, "train": int(sum(t.n for t in train.values()))},
        "n_training_surfaces": len(train),
        "primary_halo_inplane": prim.as_dict(),
        "alt_scalar_min_plus_halo": scal.as_dict(),
        "passed": prim.passed,
        "passed_alt_scalar": scal.passed,
    }
