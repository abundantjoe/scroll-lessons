# Provenance: Project HERCULES | owner the owner | [id removed]
"""Synthetic surface-prediction volumes and tracer harness for the gated tracer (build c).

Sheets are arcs of cylinders whose axis is parallel to z (like scroll wraps). A voxel is
"sheet" (value 255) iff | r - R | <= half_thickness and its arc angle lies inside the
sheet's angle range; holes and gaps are removed from the prediction. Everything else is 0.

Coordinates: volumes are indexed [z, y, x]; tifxyz vertices are (x, y, z).
Numbers only: nothing here writes or reads an image for viewing.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

VOXEL_UM = 9.362  # synthetic volumes declare this in their own meta.json
VC_IMG = "ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f"
BIN_VANILLA = "/work/villa/volume-cartographer/build/hrc-release-gcc/bin"
BIN_GATED = os.environ.get("HRC_BIN_GATED", "/work/villa-gated/volume-cartographer/build/hrc-gated-c4/bin")


@dataclass
class Sheet:
    R: float                      # radius (vox)
    phi: tuple[float, float]      # angle range (rad), phi measured from +y towards +x
    z: tuple[float, float]        # z range (vox)
    half_t: float = 1.0           # half thickness (vox)
    holes: list = field(default_factory=list)  # (phi_c, z_c, radius_vox) discs in (arc, z)
    gaps: list = field(default_factory=list)   # (phi0, phi1) full-height angular gaps


@dataclass
class Scene:
    shape: tuple[int, int, int]   # (Z, Y, X)
    axis_xy: tuple[float, float]  # cylinder axis position (x, y)
    sheets: list


def cyl(scene: Scene, X, Y):
    ax, ay = scene.axis_xy
    dx, dy = X - ax, Y - ay
    return np.hypot(dx, dy), np.arctan2(dx, dy)


def render(scene: Scene) -> np.ndarray:
    Z, Y, X = scene.shape
    yy, xx = np.mgrid[0:Y, 0:X].astype(np.float64)
    r, phi = cyl(scene, xx, yy)
    zz = np.arange(Z, dtype=np.float64)
    vol = np.zeros(scene.shape, dtype=np.uint8)
    for s in scene.sheets:
        m2 = (np.abs(r - s.R) <= s.half_t) & (phi >= s.phi[0]) & (phi <= s.phi[1])
        for g0, g1 in s.gaps:
            m2 &= ~((phi >= g0) & (phi <= g1))
        zin = (zz >= s.z[0]) & (zz <= s.z[1])
        m3 = m2[None, :, :] & zin[:, None, None]
        for pc, zc, rad in s.holes:
            arc = s.R * (phi - pc)
            d2 = arc[None, :, :] ** 2 + (zz[:, None, None] - zc) ** 2
            m3 &= ~(d2 <= rad * rad)
        vol[m3] = 255
    return vol


def write_zarr(path: Path, vol: np.ndarray, uuid: str, chunk: int = 64) -> None:
    import numcodecs
    import zarr

    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    Z, Y, X = vol.shape
    meta = {"type": "vol", "uuid": uuid, "name": uuid, "format": "zarr", "width": X, "height": Y,
            "slices": Z, "voxelsize": VOXEL_UM, "min": 0.0, "max": 255.0}
    (path / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    (path / ".zgroup").write_text(json.dumps({"zarr_format": 2}) + "\n")
    attrs = {"multiscales": [{"version": "0.4", "name": "/",
                              "axes": [{"name": a, "type": "space"} for a in "zyx"],
                              "datasets": [{"path": "0", "coordinateTransformations": [
                                  {"type": "scale", "scale": [1.0, 1.0, 1.0]}]}]}]}
    (path / ".zattrs").write_text(json.dumps(attrs, indent=2) + "\n")
    z = zarr.open_array(str(path / "0"), mode="w", shape=vol.shape, chunks=(chunk,) * 3, dtype="u1",
                        compressor=numcodecs.Blosc(cname="zstd", clevel=1, shuffle=1),
                        fill_value=0, dimension_separator=".")
    z[:] = vol


def run_logged(label: str, cmd: list[str], out: Path, runs_jsonl: Path) -> int:
    t0 = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    w0 = time.time()
    with open(out, "wb") as f:
        rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT)
    t1 = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    h = hashlib.sha256(Path(out).read_bytes()).hexdigest()
    with open(runs_jsonl, "a") as f:
        f.write(json.dumps({"label": label, "utc_start": t0, "utc_end": t1, "wall_s": round(time.time() - w0, 2),
                            "exit": rc, "out_sha256": h, "out": str(out), "cmd": cmd}) + "\n")
    return rc


def vc_cmd(binary_dir: str, app: str, args: list[str], cpus: int = 1, threads: int = 1) -> list[str]:
    proxy = os.environ.get("HTTPS_PROXY", "")
    return ["docker", "run", "--rm", "--network", "host", "--cpus", str(cpus),
            "-e", f"OMP_NUM_THREADS={threads}", "-e", f"HTTPS_PROXY={proxy}", "-e", f"https_proxy={proxy}",
            "-e", "HOME=/work/vchome",  # persistent VC3D remote-chunk cache (~/.VC3D) across runs
            "-e", "SSL_CERT_FILE=/root/.ccr/ca-bundle.crt", "-e", "CURL_CA_BUNDLE=/root/.ccr/ca-bundle.crt",
            "-v", "/root/.ccr/ca-bundle.crt:/root/.ccr/ca-bundle.crt:ro",
            "-v", "/home/user:/home/user", "-v", "/work:/work",
            VC_IMG, f"{binary_dir}/{app}", *args]


def find_single_segment(target_dir: Path) -> Path | None:
    segs = [p for p in Path(target_dir).iterdir() if p.is_dir() and (p / "x.tif").exists()]
    if len(segs) != 1:
        return None
    return segs[0]


# ------------------------------------------------------------------ metrics
def vertex_cyl(scene: Scene, pts: np.ndarray):
    """(r, phi, z) of valid vertices; pts is (H, W, 3) (x, y, z)."""
    r, phi = cyl(scene, pts[..., 0].astype(np.float64), pts[..., 1].astype(np.float64))
    return r, phi, pts[..., 2].astype(np.float64)


def coverage(scene: Scene, sheet_idx: int, pts: np.ndarray, valid: np.ndarray, res: float = 1.0,
             erode: float = 20.0) -> dict:
    """Rasterise every fully valid quad in (arc s = R*phi, z) of the given sheet and compare with the
    sheet's true support (prediction voxels of that sheet, holes and gaps removed)."""
    import cv2

    s = scene.sheets[sheet_idx]
    r, phi, z = vertex_cyl(scene, pts)
    S0, S1 = s.R * s.phi[0], s.R * s.phi[1]
    W = int(math.ceil((S1 - S0) / res)) + 1
    H = int(math.ceil((s.z[1] - s.z[0]) / res)) + 1
    traced = np.zeros((H, W), np.uint8)
    count = np.zeros((H, W), np.int32)
    qv = valid[:-1, :-1] & valid[:-1, 1:] & valid[1:, :-1] & valid[1:, 1:]
    su = (s.R * phi - S0) / res
    zv = (z - s.z[0]) / res
    for j, i in zip(*np.nonzero(qv)):
        poly = np.array([[su[j, i], zv[j, i]], [su[j, i + 1], zv[j, i + 1]],
                         [su[j + 1, i + 1], zv[j + 1, i + 1]], [su[j + 1, i], zv[j + 1, i]]])
        cv2.fillPoly(traced, [np.round(poly * 4).astype(np.int32)], 1, shift=2)
        # fold detection: each quad shrunk 2 % towards its centroid, so shared edges never double count
        shrunk = poly.mean(0) + 0.98 * (poly - poly.mean(0))
        one = np.zeros((H, W), np.uint8)
        cv2.fillPoly(one, [np.round(shrunk * 4).astype(np.int32)], 1, shift=2)
        count += one
    ss = S0 + np.arange(W) * res
    zz = s.z[0] + np.arange(H) * res
    SS, ZZ = np.meshgrid(ss, zz)
    ph = SS / s.R
    truth = np.ones((H, W), bool)
    for g0, g1 in s.gaps:
        truth &= ~((ph >= g0) & (ph <= g1))
    for pc, zc, rad in s.holes:
        truth &= ~((s.R * (ph - pc)) ** 2 + (ZZ - zc) ** 2 <= rad * rad)
    t = traced.astype(bool)
    # achievable support: a gated tracer must not place vertices past the physical sheet border,
    # so a grid of step `erode` can leave up to one step uncovered along every border
    from scipy.ndimage import distance_transform_edt
    pad = np.pad(truth, 1, constant_values=False)
    core = (distance_transform_edt(pad)[1:-1, 1:-1] > erode / res)
    return {"truth_px": int(truth.sum()), "traced_px": int(t.sum()), "core_px": int(core.sum()),
            "covered_core_frac": float((t & core).sum() / max(1, core.sum())),
            "double_covered_frac": float((count >= 2).sum() / max(1, (count >= 1).sum())),
            "covered_frac": float((t & truth).sum() / max(1, truth.sum())),
            "traced_outside_truth_frac": float((t & ~truth).sum() / max(1, t.sum()))}


