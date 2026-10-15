# Provenance: Project HERCULES | owner the owner | [id removed]
"""Flatten P4 window A (w010-027 canvas columns c8-c17, all rows) for the
Paris 4 Title Prize package. Geometry only: mesh coordinates and metadata;
no prediction, render or CT pixel is read and no image is produced.

    PYTHONPATH=src:tools/sib/flat1 /opt/hv/bin/python tools/sib/flat1/p4win.py

Rules (fixed before running):
* Mesh: organizer tifxyz 20260701183124-on-20260411134726-2.4um (voxel from
  the volume metadata.json). Canvas = grid x 20 px; tile side T = 8343 px
  (p4-tiles-a grid.json). A fine quad (i, j) belongs to the window iff
  floor(20 (j + 0.5) / T) is in [8, 17] (DECL-P4-2 tile rule, all rows).
  The largest 4-connected component of valid window quads is flattened.
* Coarse solve: the region is subsampled every K = 6 vertices (a coarse
  vertex is the fine vertex at (6a, 6b); a coarse quad is kept iff its four
  corners and all 36 fine quads inside it are valid and in the component).
  The coarse mesh is flattened with vc_flatten (official ABF++, defaults),
  SLIM and ARAP (flatpkg). Reason: 14.5 M fine quads exceed CPU memory/time
  for ABF++/SLIM; the coarse quad (0.29 mm) is still far below letter size.
* Fine UV: bilinear interpolation of the coarse UV inside each coarse quad
  (the same rule as ABF++'s own upsampleUVs). Fine quads outside kept coarse
  quads have no UV and COUNT AS FAILING.
* Orientation: each flattening is rotated (proper rotation, least squares,
  Kabsch) onto the fine grid coordinates (u = col x 20, v = row x 20), so the
  flattened image keeps the canvas orientation; reflections are never applied
  (a needed reflection would be reported).
* Metrics at FULL resolution over all window-component quads: FLAT-1 edge
  metric (all 4 edges within +-5 % after one global area factor; raw too),
  per-triangle area ratio (fraction within +-5 %, median, p5/p95 of
  |log|), angle error (median, p95, p99, max, degrees), flipped triangles.
* Deliverable: for the adopted method (vc_flatten, FLAT-1 rule) and for SLIM,
  a flattened tifxyz = xyz resampled on a regular 20-vox grid in the flat
  (u, v) plane (linear interpolation inside fine triangles), plus u.tif/v.tif
  (fine-grid UV) giving the canvas mapping: canvas px (y, x) -> fine grid
  (y/20 - R0, x/20 - C0) -> bilinear (u, v); flattened tifxyz node (i, j) =
  (u, v) = (U0 + 20 j, V0 + 20 i).
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
import tifffile
from scipy import ndimage

import flatlib as FL
import flatpkg as P
from hercules.geometry import tifxyz as T
from hercules.pipeline.window import voxel_size_from_metadata

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "logs/sib/flat1/p4win"
WORK = Path("/work/flat1/p4win")
SEG = "20260701183124-w010-027"
MESH_KEY = f"PHercParis4/segments/{SEG}/mesh/20260701183124-on-20260411134726-2.4um.tifxyz/"
VOL_META_KEY_PREFIX = "PHercParis4/volumes/"
T_PX = 8343
COLS = (8, 17)
K = 6
STEP = 20.0
CHUNK = 256


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fetch() -> tuple[Path, list, float, str]:
    import flat1_run as RUN

    c = RUN.s3()
    d = WORK / "mesh.tifxyz"
    d.mkdir(parents=True, exist_ok=True)
    dl = []
    for f in ("meta.json", "x.tif", "y.tif", "z.tif"):
        p = d / f
        if not p.exists():
            c.download_file(RUN.BUCKET, MESH_KEY + f, str(p))
        dl.append({"key": MESH_KEY + f, "size": p.stat().st_size, "sha256": sha(p)})
    r = c.list_objects_v2(Bucket=RUN.BUCKET, Prefix=VOL_META_KEY_PREFIX, Delimiter="/")
    z = [q["Prefix"] for q in r["CommonPrefixes"] if q["Prefix"].split("/")[-2].startswith("20260411134726")]
    mp = WORK / "vol_metadata.json"
    mp.write_bytes(c.get_object(Bucket=RUN.BUCKET, Key=z[0] + "metadata.json")["Body"].read())
    return d, dl, voxel_size_from_metadata(mp), sha(mp)


def window(points: np.ndarray) -> dict:
    H, W = points.shape[:2]
    qv = FL.quad_mask(points)
    tc = np.floor((np.arange(W - 1) + 0.5) * 20 / T_PX)
    inwin = (tc >= COLS[0]) & (tc <= COLS[1])
    j = np.nonzero(inwin)[0]
    C0, C1 = int(j[0]), int(j[-1]) + 1  # vertex columns [C0, C1]
    q = qv[:, C0:C1] & inwin[None, C0:C1]
    lab, n = ndimage.label(q)
    sizes = ndimage.sum(q, lab, np.arange(1, n + 1))
    keep = lab == 1 + int(np.argmax(sizes))
    return {"C0": C0, "C1": C1, "R0": 0, "R1": H - 1, "keep": keep, "n_components": int(n),
            "n_quads_valid_window": int(q.sum()), "n_quads_kept": int(keep.sum())}


def coarse(p: np.ndarray, keep: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    H, W = p.shape[:2]
    hc, wc = (H - 1) // K + 1, (W - 1) // K + 1
    pc = p[::K, ::K][:hc, :wc].copy()
    # coarse quad valid iff all K x K fine quads inside are kept
    kq = np.zeros((hc - 1, wc - 1), bool)
    S = np.zeros((keep.shape[0] + 1, keep.shape[1] + 1), np.int64)
    S[1:, 1:] = keep.cumsum(0).cumsum(1)
    a = np.arange(hc - 1) * K
    b = np.arange(wc - 1) * K
    A, B = np.meshgrid(a, b, indexing="ij")
    tot = S[A + K, B + K] - S[A, B + K] - S[A + K, B] + S[A, B]
    kq = tot == K * K
    lab, n = ndimage.label(kq)
    if n > 1:
        sizes = ndimage.sum(kq, lab, np.arange(1, n + 1))
        kq = lab == 1 + int(np.argmax(sizes))
    used = np.zeros((hc, wc), bool)
    used[:-1, :-1] |= kq
    used[1:, :-1] |= kq
    used[:-1, 1:] |= kq
    used[1:, 1:] |= kq
    pc[~used] = -1.0
    return pc, kq


def upsample(uvc: np.ndarray, kq: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    H, W = shape
    uv = np.full((H, W, 2), np.nan)
    ii = np.arange(H)
    jj = np.arange(W)
    a = np.minimum(ii // K, kq.shape[0] - 1)
    b = np.minimum(jj // K, kq.shape[1] - 1)
    fa = (ii - a * K) / K
    fb = (jj - b * K) / K
    for r0 in range(0, H, 512):
        rs = slice(r0, min(r0 + 512, H))
        A = a[rs][:, None]
        B = b[None, :]
        FA = fa[rs][:, None, None]
        FB = fb[None, :, None]
        u00 = uvc[A, B]
        u01 = uvc[A, B + 1]
        u10 = uvc[A + 1, B]
        u11 = uvc[A + 1, B + 1]
        val = (1 - FA) * (1 - FB) * u00 + (1 - FA) * FB * u01 + FA * (1 - FB) * u10 + FA * FB * u11
        ok = kq[A, B] & np.isfinite(val).all(-1)
        # a fine vertex on a coarse boundary may belong to a kept neighbour quad
        uv[rs] = np.where(ok[..., None], val, np.nan)
    # vertices on the last row/col of a kept coarse quad whose own (a, b) quad is not kept
    for da, db in ((-1, 0), (0, -1), (-1, -1)):
        miss = ~np.isfinite(uv).all(-1)
        if not miss.any():
            break
        I, J = np.nonzero(miss)
        on_r = (I % K == 0) if da else np.ones_like(I, bool)
        on_c = (J % K == 0) if db else np.ones_like(J, bool)
        A = I // K + da
        B = J // K + db
        sel = on_r & on_c & (A >= 0) & (B >= 0) & (A < kq.shape[0]) & (B < kq.shape[1])
        I, J, A, B = I[sel], J[sel], A[sel], B[sel]
        good = kq[A, B]
        I, J, A, B = I[good], J[good], A[good], B[good]
        fa2 = (I - A * K) / K
        fb2 = (J - B * K) / K
        val = ((1 - fa2) * (1 - fb2))[:, None] * uvc[A, B] + ((1 - fa2) * fb2)[:, None] * uvc[A, B + 1] + \
              (fa2 * (1 - fb2))[:, None] * uvc[A + 1, B] + (fa2 * fb2)[:, None] * uvc[A + 1, B + 1]
        uv[I, J] = val
    return uv


def kabsch_align(uv: np.ndarray) -> tuple[np.ndarray, dict]:
    H, W = uv.shape[:2]
    ok = np.isfinite(uv).all(-1)
    I, J = np.nonzero(ok)
    sel = np.arange(I.size)[:: max(1, I.size // 2_000_000)]
    X = uv[I[sel], J[sel]]
    Y = np.stack([J[sel] * STEP, I[sel] * STEP], 1).astype(np.float64)
    mx, my = X.mean(0), Y.mean(0)
    Hm = (X - mx).T @ (Y - my)
    U, S, Vt = np.linalg.svd(Hm)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, d]) @ U.T
    info = {"reflection_needed": bool(d < 0), "rotation_deg": math.degrees(math.atan2(R[1, 0], R[0, 0]))}
    if d < 0:  # never reflect: use the best proper rotation of the unreflected map instead
        R = Vt.T @ U.T
        R = R if np.linalg.det(R) > 0 else np.diag([1.0, -1.0]) @ R
    out = (uv - mx) @ R.T + my
    return out, info


def chunked_metrics(p: np.ndarray, uv: np.ndarray, keep: np.ndarray) -> dict:
    """Full-resolution statistics, row chunks (exact counts, histogram
    quantiles with 1e-4 bin resolution)."""
    H = p.shape[0]
    # pass 1: global area factor
    A3 = A2 = 0.0
    for r0 in range(0, H - 1, CHUNK):
        r1 = min(r0 + CHUNK, H - 1)
        pp, uu, kk = p[r0:r1 + 1], uv[r0:r1 + 1], keep[r0:r1]
        m = FL.grid_to_mesh(pp, kk)
        UV = np.full((m.V.shape[0], 2), np.nan)
        I, J = np.nonzero(m.index >= 0)
        UV[m.index[I, J]] = uu[I, J]
        ok = np.isfinite(UV[m.F]).all(axis=(1, 2))
        A3 += FL.tri_areas_3d(m.V, m.F)[ok].sum()
        A2 += np.abs(FL.signed_areas_2d(UV, m.F))[ok].sum()
    s = math.sqrt(A3 / A2)
    n_q = n_ok = n_ok_raw = n_ok1 = 0
    n_tri = n_flip = n_undef = n_area5 = 0
    ang_bins = np.linspace(0, 180, 1_800_001)
    ang_h = np.zeros(ang_bins.size - 1, np.int64)
    la_bins = np.linspace(0, 2, 200_001)
    la_h = np.zeros(la_bins.size - 1, np.int64)
    signs = [0, 0]
    for r0 in range(0, H - 1, CHUNK):
        r1 = min(r0 + CHUNK, H - 1)
        pp, uu, kk = p[r0:r1 + 1].astype(np.float64), uv[r0:r1 + 1], keep[r0:r1]
        n_q += int(kk.sum())
        n_ok += int((FL.quad_edge_ok(pp, uu, 0.05, s) & kk).sum())
        n_ok_raw += int((FL.quad_edge_ok(pp, uu, 0.05, 1.0) & kk).sum())
        n_ok1 += int((FL.quad_edge_ok(pp, uu, 0.01, s) & kk).sum())
        m = FL.grid_to_mesh(pp, kk)
        UV = np.full((m.V.shape[0], 2), np.nan)
        I, J = np.nonzero(m.index >= 0)
        UV[m.index[I, J]] = uu[I, J]
        ok = np.isfinite(UV[m.F]).all(axis=(1, 2))
        n_tri += m.F.shape[0]
        n_undef += int((~ok).sum())
        sa = FL.signed_areas_2d(UV, m.F)
        signs[0] += int((sa[ok] > 0).sum())
        signs[1] += int((sa[ok] < 0).sum())
        F = m.F[ok]
        UVs = UV * s
        a3 = FL._tri_angles(m.V[F])
        a2 = FL._tri_angles(np.concatenate([UVs[F], np.zeros((F.shape[0], 3, 1))], 2))
        ang_h += np.histogram(np.degrees(np.abs(a2 - a3)).ravel(), ang_bins)[0]
        ar = np.abs(FL.signed_areas_2d(UVs, F)) / FL.tri_areas_3d(m.V, F)
        la = np.abs(np.log(ar))
        n_area5 += int((np.abs(ar - 1) <= 0.05).sum())
        la_h += np.histogram(np.minimum(la, 2 - 1e-9), la_bins)[0]
    n_flip = min(signs)  # triangles against the majority orientation

    def q(h, bins, f):
        c = np.cumsum(h)
        return float(bins[np.searchsorted(c, f * c[-1]) + 1])

    return {"n_quads": n_q, "area_scale_factor": s,
            "pct_quads_within_5pct": 100.0 * n_ok / n_q, "pct_quads_within_5pct_raw": 100.0 * n_ok_raw / n_q,
            "pct_quads_within_1pct": 100.0 * n_ok1 / n_q,
            "n_triangles": n_tri, "n_triangles_uv_undefined": n_undef, "flipped_triangles": int(n_flip),
            "area_pct_tri_within_5pct": 100.0 * n_area5 / max(n_tri - n_undef, 1),
            "area_abs_log_median": q(la_h, la_bins, 0.5), "area_abs_log_p95": q(la_h, la_bins, 0.95),
            "angle_err_deg_median": q(ang_h, ang_bins, 0.5), "angle_err_deg_p95": q(ang_h, ang_bins, 0.95),
            "angle_err_deg_p99": q(ang_h, ang_bins, 0.99),
            "angle_err_deg_max": float(ang_bins[np.nonzero(ang_h)[0][-1] + 1]) if ang_h.any() else math.nan}


def rasterize(p: np.ndarray, uv: np.ndarray, keep: np.ndarray) -> tuple[np.ndarray, dict]:
    """Flattened tifxyz: xyz on a regular STEP grid in (u, v), linear inside
    fine triangles. Also returns source fine-grid (row, col) per node."""
    ok = np.isfinite(uv).all(-1)
    umin, vmin = np.nanmin(uv[..., 0]), np.nanmin(uv[..., 1])
    U0 = math.floor(umin / STEP) * STEP
    V0 = math.floor(vmin / STEP) * STEP
    Wn = int(math.ceil((np.nanmax(uv[..., 0]) - U0) / STEP)) + 1
    Hn = int(math.ceil((np.nanmax(uv[..., 1]) - V0) / STEP)) + 1
    out = np.full((Hn, Wn, 3), -1.0, np.float32)
    src = np.full((Hn, Wn, 2), -1.0, np.float32)
    n_big = 0
    H = p.shape[0]
    for r0 in range(0, H - 1, CHUNK):
        r1 = min(r0 + CHUNK, H - 1)
        kk = keep[r0:r1]
        qi, qj = np.nonzero(kk)
        qi = qi + r0
        for tri in ((( 1, 0), (0, 0), (0, 1)), ((1, 0), (0, 1), (1, 1))):
            vi = [qi + t[0] for t in tri]
            vj = [qj + t[1] for t in tri]
            A = [uv[a, b] for a, b in zip(vi, vj)]
            good = np.isfinite(np.stack(A, 1)).all(axis=(1, 2))
            if not good.any():
                continue
            A = [x[good] for x in A]
            Pv = [p[a[good], b[good]].astype(np.float64) for a, b in zip(vi, vj)]
            S = [np.stack([a[good], b[good]], 1).astype(np.float64) for a, b in zip(vi, vj)]
            gu = [(x[:, 0] - U0) / STEP for x in A]
            gv = [(x[:, 1] - V0) / STEP for x in A]
            j0 = np.floor(np.minimum.reduce(gu)).astype(np.int64)
            i0 = np.floor(np.minimum.reduce(gv)).astype(np.int64)
            ext = np.maximum(np.ceil(np.maximum.reduce(gu)) - j0, np.ceil(np.maximum.reduce(gv)) - i0)
            n_big += int((ext > 3).sum())
            d = (gu[1] - gu[0]) * (gv[2] - gv[0]) - (gu[2] - gu[0]) * (gv[1] - gv[0])
            for di in range(4):
                for dj in range(4):
                    ni, nj = i0 + di, j0 + dj
                    x, y = nj.astype(np.float64), ni.astype(np.float64)
                    with np.errstate(invalid="ignore", divide="ignore"):
                        l1 = ((x - gu[0]) * (gv[2] - gv[0]) - (gu[2] - gu[0]) * (y - gv[0])) / d
                        l2 = ((gu[1] - gu[0]) * (y - gv[0]) - (x - gu[0]) * (gv[1] - gv[0])) / d
                    l0 = 1 - l1 - l2
                    e = -1e-9
                    ins = (l0 >= e) & (l1 >= e) & (l2 >= e) & (ni >= 0) & (nj >= 0) & (ni < Hn) & (nj < Wn) & (d != 0)
                    if not ins.any():
                        continue
                    w = [l0[ins, None], l1[ins, None], l2[ins, None]]
                    out[ni[ins], nj[ins]] = (w[0] * Pv[0][ins] + w[1] * Pv[1][ins] + w[2] * Pv[2][ins]).astype(np.float32)
                    src[ni[ins], nj[ins]] = (w[0] * S[0][ins] + w[1] * S[1][ins] + w[2] * S[2][ins]).astype(np.float32)
    return out, {"U0": U0, "V0": V0, "grid_shape": [Hn, Wn], "triangles_exceeding_3_nodes": n_big, "src": src}


def grid_edge_metric(q: np.ndarray) -> dict:
    v = FL.valid_mask(q)
    qv = v[:-1, :-1] & v[1:, :-1] & v[:-1, 1:] & v[1:, 1:]
    Lh = np.linalg.norm(q[:, 1:].astype(np.float64) - q[:, :-1], axis=-1)
    Lv = np.linalg.norm(q[1:].astype(np.float64) - q[:-1], axis=-1)
    okh = np.abs(Lh / STEP - 1) <= 0.05
    okv = np.abs(Lv / STEP - 1) <= 0.05
    ok = okh[:-1] & okh[1:] & okv[:, :-1] & okv[:, 1:] & qv
    return {"n_quads": int(qv.sum()), "pct_quads_within_5pct_of_step": 100.0 * ok.sum() / max(qv.sum(), 1)}


def write_f32(path: Path, a: np.ndarray) -> str:
    tifffile.imwrite(str(path), np.ascontiguousarray(a, dtype="<f4"), photometric="minisblack",
                     compression="zlib", metadata=None, tile=(1024, 1024), software=False)
    return sha(path)


def main() -> None:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    d, dl, vox, vsha = fetch()
    mesh = T.read_tifxyz(d)
    assert abs(mesh.step_vox[0] - STEP) < 1e-3
    w = window(mesh.points)
    p = np.ascontiguousarray(mesh.points[:, w["C0"]:w["C1"] + 1])
    del mesh
    keep = w.pop("keep")
    rec = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
           "viewing": "geometry only; no prediction, render or CT pixel read; no image produced",
           "segment": SEG, "mesh": dl, "voxel_um": vox, "volume_metadata_sha256": vsha, "T_px": T_PX,
           "tile_cols": list(COLS), "window": w, "region_grid_shape": list(p.shape[:2]), "K": K}
    prev = json.loads((OUT / "metrics.json").read_text()) if (OUT / "metrics.json").exists() else {}
    if prev.get("window") == w and "official" in prev:  # resume after a container restart
        rec["official"] = prev["official"]
    else:
        # official flattening of the region (grid, nominal step) at full resolution
        uv_off = np.stack(np.meshgrid(np.arange(p.shape[1]) * STEP, np.arange(p.shape[0]) * STEP), -1).astype(np.float64)
        uv_off[~FL.valid_mask(p)] = np.nan
        rec["official"] = chunked_metrics(p, uv_off, keep)
        del uv_off
    print("official", rec["official"], flush=True)
    pc, kq = coarse(p, keep)
    rec["coarse"] = {"shape": list(pc.shape[:2]), "n_quads": int(kq.sum()),
                     "fine_quads_covered": int(kq.sum()) * K * K}
    rec["methods"] = {k: v for k, v in prev.get("methods", {}).items()
                      if prev.get("window") == w and (WORK / f"uv_{k}.npy").exists()}
    (OUT / "metrics.json").write_text(json.dumps(rec, indent=1, default=float) + "\n")
    for meth in ("vc_flatten", "slim", "arap"):
        if meth in rec["methods"]:
            continue
        t1 = time.time()
        r = P.flatten(pc, meth, workdir=WORK / f"coarse_{meth}", voxel_um=vox, step=STEP * K)
        cm = P.metrics(pc, r.uv, kq)
        uv = upsample(r.uv, kq, p.shape[:2])
        uv, al = kabsch_align(uv)
        fm = chunked_metrics(p, uv, keep)
        mrec = {"coarse_metrics": {k: cm[k] for k in ("pct_quads_within_5pct", "flipped_triangles", "n_triangles_uv_undefined",
                                                       "area_scale_factor")},
                "collapse": P.collapse_flags(cm, r.info), "abf_rescale_factor": r.info.get("abf_rescale_factor"),
                "flatten_seconds": r.seconds, "align": al, "full_resolution": fm}
        np.save(WORK / f"uv_{meth}.npy", uv.astype(np.float32))
        rec["methods"][meth] = mrec
        print(meth, round(time.time() - t1), json.dumps(mrec, default=float)[:600], flush=True)
        (OUT / "metrics.json").write_text(json.dumps(rec, indent=1, default=float) + "\n")
    # deliverables: vc_flatten (FLAT-1 adopted) and SLIM
    rec["deliverables"] = {}
    for meth in ("vc_flatten", "slim"):
        uv = np.load(WORK / f"uv_{meth}.npy").astype(np.float64)
        flat, info = rasterize(p, uv, keep)
        src = info.pop("src")
        dd = OUT / meth
        tdir = dd / "flattened.tifxyz"
        tdir.mkdir(parents=True, exist_ok=True)
        files = {}
        for i, n in enumerate(("x", "y", "z")):
            files[f"flattened.tifxyz/{n}.tif"] = write_f32(tdir / f"{n}.tif", flat[..., i])
        valid = FL.valid_mask(flat)
        meta = {"bbox": T.bbox(flat), "format": "tifxyz", "scale": [1 / STEP, 1 / STEP], "type": "seg",
                "uuid": f"p4winA_{meth}", "hercules_source": SEG, "hercules_window_tile_cols": list(COLS),
                "hercules_region_vertex_cols": [w["C0"], w["C1"]], "hercules_uv_origin_vox": [info["U0"], info["V0"]],
                "hercules_flattening": meth, "hercules_voxel_um": vox}
        (tdir / "meta.json").write_text(json.dumps(meta, indent=4, sort_keys=True) + "\n")
        files["flattened.tifxyz/meta.json"] = sha(tdir / "meta.json")
        files["uv_u.tif"] = write_f32(dd / "uv_u.tif", np.where(np.isfinite(uv[..., 0]), uv[..., 0], -1))
        files["uv_v.tif"] = write_f32(dd / "uv_v.tif", np.where(np.isfinite(uv[..., 1]), uv[..., 1], -1))
        files["src_row.tif"] = write_f32(dd / "src_row.tif", src[..., 0])
        files["src_col.tif"] = write_f32(dd / "src_col.tif", src[..., 1])
        chk = T.read_tifxyz(tdir)  # official-loader-compatible read-back
        rec["deliverables"][meth] = {"dir": str(dd.relative_to(REPO)), "files_sha256": files, "raster": info,
                                     "n_valid_nodes": int(valid.sum()), "readback_equal": bool(np.array_equal(
                                         T.canonicalize(chk.points), T.canonicalize(flat))),
                                     "area_cm2": T.area_cm2(flat, vox),
                                     "flattened_grid_metric": grid_edge_metric(flat)}
        print("deliverable", meth, json.dumps(rec["deliverables"][meth]["flattened_grid_metric"]), flush=True)
        (OUT / "metrics.json").write_text(json.dumps(rec, indent=1, default=float) + "\n")
    rec["mapping"] = {
        "canvas_to_region_grid": "canvas px (y, x) of the w010-027 prediction canvas -> region fine grid (row, col) = (y / 20, x / 20 - C0), C0 = window.C0",
        "region_grid_to_uv": "(u, v) = bilinear interpolation of <method>/uv_u.tif, uv_v.tif at (row, col); -1 = undefined",
        "uv_to_flattened_node": "flattened.tifxyz node (i, j) <-> (u, v) = (U0 + 20 j, V0 + 20 i), U0/V0 = meta.json hercules_uv_origin_vox",
        "flattened_node_to_region_grid": "<method>/src_row.tif, src_col.tif (fractional region fine-grid row/col; -1 = empty node)",
        "canvas_tile": "tile (r, c) = canvas rows [r T, (r+1) T), cols [c T, (c+1) T), T = 8343"}
    rec["seconds_total"] = time.time() - t0
    (OUT / "metrics.json").write_text(json.dumps(rec, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
