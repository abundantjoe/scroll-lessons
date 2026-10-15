# Provenance: Project HERCULES | owner the owner | [id removed]
"""Training-pool allow-list for LC384 (task devloop-r1): pairs0139 kept tiles minus everything DEV. Numbers only.

A tile is ALLOWED only if every check passes (fail-closed; any missing input or unverifiable tile is rejected):
 1. kept by pairs0139 (registry row with a shard; its gates, Rule N and Rule S already applied by that builder);
 2. its segment is not a DEV segment (dev_registry.json, every scroll), not excluded by pairs0139 exclusion.json, and
    not in any DEV hold-out list (dev_registry scrolls.*.holdout_segments);
 3. independent 3-D clearance from every DEV window (CORR-RETRACE-RULE fail-closed form, nearest densified vertex):
    - DEV surface = the organizer 9 um mesh of the DEV segment sampled at canvas pixels P = y0..y0+h, x0..x0+w with
      stride 2 px (grid coordinate (P + 0.5) * s, hercules.geometry.tifxyz.sample_grid, valid samples only);
    - tile surface = the tile's own segment mesh sampled the same way at stride 4 px over its 128 x 128 canvas pixels;
    - required: min nearest-vertex distance >= CLEAR = 11 vox (pairs0139 Rule S) + 1.42 (half-diagonal of the DEV
      2 px sampling) + 2.83 (half-diagonal of the tile 4 px sampling) -> 16 vox (rounded up);
    - at least 90 % of the tile's samples must be valid (else unverifiable -> rejected);
 4. mapping self-check: the tile centre sampled here must match the builder's recorded xyz_centre within 0.5 vox
    (else the canvas mapping is unverified -> rejected).
Meshes: official S3 (vesuvius-challenge-open-data), anonymous, cached under --mesh-dir; sha256 of every file recorded;
DEV meshes must match dev_registry mesh9_sha256.
Output: --out allow.json (sorted tile ids) and --report pool_report.json (counts per rejection reason, clearance
distribution, all hashes)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "src"))
from hercules.geometry.tifxyz import read_tifxyz, sample_grid, valid_mask  # noqa: E402

BUCKET = "vesuvius-challenge-open-data"
CLEAR_VOX = 16.0
DEV_STRIDE, TILE_STRIDE = 2, 4
CENTRE_TOL = 0.5
VALID_MIN = 0.90


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fetch_mesh(scroll, segment_id, mesh_dir, log):
    ts = segment_id.split("-")[0]
    rel = f"{scroll}/segments/{segment_id}/mesh/{ts}-on-20250728140407-9.362um.tifxyz" if scroll == "PHerc0139" else None
    if rel is None:
        raise ValueError(f"no 9 um mesh rule for scroll {scroll}")
    d = os.path.join(mesh_dir, rel)
    os.makedirs(d, exist_ok=True)
    for f in ("meta.json", "x.tif", "y.tif", "z.tif"):
        p = os.path.join(d, f)
        if not os.path.exists(p):
            import boto3
            from botocore import UNSIGNED
            from botocore.config import Config
            boto3.client("s3", config=Config(signature_version=UNSIGNED)).download_file(BUCKET, f"{rel}/{f}", p + ".part")
            os.replace(p + ".part", p)
        log.setdefault(rel, {})[f] = sha(p)
    return d


def canvas_samples(mesh, y0, x0, h, w, stride):
    """3-D points of canvas pixels P (rows y0..y0+h-1, cols x0..x0+w-1, given stride; last row/col included)."""
    ry = np.unique(np.r_[np.arange(y0, y0 + h, stride), y0 + h - 1]).astype(np.float64)
    rx = np.unique(np.r_[np.arange(x0, x0 + w, stride), x0 + w - 1]).astype(np.float64)
    su, sv = float(np.float32(mesh.scale[0])), float(np.float32(mesh.scale[1]))
    R, Cc = np.meshgrid((ry + 0.5) * sv, (rx + 0.5) * su, indexing="ij")
    pts = sample_grid(mesh.points, R, Cc).reshape(-1, 3)
    ok = valid_mask(pts[:, None, :])[:, 0]
    return pts, ok


def centre_point(mesh, y0, x0, size=128):
    su, sv = float(np.float32(mesh.scale[0])), float(np.float32(mesh.scale[1]))
    c = y0 + (size - 1) / 2.0, x0 + (size - 1) / 2.0
    return sample_grid(mesh.points, np.array([(c[0] + 0.5) * sv]), np.array([(c[1] + 0.5) * su])).reshape(3)


def build(rows, dev_windows, dev_segments, excluded_segments, mesh_for, clear=CLEAR_VOX):
    """rows: registry rows (dicts). dev_windows: list of (segment_id, y0, x0, h, w). mesh_for(segment_id) -> TifxyzMesh.
    Returns (allow_ids, report)."""
    from scipy.spatial import cKDTree
    dev_pts = []
    for seg, y0, x0, h, w in dev_windows:
        p, ok = canvas_samples(mesh_for(seg), y0, x0, h, w, DEV_STRIDE)
        dev_pts.append(p[ok])
    tree = cKDTree(np.concatenate(dev_pts)) if dev_pts else None
    reasons, allow, dmin = {}, [], []
    for r in rows:
        why = None
        if not r.get("shard") or not r.get("kept", True):
            why = "not_kept"
        elif r["segment"] in dev_segments:
            why = "dev_segment"
        elif r["segment"] in excluded_segments:
            why = "excluded_segment"
        else:
            m = mesh_for(r["segment"])
            y0, x0, size = int(r["canvas9_y0"]), int(r["canvas9_x0"]), int(r.get("size", 128))
            c = centre_point(m, y0, x0, size)
            rec = r.get("xyz_centre")
            if rec is None or not np.all(np.isfinite(c)) or np.linalg.norm(c - np.asarray(rec, float)) > CENTRE_TOL:
                why = "centre_mismatch"
            else:
                p, ok = canvas_samples(m, y0, x0, size, size, TILE_STRIDE)
                if ok.mean() < VALID_MIN:
                    why = "unverifiable_invalid"
                elif tree is not None:
                    d = float(tree.query(p[ok], k=1)[0].min())
                    dmin.append(d)
                    if d < clear:
                        why = "dev_clearance"
        if why:
            reasons[why] = reasons.get(why, 0) + 1
        else:
            allow.append(r["tile_id"])
    rep = dict(n_rows=len(rows), n_allowed=len(allow), rejected=reasons, clear_vox=clear, dev_stride_px=DEV_STRIDE,
               tile_stride_px=TILE_STRIDE, n_dev_points=int(sum(len(p) for p in dev_pts)),
               clearance_vox_quantiles=({q: float(np.quantile(dmin, q)) for q in (0.0, 0.01, 0.05, 0.5)} if dmin else None))
    return sorted(allow), rep


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True, help="pairs0139 registry directory (*.jsonl)")
    ap.add_argument("--exclusion", required=True, help="pairs0139 logs/sib/pairs0139/exclusion.json")
    ap.add_argument("--dev-registry", required=True, help="devloop logs/sib/devloop/dev_registry.json")
    ap.add_argument("--mesh-dir", default="/work/dl/meshes")
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    a = ap.parse_args(argv)
    reg = json.load(open(a.dev_registry))
    dev_windows, dev_segments, holdout = [], set(), set()
    exp_sha = {}
    for scroll, s in reg["scrolls"].items():
        for w in s.get("windows", []) + s.get("blanks", []):
            dev_segments.add(w["segment_id"])
            if scroll == "PHerc0139":
                dev_windows.append((w["segment_id"], int(w["y0"]), int(w["x0"]), int(w["h"]), int(w["w"])))
        for seg in (s.get("holdout_segments") or {}).get("dev_segments", []):
            holdout.add(seg)
        for seg in (s.get("holdout_segments") or {}).get("samepap_with_dev", {}):
            holdout.add(seg)
        for k, v in (s.get("segments") or {}).items():
            if "mesh9_sha256" in v:
                exp_sha[v["segment_id"]] = v["mesh9_sha256"]
    exc = json.load(open(a.exclusion))
    excluded = {k for k, v in exc["segments"].items() if v.get("excluded")} | holdout
    rows = []
    for fn in sorted(os.listdir(a.registry)):
        if fn.endswith(".jsonl"):
            rows += [json.loads(l) for l in open(os.path.join(a.registry, fn))]
    log, meshes = {}, {}

    def mesh_for(seg):
        if seg not in meshes:
            d = fetch_mesh("PHerc0139", seg, a.mesh_dir, log)
            if seg in exp_sha:
                got = {f: log[os.path.relpath(d, a.mesh_dir)][f] for f in ("x.tif", "y.tif", "z.tif")}
                assert all(got[f] == exp_sha[seg][f] for f in got if f in exp_sha[seg]), f"DEV mesh hash mismatch {seg}"
            meshes[seg] = read_tifxyz(d)
        return meshes[seg]

    allow, rep = build(rows, dev_windows, dev_segments, excluded, mesh_for)
    rep.update(provenance="Project HERCULES | owner the owner | [id removed]", dev_windows_0139=dev_windows,
               dev_segments=sorted(dev_segments), excluded_segments=sorted(excluded), mesh_sha256=log,
               inputs={k: sha(getattr(a, k)) for k in ("exclusion", "dev_registry")},
               registry_sha256={fn: sha(os.path.join(a.registry, fn)) for fn in sorted(os.listdir(a.registry)) if fn.endswith(".jsonl")},
               code_sha256=sha(os.path.abspath(__file__)))
    json.dump(allow, open(a.out, "w"))
    json.dump(rep, open(a.report, "w"), indent=1)
    print(json.dumps({k: rep[k] for k in ("n_rows", "n_allowed", "rejected", "clearance_vox_quantiles")}))


if __name__ == "__main__":
    main()
