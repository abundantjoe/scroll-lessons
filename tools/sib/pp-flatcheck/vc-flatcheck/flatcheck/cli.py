"""Command line interface: ``flatcheck report``, ``flatcheck flatten`` and ``flatcheck scan``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from . import api, geometry as G, tifxyz as T


def _slice(s: str | None) -> slice:
    if not s:
        return slice(None)
    a, b = s.split(":")
    return slice(int(a) if a else None, int(b) if b else None)


def _load(args) -> tuple[np.ndarray, float, tuple[slice, slice]]:
    pts, meta = T.read_tifxyz(args.mesh)
    win = (_slice(args.rows), _slice(args.cols))
    step = args.step or T.step_from_meta(meta) or api.nominal_step(pts)
    return pts, step, win


def _summary(name: str, r: dict) -> str:
    m, c = r["metrics"], r["collapse"]
    return (f"{name:>10}: {r['pct_quads_within_5pct']:6.2f} % quads within +-5 % "
            f"(raw {m['pct_quads_within_5pct_raw']:6.2f}, +-1 % {m['pct_quads_within_1pct']:6.2f}) | "
            f"folds {r['fold_overs']} | |log area| {m['area_ratio']['weighted_mean_abs_log']:.4f} | "
            f"angle err mean {m['angle_abs_err_deg']['mean']:.3f} deg | "
            f"{'COLLAPSE ' if c['collapsed'] else ''}{'PASS' if r['passes_bar'] else 'FAIL'} (bar {r['bar_pct']} %)")


def cmd_report(args) -> int:
    pts, step, win = _load(args)
    p = pts[win]
    results = {}
    if args.uv:
        uv = T.read_uv(*args.uv)[win]
        results["given_uv"] = api.report(p, uv, rescale_factor=args.rescale, bar=args.bar)
    methods = ["grid", *api.METHODS] if args.compare else ([] if args.uv else ["grid"])
    if args.flatten and args.flatten not in methods:
        methods.append(args.flatten)
    for name in methods:
        uv = G.grid_uv(p, step) if name == "grid" else api.flatten(p, name, step=step)[0]
        results[name] = api.report(p, uv, bar=args.bar)
    out = {"mesh": str(args.mesh), "window": {"rows": args.rows, "cols": args.cols},
           "grid_shape": list(p.shape[:2]), "step_vox": step,
           "curvature": next(iter(results.values()))["curvature"], "results": results}
    for name, r in results.items():
        print(_summary(name, r))
    k = out["curvature"]
    print(f"curvature: mean |angle defect| {k['mean_abs_angle_defect_deg']:.3f} deg, "
          f"sum {k['sum_angle_defect_rad']:.4f} rad over {k['n_interior_vertices']} interior vertices")
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=1, default=float) + "\n")
    bad = any(r["collapse"]["collapsed"] or not r["passes_bar"] for r in results.values())
    return 1 if (args.strict and bad) else 0


def cmd_flatten(args) -> int:
    pts, step, win = _load(args)
    p = pts[win]
    uv, info = api.flatten(p, args.method, step=step)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    T.write_uv(out / "u.tif", out / "v.tif", uv)
    r = api.report(p, uv, bar=args.bar)
    (out / "report.json").write_text(json.dumps({"info": info, "report": r}, indent=1, default=float) + "\n")
    print(_summary(args.method, r))
    return 0


def cmd_scan(args) -> int:
    pts, step, win = _load(args)
    p = pts[win]
    if args.window:
        h, w = args.window
    else:
        side_quads = (args.area_cm2 ** 0.5) / (step * args.voxel_um * 1e-4)
        h = int(round(side_quads / args.aspect ** 0.5))
        w = int(round(h * args.aspect))
    wins = G.worst_windows(p, h, w, args.k)
    methods = [m for m in ("grid", *api.METHODS) if m in args.methods.split(",")]
    for x in wins:
        q = p[x["r0"]:x["r0"] + h + 1, x["c0"]:x["c0"] + w + 1]
        x["rows"] = f"{x['r0']}:{x['r0'] + h + 1}"
        x["cols"] = f"{x['c0']}:{x['c0'] + w + 1}"
        k = G.angle_defects(q)
        if args.voxel_um:
            x["area_cm2"] = k["area_vox2"] * (args.voxel_um * 1e-4) ** 2
        x["results"] = {}
        for name in methods:
            uv = G.grid_uv(q, step) if name == "grid" else api.flatten(q, name, step=step)[0]
            r = api.report(q, uv, bar=args.bar)
            x["results"][name] = {"pct_quads_within_5pct": r["pct_quads_within_5pct"], "fold_overs": r["fold_overs"],
                                  "collapsed": r["collapse"]["collapsed"], "passes_bar": r["passes_bar"]}
        print(f"rows {x['rows']:>11} cols {x['cols']:>11} | mean |defect| {x['mean_abs_angle_defect_deg']:.3f} deg | "
              + " | ".join(f"{n} {v['pct_quads_within_5pct']:6.2f} % f{v['fold_overs']}" for n, v in x["results"].items()))
    if args.json:
        Path(args.json).write_text(json.dumps({"mesh": str(args.mesh), "step_vox": step, "voxel_um": args.voxel_um,
                                               "window_quads": [h, w], "bar_pct": args.bar, "windows": wins},
                                              indent=1, default=float) + "\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="flatcheck", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("report", "flatten", "scan"):
        s = sub.add_parser(name)
        s.add_argument("mesh", help="tifxyz directory (x.tif, y.tif, z.tif, meta.json)")
        s.add_argument("--rows", help="row window a:b (grid vertices)")
        s.add_argument("--cols", help="column window a:b (grid vertices)")
        s.add_argument("--step", type=float, help="nominal grid step in voxels (default: 1/meta scale)")
        s.add_argument("--bar", type=float, default=93.1, help="pass bar, %% of quads within +-5 %%")
    r = sub.choices["report"]
    r.add_argument("--uv", nargs=2, metavar=("U_TIF", "V_TIF"), help="score an existing flattening (e.g. vc_flatten)")
    r.add_argument("--rescale", type=float, help="global rescale factor the flattener applied (collapse check)")
    r.add_argument("--flatten", choices=api.METHODS, help="also re-flatten with this method and score it")
    r.add_argument("--compare", action="store_true", help="score grid, SLIM and ARAP")
    r.add_argument("--json", help="write the full report as JSON")
    r.add_argument("--strict", action="store_true", help="exit 1 on any FAIL or collapse")
    f = sub.choices["flatten"]
    f.add_argument("--method", choices=api.METHODS, default="slim")
    f.add_argument("--out", required=True, help="output directory (u.tif, v.tif, report.json)")
    sc = sub.choices["scan"]
    sc.add_argument("--window", nargs=2, type=int, metavar=("H", "W"), help="window size in quads")
    sc.add_argument("--area-cm2", type=float, default=4.0, help="window area if --window is not given (needs --voxel-um)")
    sc.add_argument("--aspect", type=float, default=1.5, help="window width / height")
    sc.add_argument("--voxel-um", type=float, help="voxel size in um (from the volume metadata)")
    sc.add_argument("-k", type=int, default=5, help="number of non-overlapping windows")
    sc.add_argument("--methods", default="grid,slim,arap", help="comma list of grid, slim, arap to score per window")
    sc.add_argument("--json", help="write the windows and scores as JSON")
    args = ap.parse_args(argv)
    if args.cmd == "scan" and not args.window and not args.voxel_um:
        ap.error("scan needs --window H W or --voxel-um")
    return {"report": cmd_report, "flatten": cmd_flatten, "scan": cmd_scan}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
