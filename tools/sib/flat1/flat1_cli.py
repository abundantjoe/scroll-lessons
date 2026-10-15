# Provenance: Project HERCULES | owner the owner | [id removed]
"""FLAT-1 supplementary: the official vc_flatten CLI in its default mode
(abfFlattenToNewSurface: a NEW tifxyz whose regular grid is the flat
parameterisation) on each 9.362 um benchmark patch. For such an output the
flat length of every grid edge is the nominal step 1/scale, so the metric is
% of quads whose four 3-D edge lengths lie within +-5 % of 1/scale (raw) or of
the median edge length (normalised). Not part of the adoption rule.

    PYTHONPATH=src:tools/sib/flat1 /opt/hv/bin/python tools/sib/flat1/flat1_cli.py
"""

from __future__ import annotations

import json
import subprocess
import sys

import numpy as np


import flat1_run as RUN  # noqa: E402
import flatlib as FL  # noqa: E402
from hercules.geometry import tifxyz as T  # noqa: E402


def grid_metric(p: np.ndarray, step: float, tol: float = 0.05) -> dict:
    q = FL.quad_mask(p)
    Lh = np.linalg.norm(p[:, 1:] - p[:, :-1], axis=-1)
    Lv = np.linalg.norm(p[1:] - p[:-1], axis=-1)
    out = {"n_quads": int(q.sum()), "nominal_step_vox": step}
    edges = np.concatenate([Lh[:-1][q], Lh[1:][q], Lv[:, :-1][q], Lv[:, 1:][q]])
    med = float(np.median(edges))
    out["median_edge_vox"] = med
    for lab, ref in (("raw", step), ("norm", med)):
        okh = np.abs(Lh / ref - 1) <= tol
        okv = np.abs(Lv / ref - 1) <= tol
        ok = okh[:-1] & okh[1:] & okv[:, :-1] & okv[:, 1:] & q
        out[f"pct_quads_within_5pct_{lab}"] = float(100.0 * ok.sum() / max(q.sum(), 1))
    return out


def main() -> None:
    sel = json.loads((RUN.OUT / "selection.json").read_text())
    rows = []
    for ch in sel["chosen"]:
        seg = ch["segment"]
        src = RUN.WORK / "abf" / seg / "patch.tifxyz"
        dst = RUN.WORK / "cli" / seg / "flat.tifxyz"
        dst.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run([str(RUN.REPO / "tools/sib/flat1/logrun.sh"), f"vc_flatten_cli_{seg}", "/work/bin/vc", "vc_flatten",
                            "-i", str(src), "-o", str(dst)], capture_output=True, text=True)
        row = {"segment": seg, "exit_code": r.returncode, "stdout_tail": r.stdout[-600:]}
        if r.returncode == 0:
            m_in = T.read_tifxyz(src)
            m_out = T.read_tifxyz(dst)
            row["input"] = grid_metric(m_in.points.astype(np.float64), m_in.step_vox[0])
            row["output"] = grid_metric(m_out.points.astype(np.float64), m_out.step_vox[0])
            row["output_scale"] = list(m_out.scale)
            row["output_grid_shape"] = list(m_out.points.shape[:2])
            row["output_area_cm2"] = T.area_cm2(m_out.points, sel["voxel_um"])
            row["input_area_cm2"] = T.area_cm2(m_in.points, sel["voxel_um"])
        rows.append(row)
        print(seg, r.returncode, {k: row.get(k, {}).get("pct_quads_within_5pct_raw") for k in ("input", "output")},
              {k: row.get(k, {}).get("pct_quads_within_5pct_norm") for k in ("input", "output")}, flush=True)
    (RUN.OUT / "flat1_cli.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
