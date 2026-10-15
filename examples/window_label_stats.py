#!/usr/bin/env python
"""window_label_stats.py -- label statistics of the quick-start window, from the public w040 labels.

The quick start ships the window's two prediction maps and its CT slice, not the labels. This script computes, from the
public w040 labels (fetched by scripts/reproduce_control.sh step 1 or docs/REPRODUCE.md), the label numbers the
documentation quotes for the window: the fraction of its pixels that are supervised, the fraction labelled ink,
and the labelled ink fraction phi of each 0.5 cm2 unit of the quick-start read. It reads labels exactly as scripts/score_auc.py does (slice 14, ink > 128).
usage: window_label_stats.py <w040_inklabels.zarr> <w040_supervision_mask.zarr>
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from score_auc import read_label_slice  # noqa: E402

Y0, Y1, X0, X1 = 1500, 3636, 2000, 4136   # the quick-start window, canvas rows/columns (examples/README.md)
SLICE, INK_THR = 14, 128                  # as Gate A (scripts/reproduce_control.sh step 3)
SIDE_05 = 755                             # 0.5 cm2 unit side at 9.362 um/px (rule 5.5)


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    if len(a) != 2:
        raise SystemExit(__doc__)
    lab = read_label_slice(a[0], SLICE)[Y0:Y1, X0:X1]
    sup = read_label_slice(a[1], SLICE)[Y0:Y1, X0:X1] > 0
    ink = lab > INK_THR
    n = lab.size
    print("window %d x %d px (rows %d-%d, cols %d-%d), slice %d, ink > %d" % (Y1 - Y0, X1 - X0, Y0, Y1 - 1, X0, X1 - 1, SLICE, INK_THR))
    print("supervised: %d px = %.6f %% of the window" % (sup.sum(), 100.0 * sup.sum() / n))
    print("labelled ink: %d px = %.6f %% of the window (%.6f %% of supervised px)" % (ink.sum(), 100.0 * ink.sum() / n, 100.0 * ink.sum() / max(sup.sum(), 1)))
    print("ink outside the supervision mask: %d px" % int((ink & ~sup).sum()))
    # labelled ink fraction phi per 0.5 cm2 unit, on the quick-start read's grid (origin (0, 0), side 755 px at
    # 9.362 um/px: examples/out/read/read_stats.json, rule55.units.0.5cm2): phi = mean of (label > 128) over the unit
    for r in range(len(lab) // SIDE_05):
        for c in range(len(lab[0]) // SIDE_05):
            u = ink[r * SIDE_05:(r + 1) * SIDE_05, c * SIDE_05:(c + 1) * SIDE_05]
            print("unit (%d,%d) phi %.6f (%d / %d px)" % (r, c, u.mean(), u.sum(), u.size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
