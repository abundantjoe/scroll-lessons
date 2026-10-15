"""Command-line interface: ``inkeval <command> ...`` (also ``python -m inkeval``).

Commands
  judge      pixel AUC, stroke AUC and local stroke test L of one score map against a label
  ensemble   rank-mean ensemble of several score maps
  bootstrap  crop-level bootstrap CI of a per-crop metric column in a CSV
  null       cross-crop label-swap negative control over several crops
  export     8-bit PNG + JSON sidecar of a prediction in segment coordinates
  demo       run judge and the label-swap null on the bundled real example (two held-out Scroll 1 crops)
"""
from __future__ import annotations

import argparse
import csv
import json
import sys

import numpy as np

from . import __version__
from .ensemble import rank_mean
from .io import export_png, load_map
from .metrics import judge, judge_classes
from .stats import bootstrap_ci, label_swap_null


def _bool(path):
    a = load_map(path)
    return a > 0 if a.dtype != bool else a


def cmd_judge(a):
    score = load_map(a.score).astype(np.float32); label = _bool(a.label); mask = _bool(a.mask)
    if not (score.shape == label.shape == mask.shape):
        sys.exit(f"shape mismatch: score {score.shape}, label {label.shape}, mask {mask.shape}")
    r = judge(score, label, mask, a.pitch_um)
    r["score"] = a.score
    print(json.dumps(r, indent=1))
    undefined = [k for k in ("pixel_auc", "stroke_auc", "local_L") if r[k] is None]
    if undefined:
        print(f"warning: {', '.join(undefined)} undefined (text {r['text_px']} px, blank {r['blank_px']} px after the judge's margins; "
              f"stroke disks ink {r['stroke_disks']['ink']}, blank {r['stroke_disks']['blank']}); check that --pitch-um "
              f"({a.pitch_um}) is the maps' pixel pitch in um and that the mask covers both text and blank papyrus", file=sys.stderr)


def cmd_ensemble(a):
    mask = _bool(a.mask)
    out = rank_mean([load_map(p) for p in a.scores], mask, a.sigma_mm, a.pitch_um)
    np.save(a.out, out)
    print(f"wrote {a.out} (rank-mean of {len(a.scores)} maps, sigma {a.sigma_mm} mm)")


def cmd_bootstrap(a):
    with open(a.csv) as f:
        rd = csv.DictReader(f)
        if a.column not in (rd.fieldnames or []):
            sys.exit(f"column {a.column!r} not in {a.csv}; columns: {', '.join(rd.fieldnames or [])}")
        vals = [float(row[a.column]) for row in rd if row.get(a.column) not in (None, "")]
    if not vals:
        sys.exit(f"column {a.column!r} in {a.csv} has no values")
    print(json.dumps(bootstrap_ci(vals, a.resamples, a.seed), indent=1))


def cmd_null(a):
    if not (len(a.scores) == len(a.labels) == len(a.masks)):
        sys.exit("give the same number of --scores, --labels and --masks")
    scores = [load_map(p).astype(np.float32) for p in a.scores]
    masks = [_bool(p) for p in a.masks]; labels = [_bool(p) for p in a.labels]
    shapes = sorted({x.shape for x in (*scores, *labels, *masks)})
    if len(shapes) != 1:
        sys.exit(f"all scores, labels and masks must have the same shape; got {shapes}")
    cls = [judge_classes(l, m, a.pitch_um) for l, m in zip(labels, masks)]
    try:
        r = label_swap_null(scores, [c[0] for c in cls], [c[1] for c in cls], masks)
    except ValueError as e:
        sys.exit(str(e).replace("pitch_um", "--pitch-um"))
    print(json.dumps(r, indent=1))


def cmd_export(a):
    side = export_png(load_map(a.score), _bool(a.mask), a.out, segment=a.segment, y0=a.y0, x0=a.x0, pitch_um=a.pitch_um,
                      method=a.method)
    print(json.dumps(side, indent=1))


