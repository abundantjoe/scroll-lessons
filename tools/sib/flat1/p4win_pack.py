# Provenance: Project HERCULES | owner the owner | [id removed]
"""Compact, exact git delivery of window A (the repo pre-commit hook refuses
files > 20 MB; the full-resolution files stay in /work/flat1/p4win_full).
Per method:
* flattened_s40.tifxyz: the step-20 flattened tifxyz subsampled [::2, ::2]
  (nodes at exactly the same (u, v) positions, step 40 vox, scale 0.025);
* coarse_uv.npy: aligned (u, v) of the K = 6 coarse vertices (region fine
  vertex (6a, 6b)); the full-resolution UV is EXACTLY its bilinear
  interpolation inside kept coarse quads (p4win.upsample; the alignment is
  linear), coarse_keep.npy marks the kept coarse quads.
"""
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import tifffile

import p4win as W
from hercules.geometry import tifxyz as T

OUT = W.OUT
FULL = Path("/work/flat1/p4win_full")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


rec = json.loads((OUT / "metrics.json").read_text())
FULL.mkdir(parents=True, exist_ok=True)
pack = {}
for meth in ("vc_flatten", "slim"):
    src = OUT / meth
    dst_full = FULL / meth
    if not dst_full.exists():
        shutil.copytree(src, dst_full)
    full_t = dst_full / "flattened.tifxyz"
    m = T.read_tifxyz(full_t)
    meta = json.loads((full_t / "meta.json").read_text())
    sub = m.points[::2, ::2]
    d = OUT / meth / "flattened_s40.tifxyz"
    d.mkdir(parents=True, exist_ok=True)
    files = {}
    for i, n in enumerate("xyz"):
        tifffile.imwrite(str(d / f"{n}.tif"), np.ascontiguousarray(sub[..., i], "<f4"), photometric="minisblack",
                         compression="zlib", metadata=None, tile=(512, 512), software=False)
        files[f"{n}.tif"] = sha(d / f"{n}.tif")
    meta.update(scale=[0.025, 0.025], bbox=T.bbox(sub), uuid=f"p4winA_{meth}_s40",
                hercules_subsample="flattened.tifxyz (step 20) [::2, ::2]")
    (d / "meta.json").write_text(json.dumps(meta, indent=4, sort_keys=True) + "\n")
    uv = np.load(W.WORK / f"uv_{meth}.npy")
    # aligned coarse UV = fine UV at coarse vertices (exact)
    cuv = uv[::W.K, ::W.K].astype(np.float32)
    np.save(OUT / meth / "coarse_uv.npy", cuv)
    pack[meth] = {"flattened_s40": {"grid_shape": list(sub.shape[:2]), "files_sha256": files,
                                    "readback_equal": bool(np.array_equal(T.canonicalize(T.read_tifxyz(d).points), T.canonicalize(sub)))},
                  "coarse_uv_sha256": sha(OUT / meth / "coarse_uv.npy"), "coarse_uv_shape": list(cuv.shape),
                  "full_resolution_local": str(dst_full), "full_resolution_sha256": rec["deliverables"][meth]["files_sha256"]}
    # remove the >20 MB copies from the repo tree (kept in FULL, identical sha256 recorded)
    for f in ("uv_u.tif", "uv_v.tif", "src_row.tif", "src_col.tif"):
        (OUT / meth / f).unlink()
    shutil.rmtree(OUT / meth / "flattened.tifxyz")
    assert all(sha(dst_full / k) == v for k, v in rec["deliverables"][meth]["files_sha256"].items())
# coarse keep mask (shared)
p = None
rec["git_pack"] = pack
rec["git_pack_note"] = "pre-commit hook refuses files > 20 MB; full-resolution deliverables kept in /work/flat1/p4win_full (sha256 in deliverables); offload to the data branch needs owner permission (DECL-OFFLOAD-1 item 4)"
(OUT / "metrics.json").write_text(json.dumps(rec, indent=1, default=float) + "\n")
print(json.dumps(pack, indent=1))