def surface_report(scene: Scene, seg: Path, seed_sheet: int = 0) -> dict:
    import sys
    sys.path.insert(0, "/home/user/dominion/src")
    from hercules.geometry.tifxyz import read_tifxyz, area_vox2, edge_fraction_within

    m = read_tifxyz(seg)
    pts = m.points.astype(np.float64)
    v = m.valid
    r, phi, z = vertex_cyl(scene, pts)
    rv = r[v]
    nearest = np.array([np.argmin([abs(rr - s.R) for s in scene.sheets]) for rr in rv]) if rv.size else np.array([])
    resid = np.array([min(abs(rr - s.R) for s in scene.sheets) for rr in rv]) if rv.size else np.array([])
    # edges whose two vertices lie nearest to different sheets
    lab = np.full(v.shape, -1)
    lab[v] = nearest
    cross_u = (lab[:, 1:] >= 0) & (lab[:, :-1] >= 0) & (lab[:, 1:] != lab[:, :-1])
    cross_v = (lab[1:] >= 0) & (lab[:-1] >= 0) & (lab[1:] != lab[:-1])
    meta = json.loads((seg / "meta.json").read_text())
    rep = {
        "n_valid": int(v.sum()),
        "grid_shape": list(v.shape),
        "area_vox2": area_vox2(pts),
        "n_vertices_by_sheet": [int((nearest == k).sum()) for k in range(len(scene.sheets))],
        "n_bridge_edges": int(cross_u.sum() + cross_v.sum()),
        "max_abs_r_resid": float(resid.max()) if resid.size else None,
        "p99_abs_r_resid": float(np.percentile(resid, 99)) if resid.size else None,
        "edge_frac_10pct": edge_fraction_within(pts, 20.0, 10.0),
        "coverage_seed_sheet": coverage(scene, seed_sheet, pts, v),
        "meta_gate": {k: meta[k] for k in meta if k.startswith("hrc_")},
        "max_gen": meta.get("max_gen"),
    }
    gr = seg / "gate_reject.tif"
    if gr.exists():
        import tifffile
        g = tifffile.imread(gr)
        rep["gate_reject_counts"] = {"dist": int(((g & 1) > 0).sum()), "cost": int(((g & 2) > 0).sum())}
    return rep


def params_json(path: Path, **kw) -> Path:
    p = {"mode": "seed", "step_size": 20, "min_area_cm": 0, "generations": 45, "thread_limit": 1,
         "direction_fields": [], "voxelsize": VOXEL_UM}
    p.update(kw)
    Path(path).write_text(json.dumps(p, indent=1) + "\n")
    return Path(path)
