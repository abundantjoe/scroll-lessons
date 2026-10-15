# Provenance: Project HERCULES | owner the owner | [id removed]
"""Empirical null tile builder (plan section 8.2, DECL-EMPNULL).

For a candidate region R (a window on one segment's render canvas) the null set holds
>= 40 tiles matched to R (same tile size, volume, display D*, prompt P*, reader mix and
batches; the harness enforces the reading side):

  1. R's non-text-order map (the other inference direction over R's own stack);
  2. R's NULL-arm map (text order, NULL-trained arm);
  3. R re-rendered half a local sheet pitch off-sheet, on both sides of the sheet. The
     pitch is measured by code: for every R mesh vertex, the distance along the local
     unit normal from the centre of the vertex's own m7 sheet run to the centre of the
     nearest neighbouring m7 sheet run (either side); pitch = median over vertices;
  4. >= 20 same-volume, same-radius-band tiles in the non-text order, >= a 3-D
     separation from R and from every exclusion cloud (e.g. the PHerc0841 J windows,
     144 vox), mutually separated, chosen by a seeded permutation.

The builder writes specs (and the off-sheet tifxyz meshes); rendering, inference and
display use the ordinary pipeline. Nothing here reads an image.
"""

from __future__ import annotations

import math
import uuid
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.spatial import cKDTree

from hercules.geometry.level_mesh import CentreLike
from hercules.geometry.tifxyz import TifxyzMesh, sample_grid, valid_mask, vertex_normals, write_tifxyz
from hercules.pipeline import canvas as C

from . import TRIBUNAL_VERSION

N_TOTAL_MIN = 40
N_BAND_MIN = 20
BAND_FRAC = 0.10          # same-radius band: |r - r_R| <= 10 % of r_R
SEP_FROM_R_VOX = 192.0    # 128 vox + 64 px halo (FL-09 distances) from R
EXCLUSION_VOX = 144.0     # e.g. PHerc0841 J windows
MUTUAL_SEP_VOX = 64.0     # between selected band tiles
PITCH_MAX_DIST = 60.0
PITCH_DT = 0.25
PITCH_OWN_MAX = 4.0       # own sheet run must touch |t| <= 4 vox, else the vertex is skipped
PITCH_MIN_POINTS = 50


# ----------------------------------------------------------------------------- m7 access and centre curve

class ChunkPointSampler:
    """Nearest-voxel values of a large chunked array (zarr) at many integer points, fetching each
    needed chunk exactly once per call (no whole-bbox read). Points outside the array read 0."""

    def __init__(self, arr):
        self.arr = arr
        self.shape = tuple(arr.shape)
        self.chunks = tuple(arr.chunks)

    def sample(self, zyx: np.ndarray) -> np.ndarray:
        q = np.asarray(zyx, dtype=np.int64).reshape(-1, 3)
        out = np.zeros(len(q), dtype=np.asarray(self.arr[0:1, 0:1, 0:1]).dtype)
        inside = np.all((q >= 0) & (q < np.asarray(self.shape)), axis=1)
        idx = np.flatnonzero(inside)
        if idx.size == 0:
            return out
        ch = np.asarray(self.chunks)
        keys = q[idx] // ch
        order = np.lexsort((keys[:, 2], keys[:, 1], keys[:, 0]))
        idx, keys = idx[order], keys[order]
        brk = np.flatnonzero(np.any(np.diff(keys, axis=0) != 0, axis=1)) + 1
        for grp in np.split(np.arange(len(idx)), brk):
            k = keys[grp[0]]
            lo = k * ch
            hi = np.minimum(lo + ch, self.shape)
            blk = np.asarray(self.arr[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]])
            rel = q[idx[grp]] - lo
            out[idx[grp]] = blk[rel[:, 0], rel[:, 1], rel[:, 2]]
        return out


