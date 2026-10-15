# Provenance: Project HERCULES | owner the owner | [id removed]
"""FLAT-1 supplementary: flatten each WHOLE levelled 9.362 um mesh (largest
4-connected component of valid quads) with vc_flatten (ABF++), SLIM and
ARAP, and score all quads and the quads of the benchmark rectangle R.
Question answered: how much does distortion grow when the flattening is
not local to R (patch-size effect on the +-5 % metric)? Not part of the
adoption rule.

    PYTHONPATH=src:tools/sib/flat1 /opt/hv/bin/python tools/sib/flat1/flat1_whole.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage


import flat1_run as RUN  # noqa: E402
import flatlib as FL  # noqa: E402


def main() -> None:
    sel = json.loads((RUN.OUT / "selection.json").read_text())
    vox = sel["voxel_um"]
    out = []
    for ch in sel["chosen"]:
        seg = ch["segment"]
        cp = RUN.WORK / "whole" / f"{seg}.json"
        if cp.exists():
            out.append(json.loads(cp.read_text()))
            continue
        lev = np.load(ch["levelled_npy"]).astype(np.float64)
        q = FL.quad_mask(lev)
        lab, n = ndimage.label(q)
        sizes = ndimage.sum(q, lab, index=np.arange(1, n + 1))
        keep = lab == (1 + int(np.argmax(sizes)))
        pts = lev.copy()
        # vertices not used by a kept quad are invalidated so vc_flatten sees the same mesh
        used = np.zeros(lev.shape[:2], bool)
        used[:-1, :-1] |= keep
        used[1:, :-1] |= keep
        used[:-1, 1:] |= keep
        used[1:, 1:] |= keep
        pts[~used] = -1.0
        r = ch["rect"]
        inR = np.zeros_like(q)
        inR[r["r0"]:r["r0"] + r["h_quads"], r["c0"]:r["c0"] + r["w_quads"]] = True
        mesh = FL.grid_to_mesh(pts, keep)
        H, W = pts.shape[:2]
        res = {"segment": seg, "n_components": int(n), "n_quads_total": int(q.sum()), "n_quads_kept": int(keep.sum()),
               "R_inside_kept": bool((keep | ~inR).all()), "area_cm2": float(FL.tri_areas_3d(mesh.V, mesh.F).sum() * (vox * 1e-4) ** 2),
               "methods": {}}
        uvs = {}
        t0 = time.time()
        uv, info = RUN.run_abf(pts, seg + "_whole", vox)
        uvs["vc_flatten"] = (uv, info, time.time() - t0)
        UVg = FL.grid_init_uv(mesh, RUN.STEP_VOX)
        t0 = time.time()
        UV, info = FL.flatten_slim(mesh.V, mesh.F, UVg)
        uvs["slim"] = (FL.uv_to_grid(mesh, UV, (H, W)), info, time.time() - t0)
        t0 = time.time()
        UV, info = FL.flatten_arap(mesh.V, mesh.F, UVg)
        uvs["arap"] = (FL.uv_to_grid(mesh, UV, (H, W)), info, time.time() - t0)
        uvs["grid_baseline"] = (FL.uv_to_grid(mesh, UVg, (H, W)), {}, 0.0)
        for k, (uv, info, sec) in uvs.items():
            info = {kk: vv for kk, vv in info.items() if kk != "energy_history"} | {"seconds": sec}
            res["methods"][k] = {"all": FL.evaluate(pts, uv, keep), "R": FL.evaluate(pts, uv, inR & keep), "info": info}
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps(res, indent=1, default=float))
        out.append(res)
        print(seg, res["n_quads_kept"], {k: (round(v["all"]["pct_quads_within_5pct"], 2), round(v["R"]["pct_quads_within_5pct"], 2),
                                             v["all"]["flipped_triangles"]) for k, v in res["methods"].items()}, flush=True)
    (RUN.OUT / "flat1_whole.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
