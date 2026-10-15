# Provenance: Project HERCULES | owner the owner | [id removed]
"""Bring an organizer mesh that exists only on another volume's voxel frame
onto the canvas frame, with the organizer's own transform recovered from
segments that the organizer published on BOTH frames (same grid, vertex for
vertex). Geometry only.

The two frames' grids are resampled independently (same nominal scale in
their own voxels), so vertices do not correspond one to one. The 3-D affine is
initialised from the grid-index ratio (voxel-size ratio) and refined by
point-to-plane ICP against the 5 x 5 dense canvas-frame meshes of the fit
segments. It is validated on HELD-OUT segments (normal distance of the
transformed source mesh to the organizer's canvas-frame mesh) and applied
only if the held-out median <= --max-nd-median and p90 <= --max-nd-p90 vox.
Normal accuracy is what the same-papyrus test needs; tangential accuracy is
only as good as the grid initialisation (reported as grid_init_rms).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import boto3
import numpy as np
from botocore import UNSIGNED
from botocore.config import Config

from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import contam3d as C  # noqa: E402

from hercules.geometry.tifxyz import TifxyzMesh, read_tifxyz, sample_grid, valid_mask, write_tifxyz  # noqa: E402

BUCKET = "vesuvius-challenge-open-data"


def fetch_dir(s3, prefix: str, out: Path, rec: dict) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    for n in ("x.tif", "y.tif", "z.tif", "meta.json"):
        for i in range(5):
            try:
                b = s3.get_object(Bucket=BUCKET, Key=prefix + n)["Body"].read()
                break
            except Exception:
                if i == 4:
                    raise
                time.sleep(2 ** (i + 1))
        (out / n).write_bytes(b)
        rec[prefix + n] = hashlib.sha256(b).hexdigest()
    return out


def grid_pairs(src: TifxyzMesh, dst: TifxyzMesh, ratio: float):
    """Corresponding points via grid index scaling (initialisation only)."""
    H, W = dst.shape
    ii, jj = np.mgrid[0:H, 0:W].astype(np.float64)
    X = sample_grid(src.points, ii * ratio, jj * ratio).reshape(-1, 3)
    Y = dst.points.reshape(-1, 3).astype(np.float64)
    ok = (X != -1).all(1) & valid_mask(dst.points).reshape(-1)
    return X[ok], Y[ok]


def fit_affine(X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    A = np.hstack([X, np.ones((X.shape[0], 1))])
    M, *_ = np.linalg.lstsq(A, Y, rcond=None)
    return M  # (4, 3): Y = [X 1] @ M


def apply(M, X):
    return np.hstack([X, np.ones((X.shape[0], 1))]) @ M


def transformed_dense(src: TifxyzMesh, M, ratio: float, k: int = 2) -> C.DenseSurface:
    p = src.points.reshape(-1, 3).astype(np.float64)
    v = valid_mask(src.points).reshape(-1)
    q = np.full_like(p, -1.0)
    q[v] = apply(M, p[v])
    return C.dense_surface(q.reshape(src.points.shape), (src.scale[0] * ratio, src.scale[1] * ratio), k)


def icp_point_to_plane(M, srcs, dsts, ratio, iters=6, radius=6.0, workers=4):
    """Refine the (4, 3) affine M so that the transformed source meshes lie on
    the destination dense surfaces (point-to-plane least squares, 12 dof)."""
    trees = [cKDTree(d.points) for d in dsts]
    hist = []
    for it in range(iters):
        rows, rhs = [], []
        for s, d, t in zip(srcs, dsts, trees):
            S = transformed_dense(s, M, ratio)
            dd, j = t.query(S.points, k=1, distance_upper_bound=radius, workers=workers)
            g = np.isfinite(dd)
            x, tp, n = S.points[g], d.points[j[g]], d.normals[j[g]]
            ok = np.isfinite(n).all(1)
            x, tp, n = x[ok], tp[ok], n[ok]
            rows.append(np.hstack([n[:, [0]] * x, n[:, [1]] * x, n[:, [2]] * x, n]))
            rhs.append(-((x - tp) * n).sum(1))
        sol, *_ = np.linalg.lstsq(np.concatenate(rows), np.concatenate(rhs), rcond=None)
        B, c = sol[:9].reshape(3, 3), sol[9:]
        # x' = (I + B) x + c applied after M
        L = M[:3] @ (np.eye(3) + B).T
        t = M[3] @ (np.eye(3) + B).T + c
        M = np.vstack([L, t])
        hist.append(dict(iter=it, max_abs_B=float(np.abs(B).max()), max_abs_c=float(np.abs(c).max())))
        if np.abs(B).max() < 1e-7 and np.abs(c).max() < 1e-4:
            break
    return M, hist


def nd_stats(S: C.DenseSurface, D: C.DenseSurface, workers=4) -> dict:
    nd = C.normal_distances(S, D, radius=6.0, workers=workers)
    f = np.isfinite(nd)
    return dict(coverage=float(f.mean()), nd_median=float(np.median(nd[f])),
                nd_p90=float(np.percentile(nd[f], 90)), nd_p99=float(np.percentile(nd[f], 99)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scroll", default="PHerc0139")
    ap.add_argument("--src-vol", default="20260102150214")
    ap.add_argument("--dst-vol", default="20250728140407")
    ap.add_argument("--fit", default="20260126000000-w045_2026012619,20260215000000-w024_2026021572")
    ap.add_argument("--check", default="20260220000000-w053_2026022021")
    ap.add_argument("--target", default="20260130000001-w030_202601301912")
    ap.add_argument("--work", default="/work/sib_contam/xform")
    ap.add_argument("--meshes", default="/work/sib_contam/meshes")
    ap.add_argument("--src-tag", default="2.399um")
    ap.add_argument("--dst-vox-um", type=float, default=None, help="default: from the volume metadata.json")
    ap.add_argument("--manifest", default="logs/sib/contam/mesh_manifest_0139.json")
    ap.add_argument("--max-nd-median", type=float, default=0.25)
    ap.add_argument("--max-nd-p90", type=float, default=1.0)
    ap.add_argument("--out-json", required=True)
    a = ap.parse_args(argv)
    if a.dst_vox_um is None:
        man = json.loads(Path(a.manifest).read_text())
        a.dst_vox_um = 1000.0 * float(man["volume_metadata"]["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"])
    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED, retries={"max_attempts": 8}),
                      region_name="us-east-1")
    work = Path(a.work)
    hashes: dict = {}
    vp = [q["Prefix"] for q in s3.list_objects_v2(Bucket=BUCKET, Prefix=f"{a.scroll}/volumes/", Delimiter="/")
          .get("CommonPrefixes", []) if q["Prefix"].split("/")[-2].startswith(a.src_vol)]
    if len(vp) != 1:
        raise SystemExit(f"source volume prefix not unique: {vp}")
    vb = s3.get_object(Bucket=BUCKET, Key=vp[0] + "metadata.json")["Body"].read()
    hashes[vp[0] + "metadata.json"] = hashlib.sha256(vb).hexdigest()
    src_vox_um = 1000.0 * float(json.loads(vb)["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"])
    ratio = float(a.dst_vox_um) / src_vox_um
    loaded = {}
    for role, segs in (("fit", a.fit.split(",")), ("check", a.check.split(","))):
        for sname in segs:
            sid = sname.split("-")[0]
            src = fetch_dir(s3, f"{a.scroll}/segments/{sname}/mesh/{sid}-on-{a.src_vol}-{a.src_tag}.tifxyz/",
                            work / sname, hashes)
            dst = Path(a.meshes) / a.scroll / sname
            loaded[sname] = (role, read_tifxyz(src), read_tifxyz(dst))
    X, Y = zip(*(grid_pairs(sv, dv, ratio) for r, sv, dv in loaded.values() if r == "fit"))
    M0 = fit_affine(np.concatenate(X), np.concatenate(Y))
    grid_rms = float(np.sqrt(np.mean(np.linalg.norm(apply(M0, np.concatenate(X)) - np.concatenate(Y), axis=1) ** 2)))
    dense = {n: C.dense_surface(dv.points, dv.scale, 5) for n, (r, sv, dv) in loaded.items()}
    fit_names = [n for n, v in loaded.items() if v[0] == "fit"]
    M, hist = icp_point_to_plane(M0, [loaded[n][1] for n in fit_names], [dense[n] for n in fit_names], ratio)
    res = {n: dict(role=r, init=nd_stats(transformed_dense(sv, M0, ratio), dense[n]),
                   final=nd_stats(transformed_dense(sv, M, ratio), dense[n]))
           for n, (r, sv, dv) in loaded.items()}
    L = M[:3].T
    out = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
           "src_volume": a.src_vol, "dst_volume": a.dst_vol, "voxel_ratio_dst_over_src": ratio,
           "voxel_size_um": {"src": src_vox_um, "dst": a.dst_vox_um,
                             "from": "volume metadata.json scan.tomo.acquisition.detector.samplePixelSize"},
           "affine_rows_x1_to_dst": M.tolist(), "grid_init_rms_vox": grid_rms,
           "linear_singular_values": np.linalg.svd(L, compute_uv=False).tolist(), "icp": hist,
           "normal_distance_vox": res, "fit_segments": fit_names,
           "check_segments": [n for n, v in loaded.items() if v[0] == "check"],
           "bars": dict(max_nd_median=a.max_nd_median, max_nd_p90=a.max_nd_p90, min_coverage=0.95),
           "downloaded_sha256": hashes}
    chk = [v["final"] for v in res.values() if v["role"] == "check"]
    applied = all(c["nd_median"] <= a.max_nd_median and c["nd_p90"] <= a.max_nd_p90 and c["coverage"] >= 0.95
                  for c in chk)
    out["applied"] = bool(applied)
    if applied:
        tgt = fetch_dir(s3, f"{a.scroll}/segments/{a.target}/mesh/intermediate/tifxyz_original/", work / a.target, hashes)
        m = read_tifxyz(tgt)
        ok = valid_mask(m.points)
        p = np.full(m.points.shape, -1.0, dtype=np.float32)
        p[ok] = apply(M, m.points[ok].astype(np.float64)).astype(np.float32)
        dst = work / f"{a.target}.on-{a.dst_vol}"
        # grid step = 1/scale SOURCE voxels = 1/(scale*ratio) destination voxels
        sc = (m.scale[0] * ratio, m.scale[1] * ratio)
        write_tifxyz(dst, TifxyzMesh(points=p, scale=sc, uuid=m.uuid + f"_on_{a.dst_vol}",
                                     meta={"derived_by": "tools/sib/contam/w030_transform.py (affine, see json)"}))
        out["target"] = a.target
        out["target_mesh_out"] = str(dst)
        out["target_grid_hw"] = list(m.shape)
        out["target_scale_src"] = list(m.scale)
        out["target_scale_dst"] = list(sc)
        out["target_frame_note"] = ("the bucket index gives the target's bbox_transformed on the source volume equal "
                                    "to its own bbox (overlap 1.0): its original tifxyz is already in the source frame")
        out["target_out_sha256"] = {n: hashlib.sha256((dst / n).read_bytes()).hexdigest()
                                    for n in ("x.tif", "y.tif", "z.tif", "meta.json")}
    Path(a.out_json).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ("normal_distance_vox", "linear_singular_values", "applied")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