def centre_from_normals(meshes, z_band: float = 200.0, stride: int = 4, min_xy_norm: float = 0.5,
                        min_points: int = 200) -> tuple:
    """Geometry-only centre curve: per z-band, the least-squares point closest to every xy
    vertex-normal line of all meshes (lines p + t n_xy), smoothed by a 3-band running median.
    Returns (CentreCurve, per-band diagnostics)."""
    from hercules.geometry.level_mesh import CentreCurve

    P, N = [], []
    for pts in meshes:
        p = np.asarray(pts, dtype=np.float64)
        n = vertex_normals(p)
        p, n = p[::stride, ::stride], n[::stride, ::stride]
        ok = valid_mask(p) & np.isfinite(n).all(-1)
        nxy = n[ok][:, :2]
        L = np.linalg.norm(nxy, axis=1)
        keep = L >= min_xy_norm
        P.append(p[ok][keep])
        N.append(nxy[keep] / L[keep, None])
    P, N = np.concatenate(P), np.concatenate(N)
    zb = np.floor(P[:, 2] / z_band).astype(np.int64)
    zs, xs, ys, diag = [], [], [], []
    for b in np.unique(zb):
        m = zb == b
        if m.sum() < min_points:
            continue
        n, p = N[m], P[m][:, :2]
        proj = np.eye(2)[None] - n[:, :, None] * n[:, None, :]
        A = proj.sum(0)
        bb = np.einsum("nij,nj->i", proj, p)
        if np.linalg.cond(A) > 1e6:
            continue
        c = np.linalg.solve(A, bb)
        res = np.sqrt(np.einsum("ni,nij,nj->n", c - p, proj, c - p))
        zs.append((b + 0.5) * z_band)
        xs.append(c[0])
        ys.append(c[1])
        diag.append({"z": (b + 0.5) * z_band, "n": int(m.sum()), "cx": float(c[0]), "cy": float(c[1]),
                     "median_line_dist_vox": float(np.median(res))})
    if not zs:
        raise ValueError("no z-band has enough vertices with an xy normal component")
    xs, ys = np.asarray(xs), np.asarray(ys)
    if len(xs) >= 3:
        xm = np.array([np.median(xs[max(0, i - 1):i + 2]) for i in range(len(xs))])
        ym = np.array([np.median(ys[max(0, i - 1):i + 2]) for i in range(len(ys))])
    else:
        xm, ym = xs, ys
    return CentreCurve(z=np.asarray(zs), x=xm, y=ym), diag


# ----------------------------------------------------------------------------- pitch

def _runs(b: np.ndarray) -> list[tuple[int, int]]:
    """[start, end] index pairs (inclusive) of True runs."""
    d = np.diff(np.concatenate([[0], b.astype(np.int8), [0]]))
    s = np.flatnonzero(d == 1)
    e = np.flatnonzero(d == -1) - 1
    return list(zip(s.tolist(), e.tolist()))