def cmd_demo(a):
    from .example import run_demo
    run_demo(verbose=True)


def main(argv=None):
    p = argparse.ArgumentParser(prog="inkeval", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"inkeval {__version__}")
    sp = p.add_subparsers(dest="cmd", required=True)

    j = sp.add_parser("judge", help="pixel AUC, stroke AUC and L of one score map")
    j.add_argument("--score", required=True, help="score map (.npy, file.npz:key, .png, .tif); higher means more ink-like")
    j.add_argument("--label", required=True, help="hand label, same shape as the score; > 0 is ink")
    j.add_argument("--mask", required=True, help="judge mask, same shape as the score; > 0 is judged")
    j.add_argument("--pitch-um", type=float, default=2.4,
                   help="pixel pitch of the maps in um; converts the judge's mm distances to pixels and must match the data "
                        "(default: %(default)s)")
    j.set_defaults(fn=cmd_judge)

    e = sp.add_parser("ensemble", help="rank-mean ensemble")
    e.add_argument("--scores", nargs="+", required=True, help="score maps to combine, all of the same shape")
    e.add_argument("--mask", required=True, help="mask, same shape; ranks and smoothing are taken inside it (> 0)")
    e.add_argument("--sigma-mm", type=float, default=0.08, help="Gaussian smoothing sigma in mm (default: %(default)s)")
    e.add_argument("--pitch-um", type=float, default=2.4,
                   help="pixel pitch of the maps in um; converts --sigma-mm to pixels and must match the data (default: %(default)s)")
    e.add_argument("-o", "--out", required=True, help="output .npy file (float16, 0 outside the mask)"); e.set_defaults(fn=cmd_ensemble)

    b = sp.add_parser("bootstrap", help="crop-level bootstrap CI of a CSV column")
    b.add_argument("csv", help="CSV file with one row per crop")
    b.add_argument("--column", required=True, help="column to average over crops (empty cells are skipped)")
    b.add_argument("--resamples", type=int, default=10000, help="bootstrap resamples (default: %(default)s)")
    b.add_argument("--seed", type=int, default=0, help="random seed (default: %(default)s)"); b.set_defaults(fn=cmd_bootstrap)

    n = sp.add_parser("null", help="cross-crop label-swap negative control")
    n.add_argument("--scores", nargs="+", required=True, help="one score map per crop, all of the same shape")
    n.add_argument("--labels", nargs="+", required=True, help="one hand label per crop, in the same order; > 0 is ink")
    n.add_argument("--masks", nargs="+", required=True, help="one judge mask per crop, in the same order; > 0 is judged")
    n.add_argument("--pitch-um", type=float, default=2.4,
                   help="pixel pitch of the maps in um; converts the judge's mm distances to pixels and must match the data "
                        "(default: %(default)s)")
    n.set_defaults(fn=cmd_null)

    x = sp.add_parser("export", help="8-bit PNG + JSON sidecar in segment coordinates")
    x.add_argument("--score", required=True, help="score map to export (.npy, file.npz:key, .png, .tif)")
    x.add_argument("--mask", required=True, help="mask, same shape; pixels outside it are written as 0 (> 0 is judged)")
    x.add_argument("-o", "--out", required=True, help="output .png; the JSON sidecar is written next to it with the same stem")
    x.add_argument("--segment", help="segment ID, recorded in the sidecar")
    x.add_argument("--y0", type=int, default=0, help="row of the map's top-left pixel in the segment canvas (default: %(default)s)")
    x.add_argument("--x0", type=int, default=0, help="column of the map's top-left pixel in the segment canvas (default: %(default)s)")
    x.add_argument("--pitch-um", type=float, default=2.4, help="pixel pitch of the map in um, recorded in the sidecar (default: %(default)s)")
    x.add_argument("--method", default="", help="method name, recorded in the sidecar"); x.set_defaults(fn=cmd_export)

    d = sp.add_parser("demo", help="run on the bundled real example"); d.set_defaults(fn=cmd_demo)

    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
