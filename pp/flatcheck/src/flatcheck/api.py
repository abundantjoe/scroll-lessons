"""flatcheck API: flatten a tifxyz grid, score it, detect collapse, and
write/verify flat packages.

Public API (all geometry only):

* ``flatten(points, method, workdir=None, voxel_um=None)`` -> FlatResult
  method "vc_flatten": official ABF++ (ScrollPrize/villa ``vc::abfFlatten``,
  vc_flatten defaults) through abf/abf_uv_dump.cpp (optional, see
  flatcheck.abf); "slim": libigl SLIM, symmetric Dirichlet, free
  boundary, start = the grid (u, v) x step (flip-free), stop at relative
  energy decrease <= 1e-7 per 5 iterations (max 200); "arap": libigl ARAP
  (elements, 200 iterations, one pinned vertex).
* ``metrics(points, uv, quads=None)``: the FLAT-1 metric (% quads with all
  four edges within +-5 % after one global area-matching factor, plus raw),
  flips, area/angle distortion (flatlib.evaluate).
* ``collapse_flags(result)``: collapse detector: flipped triangles > 0, or
  ABF rescale factor outside [1/1.5, 1.5], or any undefined UV.
* ``write_package(dir, points, uv, record)`` / ``read_package(dir)``: a
  flattened package = the input tifxyz (points), ``u.tif``/``v.tif`` float32
  (-1 where undefined; the channel layout abf_uv_dump writes) and
  ``flat_record.json`` (metrics, method, sha256 of every file).
* ``verify_package(dir)``: recompute the metric from the packaged mesh and
  UV; must equal the record exactly (JSON-level equality of every metric)
  and every sha256 must match. Returns (ok, report).
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import tifffile

from . import abf as ABF
from . import core as FL
from . import tifxyz as T

RESCALE_LIMIT = 1.5
METHODS = ("vc_flatten", "slim", "arap")
PKG_VERSION = 1


@dataclass
class FlatResult:
    method: str
    uv: np.ndarray  # (H, W, 2) float64, NaN undefined
    seconds: float
    info: dict = field(default_factory=dict)


def _step(points: np.ndarray, step: float | None) -> float:
    if step is not None:
        return float(step)
    # median edge length of the grid (nominal step of an isometric grid)
    p = np.asarray(points, dtype=np.float64)
    L = np.concatenate([np.linalg.norm(p[:, 1:] - p[:, :-1], axis=-1).ravel(),
                        np.linalg.norm(p[1:] - p[:-1], axis=-1).ravel()])
    L = L[np.isfinite(L) & (L > 0)]
    return float(np.median(L))


def flatten(points: np.ndarray, method: str, *, workdir: str | Path | None = None, voxel_um: float | None = None,
            step: float | None = 20.0) -> FlatResult:
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}")
    p = np.asarray(points, dtype=np.float64)
    st = _step(p, step)
    t0 = time.time()
    if method == "vc_flatten":
        uv, info = ABF.flatten_abf(p, st, workdir)
        return FlatResult(method, uv, time.time() - t0, info)
    mesh = FL.grid_to_mesh(p)
    UV0 = FL.grid_init_uv(mesh, st)
    if method == "slim":
        UV, info = FL.flatten_slim(mesh.V, mesh.F, UV0)
    else:
        UV, info = FL.flatten_arap(mesh.V, mesh.F, UV0)
    info = {k: v for k, v in info.items() if k != "energy_history"}
    return FlatResult(method, FL.uv_to_grid(mesh, UV, p.shape[:2]), time.time() - t0, info)


def metrics(points: np.ndarray, uv: np.ndarray, quads: np.ndarray | None = None) -> dict:
    p = np.asarray(points, dtype=np.float64)
    q = FL.quad_mask(p) if quads is None else np.asarray(quads, bool)
    return json.loads(json.dumps(FL.evaluate(p, np.asarray(uv, np.float64), q), default=float))


def collapse_flags(m: dict, info: dict | None = None) -> dict:
    """Flags: flips > 0; ABF rescale factor outside [1/1.5, 1.5]; any
    undefined UV. ``collapsed`` is True if any flag is set."""
    info = info or {}
    f = {"flipped": m.get("flipped_triangles", 0) > 0,
         "undefined_uv": m.get("n_triangles_uv_undefined", 0) > 0}
    rs = info.get("abf_rescale_factor")
    f["abf_rescale"] = rs is not None and not (1 / RESCALE_LIMIT <= rs <= RESCALE_LIMIT)
    f["abf_rescale_factor"] = rs
    f["collapsed"] = bool(f["flipped"] or f["undefined_uv"] or f["abf_rescale"])
    return f


# ---------------------------------------------------------------------------
# package I/O and verifier
# ---------------------------------------------------------------------------

def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _write_f32(path: Path, a: np.ndarray) -> None:
    tifffile.imwrite(str(path), np.ascontiguousarray(a, dtype="<f4"), photometric="minisblack",
                     compression=None, metadata=None, software=False)


def write_package(d: str | Path, points: np.ndarray, uv: np.ndarray, *, method: str, step: float = 20.0,
                  voxel_um: float | None = None, quads: np.ndarray | None = None, info: dict | None = None,
                  source: str = "") -> dict:
    """Write mesh + UV + record. The record's metrics are computed from the
    float32 values actually written (so the verifier can match exactly)."""
    d = Path(d)
    d.mkdir(parents=True, exist_ok=True)
    pts32 = T.canonicalize(np.asarray(points))
    T.write(d / "mesh.tifxyz", T.Tifxyz(pts32, (1 / step, 1 / step), "flat_package"), overwrite=True)
    uv = np.asarray(uv, np.float64)
    bad = ~np.isfinite(uv).all(-1)
    u32 = np.where(bad, -1.0, uv[..., 0]).astype("<f4")
    v32 = np.where(bad, -1.0, uv[..., 1]).astype("<f4")
    _write_f32(d / "u.tif", u32)
    _write_f32(d / "v.tif", v32)
    if quads is None:
        quads = FL.quad_mask(pts32)
    np.save(d / "quads.npy", np.asarray(quads, bool))
    pk = read_package(d, record=False)
    m = metrics(pk["points"], pk["uv"], pk["quads"])
    rec = {"package_version": PKG_VERSION, "method": method, "step_vox": step, "voxel_um": voxel_um,
           "source": source, "metrics": m, "collapse": collapse_flags(m, info), "info": info or {},
           "files": {f: _sha(d / f) for f in ("mesh.tifxyz/x.tif", "mesh.tifxyz/y.tif", "mesh.tifxyz/z.tif",
                                                "mesh.tifxyz/meta.json", "u.tif", "v.tif", "quads.npy")}}
    (d / "flat_record.json").write_text(json.dumps(rec, indent=1, sort_keys=True, default=float) + "\n")
    return rec


def read_package(d: str | Path, record: bool = True) -> dict:
    d = Path(d)
    mesh = T.read(d / "mesh.tifxyz")
    u = tifffile.imread(d / "u.tif").astype(np.float64)
    v = tifffile.imread(d / "v.tif").astype(np.float64)
    uv = np.stack([u, v], -1)
    uv[(u == -1) | (v == -1)] = np.nan
    out = {"points": mesh.points, "uv": uv, "quads": np.load(d / "quads.npy"), "scale": mesh.scale}
    if record:
        out["record"] = json.loads((d / "flat_record.json").read_text())
    return out


def verify_package(d: str | Path) -> tuple[bool, dict]:
    d = Path(d)
    pk = read_package(d)
    rec = pk["record"]
    rep = {"sha_mismatch": [f for f, h in rec["files"].items() if _sha(d / f) != h]}
    m = metrics(pk["points"], pk["uv"], pk["quads"])
    a = json.dumps(m, sort_keys=True, default=float)
    b = json.dumps(rec["metrics"], sort_keys=True, default=float)
    rep["metrics_equal"] = a == b
    if not rep["metrics_equal"]:
        rep["diff_keys"] = sorted(k for k in m if json.dumps(m[k], sort_keys=True, default=float)
                                  != json.dumps(rec["metrics"].get(k), sort_keys=True, default=float))
    rep["collapse_equal"] = collapse_flags(m, rec.get("info")) == rec["collapse"]
    rep["pct_quads_within_5pct"] = m["pct_quads_within_5pct"]
    ok = not rep["sha_mismatch"] and rep["metrics_equal"] and rep["collapse_equal"]
    return ok, rep
