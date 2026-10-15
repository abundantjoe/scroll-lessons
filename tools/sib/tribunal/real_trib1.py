# Provenance: Project HERCULES | owner the owner | [id removed]
"""REAL-TRIB-1: the pre-read gate on official CT renders of non-eligible PHerc0139
(base-training segments w040, w044; volume 20250728140407, 9.362 um from metadata.json).
CT stacks only: no ink map, no inference, no image file, no read, nothing viewed.

Per window (384 x 384 px on the organizer canvas, fully render-valid with a 16 px margin,
6 per segment spread over the segment):
  clean      official vc_render_tifxyz -n 31 --flip-normals at the declared crop
  offset8    official render at the crop shifted 8 px (direction cycles over the 8 compass
             directions), recorded at the declared crop
  off_by_one official -n 33 render at the declared crop; slices [0:31] (lag -1) or [2:33]
             (lag +1), alternating; [1:32] must equal the clean -n 31 render
  swap_depth clean[::-1]; mirror: clean flipped left-right / up-down (alternating)
  wrong_voxel record voxel 9.366 (PHerc0841's), or the PHerc0841 metadata.json (foreign)
Re-trace, from official 0139 geometry: windows on w024 / w053 where the official re-traces
w023 / w052 overlap (RCBANK-1 pairs) must be SAME; windows of the same segments where the
re-trace is > 50 vox away, and every base-training trace, must not be.

    python tools/sib/tribunal/real_trib1.py WORKDIR MESH_ROOT meshes_fetched.json OUT.json
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from hercules.geometry.tifxyz import densify, read_tifxyz, valid_mask
from hercules.pipeline import canvas as C
from hercules.pipeline.window import render_command, voxel_size_from_metadata
from hercules.tribunal import faults as F
from hercules.tribunal import preread as P

B = "vesuvius-challenge-open-data"
# Overridable for other protocols (REAL-TRIB-2 iii): TRIB_VOL, TRIB_FOREIGN_META, TRIB_SKIP_RETRACE=1.
VOL = os.environ.get("TRIB_VOL", "PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr")
VOL_URL = f"s3://{B}/{VOL}"
FOREIGN_META = os.environ.get("TRIB_FOREIGN_META",
                              "PHerc0841/volumes/20250821151531-9.366um-1.2m-113keV-masked.zarr/metadata.json")
WIN, MARGIN, PER_SEG = 384, 16, 6
SEGS = ("w040", "w044")


def s3_get(key: str, dst: Path) -> str:
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config

    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        boto3.client("s3", config=Config(signature_version=UNSIGNED)).download_file(B, key, str(dst))
    return hashlib.sha256(dst.read_bytes()).hexdigest()


def open_volume():
    import s3fs
    import zarr

    fs = s3fs.S3FileSystem(anon=True)
    return zarr.open(s3fs.S3Map(root=f"{B}/{VOL}/0", s3=fs, check=False), mode="r")


class CachedVolume:
    """Serves reads from the last block fetched when it contains the request (all cases
    of one window read the same block, which is fetched from S3 once)."""

    def __init__(self, vol):
        self.vol, self.shape, self.lo, self.block = vol, vol.shape, None, None

    def __getitem__(self, sl):
        lo = [s.start for s in sl]
        hi = [s.stop for s in sl]
        if self.block is not None and all(a >= b for a, b in zip(lo, self.lo)) and \
                all(a <= b + n for a, b, n in zip(hi, self.lo, self.block.shape)):
            return self.block[tuple(slice(a - b, c - b) for a, b, c in zip(lo, self.lo, hi))]
        pad = 24
        lo2 = [max(0, a - pad) for a in lo]
        hi2 = [min(n, a + pad) for a, n in zip(hi, self.shape)]
        self.block = np.asarray(self.vol[tuple(slice(a, b) for a, b in zip(lo2, hi2))])
        self.lo = lo2
        return self.block[tuple(slice(a - b, c - b) for a, b, c in zip(lo, lo2, hi))]


def _valid_window_fast(V, NV, cv, y0, x0, h, w):
    """Exactly emulate_gen's render-valid rule for one window, from vertex validity V and finite
    official normals NV computed once per mesh: all 4 bilinear corners valid, nearest vertex (C lround)
    inside the grid, valid and with a finite normal."""
    H, W = V.shape
    v, _ = cv.pixel_to_grid(np.arange(y0, y0 + h, dtype=np.float64) - cv.origin[0], 0.0)
    _, u = cv.pixel_to_grid(0.0, np.arange(x0, x0 + w, dtype=np.float64) - cv.origin[1])
    fy, fx = np.clip(v, 0, H - 1), np.clip(u, 0, W - 1)
    ya, xa = np.floor(fy).astype(np.int64), np.floor(fx).astype(np.int64)
    yb, xb = np.minimum(ya + 1, H - 1), np.minimum(xa + 1, W - 1)
    yi, xi = C.c_lround(v), C.c_lround(u)
    if not ((yi >= 0).all() and (yi < H).all() and (xi >= 0).all() and (xi < W).all()):
        return False
    corners = V[np.ix_(ya, xa)] & V[np.ix_(ya, xb)] & V[np.ix_(yb, xa)] & V[np.ix_(yb, xb)]
    return bool((corners & V[np.ix_(yi, xi)] & NV[np.ix_(yi, xi)]).all())


def pick_windows(points, scale) -> list[tuple[int, int]]:
    """Same rule as pick_windows_slow (REAL-TRIB-1), with normals and validity computed once."""
    cv = C.canvas_for(points, scale)
    Hc, Wc = cv.shape
    p = np.asarray(points, dtype=np.float64)
    V = valid_mask(p)
    NV = np.isfinite(C.vertex_normals_official(np.where(V[..., None], p, -1.0))).all(-1)
    cands = []
    for y0 in range(MARGIN + 32, Hc - WIN - MARGIN - 32, WIN):
        for x0 in range(MARGIN + 32, Wc - WIN - MARGIN - 32, WIN):
            if _valid_window_fast(V, NV, cv, y0 - MARGIN, x0 - MARGIN, WIN + 2 * MARGIN, WIN + 2 * MARGIN):
                cands.append((y0, x0))
    idx = np.unique(np.linspace(0, len(cands) - 1, PER_SEG).round().astype(int)) if cands else []
    return [cands[i] for i in idx]


def pick_windows_slow(points, scale) -> list[tuple[int, int]]:
    cv = C.canvas_for(points, scale)
    Hc, Wc = cv.shape
    cands = []
    for y0 in range(MARGIN + 32, Hc - WIN - MARGIN - 32, WIN):
        for x0 in range(MARGIN + 32, Wc - WIN - MARGIN - 32, WIN):
            c, n = C.emulate_gen(points, cv.with_origin(y0 - MARGIN, x0 - MARGIN), (WIN + 2 * MARGIN, WIN + 2 * MARGIN))
            if C.render_valid(c, n).all():
                cands.append((y0, x0))
    idx = np.unique(np.linspace(0, len(cands) - 1, PER_SEG).round().astype(int)) if cands else []
    return [cands[i] for i in idx]


def render(work: Path, mesh_dir: Path, name: str, y0: int, x0: int, n: int, voxel: float) -> tuple[np.ndarray, list]:
    out = work / "renders" / f"{name}.zarr"
    cmd = ["/work/bin/vc"] + render_command(VOL_URL + "/", mesh_dir, out, voxel, crop_xywh=(x0, y0, WIN, WIN),
                                            num_slices=n, flip_normals=True)
    if not (out / ".done").exists():
        for attempt in range(2):
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0:
                break
        if r.returncode != 0:
            raise RuntimeError(f"render {name} failed: {r.stderr[-400:]}")
        (out / ".done").write_text("ok")
    return P.load_stack(out), cmd


def record(work, name, stack, mesh_dir, mesh_sha, y0, x0, n, voxel, meta_path, meta_source, cmd):
    return {"window_id": name,
            "volume": {"url": VOL_URL, "metadata_source": meta_source, "metadata_json": str(meta_path),
                       "metadata_sha256": P.file_sha256(meta_path)},
            "voxel_size_um": voxel, "mesh": {"path": str(mesh_dir), "sha256": mesh_sha},
            "crop": {"y0": y0, "x0": x0, "h": WIN, "w": WIN}, "n_slices": n, "slice_step": 1.0, "flip_normals": True,
            "stack": {"path": None, "sha256": P.array_sha256(stack)}, "render_command": cmd,
            "display": {"scale": 0.5, "px_per_mm_image": 1000.0 * 0.5 / voxel}}


def gate_array(rec, stack, vol, training):
    """preread_gate with the stack given in memory (written to a scratch zarr)."""
    import zarr

    p = Path(rec["_scratch"])
    g = zarr.open_group(str(p), mode="w")
    g.create_dataset("0", data=stack, chunks=(stack.shape[0], 128, 128))
    rec = {k: v for k, v in rec.items() if k != "_scratch"}
    rec["stack"]["path"] = str(p)
    return P.preread_gate(rec, volume=vol, training=training)


def summ(rep):
    ch = {c["name"]: c for c in rep["checks"]}
    return {"passed": rep["passed"], "failed": rep["failed"],
            "shift": ch["window_offset"]["details"].get("shift_yx"), "best_ncc": ch["window_offset"]["details"].get("best_ncc"),
            "identity_zero_ncc": ch["window_offset"]["details"].get("identity_zero_shift_ncc"),
            "transform": ch["mirror"]["details"].get("transform"), "mirror_margin": ch["mirror"]["details"].get("identity_margin"),
            "depth_margin": ch["depth_order"]["details"].get("fwd_minus_rev"), "winner": ch["depth_order"]["details"].get("winner"),
            "slice_margin": ch["slice_index"]["details"].get("margin"), "lag": ch["slice_index"]["details"].get("lag"),
            "voxel_reason": ch["voxel_size"]["reason"]}


def retrace_study(mesh_root: Path, ids: dict, neg_min: float = 50.0) -> list[dict]:
    find = lambda t: sorted(s for s in ids if f"-{t}_" in s)  # noqa: E731
    base = {s: read_tifxyz(ids[s]).points.astype(np.float64) for t in
            ("w029", "w030", "w035", "w039", "w040", "w041", "w043", "w044", "w045", "w046") for s in find(t)}
    rows = []
    for win_tag, rt_tag in (("w024", "w023"), ("w053", "w052")):
        A = read_tifxyz(ids[find(win_tag)[0]]).points.astype(np.float64)
        Rt = read_tifxyz(ids[find(rt_tag)[0]]).points.astype(np.float64)
        va = valid_mask(A)
        d = P.surface_distances(A[va], densify(Rt, 5), max_dist=60.0, workers=3)
        dmap = np.full(A.shape[:2], np.inf)
        dmap[va] = d
        k = WIN // 20  # a 384 px window spans ~19 grid cells
        pos, neg = [], []
        for r in range(0, A.shape[0] - k, k):
            for c in range(0, A.shape[1] - k, k):
                blk, vb = dmap[r:r + k + 1, c:c + k + 1], va[r:r + k + 1, c:c + k + 1]
                if not vb.all():
                    continue
                if (blk < 1.0).mean() > 0.5:
                    pos.append((r, c))
                elif np.all(blk >= neg_min):
                    neg.append((r, c))
        # negatives: prefer the neighbouring winding (every vertex 5-60 vox from the re-trace);
        # far windows (> 60 vox everywhere) only fill up to 5
        near_neg = [rc for rc in neg if np.isfinite(dmap[rc[0]:rc[0] + k + 1, rc[1]:rc[1] + k + 1]).any()]
        far_neg = [rc for rc in neg if rc not in near_neg]
        negs = near_neg[:: max(1, len(near_neg) // 5)][:5]
        negs += far_neg[:: max(1, len(far_neg) // 5)][:max(0, 5 - len(negs))]
        for kind, lst in (("retrace_pos", pos[:: max(1, len(pos) // 5)][:5]), ("retrace_neg", negs)):
            for (r, c) in lst:
                wblk = dmap[r:r + k + 1, c:c + k + 1]
                sub = A[r:r + k + 1, c:c + k + 1]
                rep = P.check_retrace(sub, {rt_tag: Rt}, workers=3)
                rep_b = P.check_retrace(sub, base, workers=3)
                seg = rep.details["per_segment"][rt_tag]
                rows.append({"case": kind, "neg_min_vox": neg_min,
                             "min_surface_dist_to_retrace_vox": float(np.min(wblk)), "window_seg": win_tag, "retrace_seg": rt_tag, "grid_rc": [r, c],
                             "caught": not rep.passed, "vertex_same": seg["vertex"]["same"], "surface_same": seg["surface"]["same"],
                             "vertex_counts": seg["vertex"]["counts"], "surface_counts": seg["surface"]["counts"],
                             "base_training_same_as": rep_b.details["same_as"]})
    return rows


def main_retrace_only():
    """--retrace-only RAW.json MESHES_JSON NEG_MIN: redo only the re-trace study (geometry only) with
    negatives = windows whose every vertex is >= NEG_MIN vox from the re-trace surface."""
    raw, fetched_json, neg_min = Path(sys.argv[2]), Path(sys.argv[3]), float(sys.argv[4])
    res = json.loads(raw.read_text())
    fetched = json.loads(fetched_json.read_text())
    ids = {k.split("/")[1]: Path(v["mesh"]) for k, v in fetched["segments"].items()
           if k.startswith("PHerc0139/") and "mesh" in v}
    res.setdefault("retrace_superseded", []).append({"neg_min_vox": 50.0, "rows": res.get("retrace", []),
                                                     "note": "0 negatives: the re-trace lies one winding (20-40 vox) away "
                                                             "wherever it does not overlap"})
    res["retrace"] = retrace_study(None, ids, neg_min=neg_min)
    raw.write_text(json.dumps(res, indent=1, default=float) + "\n")
    print(sum(r["case"] == "retrace_pos" for r in res["retrace"]), "pos",
          sum(r["case"] == "retrace_neg" for r in res["retrace"]), "neg")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--retrace-only":
        return main_retrace_only()
    work, mesh_root, fetched_json, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
    t0 = time.time()
    fetched = json.loads(fetched_json.read_text())
    ids = {k.split("/")[1]: Path(v["mesh"]) for k, v in fetched["segments"].items()
           if k.startswith("PHerc0139/") and "mesh" in v}
    meta = work / "meta" / (VOL.replace("/", "_") + "_metadata.json")
    meta_sha = s3_get(f"{VOL}/metadata.json", meta)
    voxel = voxel_size_from_metadata(meta)
    fmeta = work / "meta" / (FOREIGN_META.replace("/", "_"))
    fmeta_sha = s3_get(FOREIGN_META, fmeta)
    fvoxel = voxel_size_from_metadata(fmeta)
    vol = CachedVolume(open_volume())
    res = {"provenance": "Provenance: Project HERCULES | owner the owner | [id removed]",
           "rule": "REAL-TRIB-1 (proposal, approved by the orchestrator 2026-09-25 19:04Z)",
           "volume": VOL_URL, "metadata_sha256": meta_sha, "voxel_um": voxel,
           "foreign_metadata": {"key": FOREIGN_META, "sha256": fmeta_sha, "voxel_um": fvoxel},
           "renderer_sha256": P.file_sha256("/work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz"),
           "not_done": "no ink map, inference, image file, read or view", "rows": []}
    rng = np.random.default_rng(20260925)
    wi = 0
    for tag in SEGS:
        sid = sorted(s for s in ids if f"-{tag}_" in s)[0]
        mesh_dir = ids[sid]
        mesh = read_tifxyz(mesh_dir)
        mesh_sha = P.tree_sha256(mesh_dir)
        for (y0, x0) in pick_windows(mesh.points, mesh.scale):
            name = f"{tag}_y{y0}_x{x0}"
            clean, cmd = render(work, mesh_dir, name + "_n31", y0, x0, 31, voxel)
            n33, _ = render(work, mesh_dir, name + "_n33", y0, x0, 33, voxel)
            d = F.OFFSET_DIRECTIONS[wi % 8]
            off, _ = render(work, mesh_dir, name + f"_off{d[0]}_{d[1]}", y0 + d[0], x0 + d[1], 31, voxel)
            ident = int(np.abs(n33[1:32].astype(int) - clean.astype(int)).max())
            base = dict(mesh_dir=mesh_dir, mesh_sha=mesh_sha, y0=y0, x0=x0, n=31, voxel=voxel, meta_path=meta,
                        meta_source=VOL_URL + "/metadata.json", cmd=cmd)
            sign = (-1, 1)[wi % 2]
            flip = ("flip_lr", "flip_ud")[wi % 2]
            cases = [("clean", clean, {}), ("offset8", off, {"offset_yx": list(d)}),
                     ("swap_depth", np.ascontiguousarray(clean[::-1]), {}),
                     ("mirror", np.ascontiguousarray(clean[:, :, ::-1] if flip == "flip_lr" else clean[:, ::-1, :]), {"mirror": flip}),
                     ("off_by_one", np.ascontiguousarray(n33[0:31] if sign < 0 else n33[2:33]), {"slice_shift": sign}),
                     ("wrong_voxel", clean, {"variant": "value" if wi % 2 == 0 else "foreign_metadata"})]
            for case, stack, info in cases:
                b = dict(base)
                if case == "wrong_voxel":
                    b["voxel"] = fvoxel
                    if info["variant"] == "foreign_metadata":
                        b["meta_path"] = fmeta
                        b["meta_source"] = f"s3://{B}/{FOREIGN_META}"
                rec = record(work, name, stack, b["mesh_dir"], b["mesh_sha"], y0, x0, 31, b["voxel"], b["meta_path"],
                             b["meta_source"], render_command(VOL_URL + "/", mesh_dir, "OUT", b["voxel"],
                                                              crop_xywh=(x0, y0, WIN, WIN), num_slices=31))
                rec["_scratch"] = str(work / "scratch" / f"{name}_{case}.zarr")
                t1 = time.time()
                rep = gate_array(rec, stack, vol, training={})
                res["rows"].append({"window": name, "case": case, "info": info, "n33_vs_n31_maxabs": ident,
                                    "seconds": round(time.time() - t1, 2), **summ(rep)})
            wi += 1
            out.write_text(json.dumps(res, indent=1, default=float) + "\n")
    if os.environ.get("TRIB_SKIP_RETRACE") != "1":
        res["retrace"] = retrace_study(mesh_root, ids)
    res["seconds"] = round(time.time() - t0, 1)
    out.write_text(json.dumps(res, indent=1, default=float) + "\n")
    print("done", len(res["rows"]), "gate rows", len(res.get("retrace", [])), "retrace rows", res["seconds"], "s")


if __name__ == "__main__":
    main()