def local_pitch(points: np.ndarray, m7, *, m7_scale: float = 1.0, threshold: float = 0.0,
                max_dist: float = PITCH_MAX_DIST, dt: float = PITCH_DT, own_max: float = PITCH_OWN_MAX,
                stride: int = 1, min_points: int = PITCH_MIN_POINTS) -> dict:
    """Median centre-to-centre distance from each vertex's own m7 sheet to the nearest
    neighbouring m7 sheet along the local normal (vox). ``m7`` is indexed [z, y, x] at
    ``m7_scale`` volume voxels per m7 voxel; positive = value > threshold."""
    p = np.asarray(points, dtype=np.float64)[::stride, ::stride]
    nrm = vertex_normals(np.asarray(points, dtype=np.float64))[::stride, ::stride]
    ok = valid_mask(p) & np.isfinite(nrm).all(-1)
    P, N = p[ok], nrm[ok]
    t = np.arange(-max_dist, max_dist + 1e-9, dt)
    i0 = int(np.argmin(np.abs(t)))
    Z, Y, X = m7.shape
    lo = np.floor((P.min(0) - max_dist - 1) / float(m7_scale)).astype(np.int64)
    hi = np.ceil((P.max(0) + max_dist + 1) / float(m7_scale)).astype(np.int64) + 1
    lo_c = np.maximum(lo, 0)
    hi_c = np.minimum(hi, [X, Y, Z])
    pos_b = np.zeros((len(P), len(t)), dtype=bool)
    big = int(np.prod(np.maximum(hi_c - lo_c, 0))) > 64 * 1024 ** 2 and hasattr(m7, "chunks")
    if big:  # never materialise a large bbox: fetch only the chunks the normal lines touch
        sampler = ChunkPointSampler(m7)
        for c0 in range(0, len(P), 512):
            pos = P[c0:c0 + 512, None, :] + t[None, :, None] * N[c0:c0 + 512, None, :]
            q = np.rint(pos / float(m7_scale)).astype(np.int64).reshape(-1, 3)[:, ::-1]  # xyz -> zyx
            pos_b[c0:c0 + 512] = (sampler.sample(q) > threshold).reshape(-1, len(t))
    else:
        block = np.asarray(m7[lo_c[2]:hi_c[2], lo_c[1]:hi_c[1], lo_c[0]:hi_c[0]])
        for c0 in range(0, len(P), 2048):
            pos = P[c0:c0 + 2048, None, :] + t[None, :, None] * N[c0:c0 + 2048, None, :]   # volume vox
            q = np.rint(pos / float(m7_scale)).astype(np.int64)
            inside = np.all((q >= lo_c) & (q < hi_c), axis=-1)
            qq = np.where(inside[..., None], q - lo_c, 0)
            vals = np.where(inside, block[qq[..., 2], qq[..., 1], qq[..., 0]], 0)
            pos_b[c0:c0 + 2048] = vals > threshold
    nearest = np.full(len(P), np.nan)
    own_found = 0
    for k in range(len(P)):
        runs = _runs(pos_b[k])
        own = [r for r in runs if t[r[0]] <= own_max and t[r[1]] >= -own_max]
        if not own:
            continue
        own_found += 1
        a, b = min(own, key=lambda r: abs(0.5 * (t[r[0]] + t[r[1]])))
        c0 = 0.5 * (t[a] + t[b])
        d = []
        after = [r for r in runs if r[0] > b and r[1] < len(t) - 1]        # truncated runs excluded
        before = [r for r in runs if r[1] < a and r[0] > 0]
        if after:
            r = after[0]
            d.append(0.5 * (t[r[0]] + t[r[1]]) - c0)
        if before:
            r = before[-1]
            d.append(c0 - 0.5 * (t[r[0]] + t[r[1]]))
        if d:
            nearest[k] = min(d)
    fin = nearest[np.isfinite(nearest)]
    res = {"n_vertices": int(len(P)), "own_sheet_confirmed": own_found, "n_used": int(fin.size),
           "m7_scale": m7_scale, "dt": dt, "max_dist": max_dist, "own_max": own_max, "i0": i0}
    if fin.size < min_points:
        res.update(status="INSUFFICIENT", pitch_vox=math.nan)
        return res
    res.update(status="OK", pitch_vox=float(np.median(fin)), p10=float(np.percentile(fin, 10)),
               p90=float(np.percentile(fin, 90)), mean=float(fin.mean()))
    return res


def offsheet_meshes(points: np.ndarray, scale, pitch_vox: float, out_dir: str | Path, uid: str, voxel_um: float,
                    centre: CentreLike | None = None) -> list[dict]:
    """Write R's mesh displaced by +-pitch/2 along the unit normal normalize(du x dv).
    The grid (hence the canvas and R's window coordinates) is unchanged. With ``centre``
    each side is labelled outward/inward."""
    if not (pitch_vox > 0 and math.isfinite(pitch_vox)):
        raise ValueError("pitch must be a positive finite number")
    p = np.asarray(points, dtype=np.float64)
    n = vertex_normals(p)
    ok = valid_mask(p) & np.isfinite(n).all(-1)
    out = []
    for sign in (+1, -1):
        q = np.where(ok[..., None], p + sign * 0.5 * pitch_vox * np.where(ok[..., None], n, 0.0), -1.0)
        side = None
        if centre is not None:
            cx, cy = centre(p[..., 2])
            rv = np.stack([p[..., 0] - cx, p[..., 1] - cy], -1)
            dot = np.nanmedian(np.einsum("...i,...i->...", rv[ok], n[ok][..., :2]))
            side = "outward" if dot * sign > 0 else "inward"
        name = f"{uid}_off{'p' if sign > 0 else 'm'}"
        d = write_tifxyz(Path(out_dir) / name, TifxyzMesh(points=q.astype(np.float32), scale=tuple(scale), uuid=name,
                                                          meta={}), overwrite=True, voxel_size_um=voxel_um)
        out.append({"sign": sign, "side": side, "offset_vox": 0.5 * pitch_vox, "mesh_path": str(d), "uuid": name})
    return out


