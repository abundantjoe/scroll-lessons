"""flatcheck command line.

  flatcheck report  <tifxyz> [--tile N] [--tol 0.05] [--json out.json]
      score a tifxyz as a flattening (edges vs nominal step, fold-overs, tiles)
  flatcheck flatten <tifxyz> --out DIR [--method slim|arap|vc_flatten ...]
                    [--rect R0 C0 H W | --rect4cm2 VOXEL_UM [--seed S]] [--level]
      re-flatten (a crop of) the mesh, score every method (quads within +-5 %,
      fold/flip counts, area and angle distortion, collapse flags) and write a
      verifiable flat package per method
  flatcheck verify  <package_dir>
      recompute the metric from a package; exit 1 unless it matches exactly
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from . import api, core, level, report, tifxyz


def _dump(obj, path=None):
    txt = json.dumps(obj, indent=1, default=float)
    if path:
        Path(path).write_text(txt + "\n")
    print(txt if len(txt) < 20000 else txt[:20000] + "\n...")


def cmd_report(a) -> int:
    t = tifxyz.read(a.tifxyz)
    r = report.grid_report(t.points, t.step_vox[0], tol=a.tol, tile=a.tile, bar=a.bar)
    r["source"] = str(a.tifxyz)
    _dump(r, a.json)
    return 0


def cmd_flatten(a) -> int:
    t = tifxyz.read(a.tifxyz)
    p, step = t.points, t.step_vox[0]
    info = {"source": str(a.tifxyz), "step_vox": step}
    if a.level:
        L = level.level_mesh(p, step_vox=step)
        p = L.points
        info["level"] = {"angle_deg": L.angle_deg, "spread_deg": L.spread_deg, "grid_shape": list(p.shape[:2])}
    if a.rect4cm2:
        rect = core.choose_rectangle(p, a.rect4cm2, step, np.random.default_rng(a.seed))
        if rect is None:
            print("no fully valid 4 cm^2 rectangle", file=sys.stderr)
            return 2
        info["rect"] = rect
        r0, c0, h, w = rect["r0"], rect["c0"], rect["h_quads"], rect["w_quads"]
        p = p[r0:r0 + h + 1, c0:c0 + w + 1]
    elif a.rect:
        r0, c0, h, w = a.rect
        info["rect"] = {"r0": r0, "c0": c0, "h_quads": h, "w_quads": w}
        p = p[r0:r0 + h + 1, c0:c0 + w + 1]
    out = Path(a.out)
    res = {"input": info, "grid_as_is": api.metrics(p, core.uv_to_grid(
        m := core.grid_to_mesh(p), core.grid_init_uv(m, step), p.shape[:2])), "methods": {}}
    for meth in a.method:
        fr = api.flatten(p, meth, step=step)
        rec = api.write_package(out / meth, p, fr.uv, method=meth, step=step, info=fr.info, source=str(a.tifxyz))
        ok, _ = api.verify_package(out / meth)
        res["methods"][meth] = {"metrics": rec["metrics"], "collapse": rec["collapse"], "seconds": fr.seconds,
                                "package_verified": ok}
    out.mkdir(parents=True, exist_ok=True)
    summary = {k: {"pct_quads_within_5pct": v["metrics"]["pct_quads_within_5pct"],
                   "flipped_triangles": v["metrics"]["flipped_triangles"], "collapsed": v["collapse"]["collapsed"]}
               for k, v in res["methods"].items()}
    summary["grid_as_is"] = {"pct_quads_within_5pct": res["grid_as_is"]["pct_quads_within_5pct"]}
    res["summary"] = summary
    _dump(summary)
    (out / "flatcheck_result.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    return 0


def cmd_verify(a) -> int:
    ok, rep = api.verify_package(a.package)
    _dump({"ok": ok, **rep})
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="flatcheck", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("report")
    r.add_argument("tifxyz")
    r.add_argument("--tile", type=int, default=None, help="tile side in grid cells")
    r.add_argument("--tol", type=float, default=0.05)
    r.add_argument("--bar", type=float, default=93.1)
    r.add_argument("--json")
    f = sp.add_parser("flatten")
    f.add_argument("tifxyz")
    f.add_argument("--out", required=True)
    f.add_argument("--method", nargs="+", default=["slim", "arap"], choices=list(api.METHODS))
    g = f.add_mutually_exclusive_group()
    g.add_argument("--rect", nargs=4, type=int, metavar=("R0", "C0", "H", "W"))
    g.add_argument("--rect4cm2", type=float, metavar="VOXEL_UM", help="seeded 4.00 cm^2 rectangle (voxel size in um)")
    f.add_argument("--seed", type=int, default=0)
    f.add_argument("--level", action="store_true", help="level the grid first (iso-z along rows)")
    v = sp.add_parser("verify")
    v.add_argument("package")
    a = ap.parse_args(argv)
    return {"report": cmd_report, "flatten": cmd_flatten, "verify": cmd_verify}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