# ----------------------------------------------------------------------------- band tiles

def tile_cloud(points: np.ndarray, scale, window: Mapping[str, int], sample_px: int = 10) -> tuple[np.ndarray, float]:
    """3-D points of a canvas window (sampled every ``sample_px``) and its valid fraction."""
    cv = C.canvas_for(np.asarray(points), scale)
    rows = np.arange(window["y0"], window["y0"] + window["h"], sample_px, dtype=np.float64)
    cols = np.arange(window["x0"], window["x0"] + window["w"], sample_px, dtype=np.float64)
    v, _ = cv.pixel_to_grid(rows, 0.0)
    _, u = cv.pixel_to_grid(0.0, cols)
    V, U = np.meshgrid(v, u, indexing="ij")
    g = sample_grid(points, V, U)
    ok = valid_mask(g)
    return g[ok], float(ok.mean()) if ok.size else 0.0


def grid_tiles(segment_id: str, volume_id: str, points: np.ndarray, scale, tile_hw: tuple[int, int],
               stride_px: int | None = None, min_valid: float = 0.9, sample_px: int = 10) -> list[dict]:
    """Candidate tiles of R's size over one segment's canvas."""
    cv = C.canvas_for(np.asarray(points), scale)
    Hc, Wc = cv.shape
    th, tw = tile_hw
    sh = stride_px or th
    sw = stride_px or tw
    out = []
    for y0 in range(0, Hc - th + 1, sh):
        for x0 in range(0, Wc - tw + 1, sw):
            win = {"y0": y0, "x0": x0, "h": th, "w": tw}
            cl, vf = tile_cloud(points, scale, win, sample_px)
            if vf >= min_valid and len(cl):
                out.append({"segment_id": segment_id, "volume_id": volume_id, "window": win, "cloud": cl,
                            "valid_frac": vf})
    return out


def radius_of(cloud: np.ndarray, centre: CentreLike) -> float:
    cx, cy = centre(cloud[:, 2])
    return float(np.median(np.hypot(cloud[:, 0] - cx, cloud[:, 1] - cy)))


def select_band_tiles(R_cloud: np.ndarray, volume_id: str, candidates: Sequence[Mapping[str, Any]],
                      centre: CentreLike, n_needed: int, *, band_frac: float = BAND_FRAC,
                      sep_from_R: float = SEP_FROM_R_VOX, exclusions: Mapping[str, np.ndarray] | None = None,
                      exclusion_vox: float = EXCLUSION_VOX, mutual_sep: float = MUTUAL_SEP_VOX,
                      seed: int = 0) -> dict:
    """Same-volume, same-radius-band tiles, far from R and every exclusion cloud, mutually
    separated; seeded permutation then greedy acceptance."""
    rR = radius_of(R_cloud, centre)
    band = band_frac * rR
    tR = cKDTree(R_cloud)
    ex_trees = {k: cKDTree(np.asarray(v, dtype=np.float64)) for k, v in (exclusions or {}).items() if len(v)}
    reasons: dict[str, int] = {"other_volume": 0, "out_of_band": 0, "near_R": 0, "near_exclusion": 0}
    eligible = []
    for c in candidates:
        if c["volume_id"] != volume_id:
            reasons["other_volume"] += 1
            continue
        r = radius_of(c["cloud"], centre)
        if abs(r - rR) > band:
            reasons["out_of_band"] += 1
            continue
        if tR.query(c["cloud"], k=1)[0].min() < sep_from_R:
            reasons["near_R"] += 1
            continue
        if any(t.query(c["cloud"], k=1)[0].min() < exclusion_vox for t in ex_trees.values()):
            reasons["near_exclusion"] += 1
            continue
        eligible.append((c, r))
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(eligible))
    chosen, trees = [], []
    for i in order:
        c, r = eligible[int(i)]
        if any(t.query(c["cloud"], k=1)[0].min() < mutual_sep for t in trees):
            continue
        chosen.append({"segment_id": c["segment_id"], "window": dict(c["window"]), "radius_vox": r,
                       "valid_frac": c["valid_frac"]})
        trees.append(cKDTree(c["cloud"]))
        if len(chosen) >= n_needed:
            break
    return {"radius_R_vox": rR, "band_vox": band, "n_candidates": len(candidates), "n_eligible": len(eligible),
            "rejected": reasons, "chosen": chosen, "n_chosen": len(chosen), "n_needed": n_needed, "seed": seed}


# ----------------------------------------------------------------------------- assembly

def build_null_set(R: Mapping[str, Any], *, R_points: np.ndarray, scale, voxel_um: float, m7, centre: CentreLike,
                   band_candidates: Sequence[Mapping[str, Any]], out_dir: str | Path, m7_scale: float = 1.0,
                   exclusions: Mapping[str, np.ndarray] | None = None, n_total: int = N_TOTAL_MIN,
                   n_band_min: int = N_BAND_MIN, seed: int = 0, band_frac: float = BAND_FRAC,
                   pitch_stride: int = 1) -> dict:
    """R: {candidate_id, volume_id, segment_id, window {y0, x0, h, w}, text_direction
    ("forward"/"reverse")}. Returns the null-set spec; status OK only with >= n_total
    tiles of which >= n_band_min are band tiles."""
    if R["text_direction"] not in ("forward", "reverse"):
        raise ValueError("text_direction must be forward or reverse")
    nontext_dir = "reverse" if R["text_direction"] == "forward" else "forward"
    win = dict(R["window"])
    match = {"tile_hw": [win["h"], win["w"]], "voxel_um": float(voxel_um), "volume_id": R["volume_id"],
             "reading": "same D*, P*, reader mix and batches as R"}
    tiles: list[dict] = []

    def add(kind, **kw):
        tiles.append({"null_id": str(uuid.uuid4()), "kind": kind, "match": match, **kw})

    add("R_nontext_order", segment_id=R["segment_id"], window=win, direction=nontext_dir, order="nontext", arm="base")
    add("R_null_arm", segment_id=R["segment_id"], window=win, direction=R["text_direction"], order="text", arm="NULL")
    pitch = local_pitch(R_points, m7, m7_scale=m7_scale, stride=pitch_stride)
    R_cloud, _ = tile_cloud(R_points, scale, win)
    if pitch["status"] == "OK":
        for m in offsheet_meshes(R_points, scale, pitch["pitch_vox"], out_dir, f"{R['candidate_id']}", voxel_um,
                                 centre):
            add("R_offsheet_half_pitch", segment_id=R["segment_id"], window=win, direction=R["text_direction"],
                order="text", arm="base", **m)
    n_fixed = len(tiles)
    n_band_needed = max(n_band_min, n_total - n_fixed)
    band = select_band_tiles(R_cloud, R["volume_id"], band_candidates, centre, n_band_needed,
                             band_frac=band_frac, exclusions=exclusions, seed=seed)
    for c in band["chosen"]:
        add("band_nontext_order", segment_id=c["segment_id"], window=c["window"], direction=nontext_dir,
            order="nontext", arm="base", radius_vox=c["radius_vox"])
    n_band = len(band["chosen"])
    status = "OK" if (len(tiles) >= n_total and n_band >= n_band_min and pitch["status"] == "OK") else "INSUFFICIENT"
    return {"tribunal_version": TRIBUNAL_VERSION, "candidate_id": R["candidate_id"], "status": status,
            "n_tiles": len(tiles), "n_band": n_band, "n_total_min": n_total, "n_band_min": n_band_min,
            "pitch": pitch, "band": {k: v for k, v in band.items() if k != "chosen"}, "tiles": tiles}
