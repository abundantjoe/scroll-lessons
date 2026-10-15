#!/usr/bin/env python
"""check_quickstart.py -- assert that examples/quickstart.sh produced exactly the recorded outputs.

Every expected value below was produced by the committed code on the committed inputs (2026-10-15) and is listed in
examples/README.md. A difference means the code or the inputs changed; it is reported, never silently accepted.
usage: check_quickstart.py <out_dir>
"""
import json, os, sys
import numpy as np, tifffile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import rule55  # noqa: E402

EXPECTED_UNITS = [  # row, col, forward mean, reverse mean, margin, flagged  (0.5 cm^2 units, mask-origin grid)
    (0, 0, 0.3760, 0.3168, 0.0592, False),
    (0, 1, 0.3567, 0.2800, 0.0767, False),
    (1, 0, 0.3827, 0.3009, 0.0818, True),
    (1, 1, 0.3616, 0.3212, 0.0405, False),
]
fails = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


def main(out):
    j = json.load(open(os.path.join(out, "read", "read_stats.json")))
    h = j["rule55"]["units"]["0.5cm2"]
    check(j["verdict"] == "NOT ESTABLISHED", "known-text window verdict NOT ESTABLISHED (got %s)" % j["verdict"])
    check(h["n_valid"] == 4 and h["n_flagged"] == 1, "1 flagged of 4 valid 0.5 cm^2 units (got %d of %d)" % (h["n_flagged"], h["n_valid"]))
    got = [(u["row"], u["col"], u["fwd_mean"], u["rev_mean"], u["margin"], u["flagged"]) for u in h["valid_units"]]
    check(got == EXPECTED_UNITS, "per-unit forward / reverse / margin table matches the record")
    check(all(u[4] > 0 for u in got), "every unit's forward-minus-reverse margin is positive on known text")
    check(j["maps"]["fwd_minus_rev_mean"] == 0.0596, "whole-window margin +0.0596 (got %+.4f)" % j["maps"]["fwd_minus_rev_mean"])
    check(j["depth_swap_tripwire"] is False, "depth-swap tripwire silent on the correctly oriented read")

    s = json.load(open(os.path.join(out, "read_swapped", "read_stats.json")))
    check(s["verdict"] == "BLANK", "orders swapped (a mirrored surface): signed rule says BLANK (got %s)" % s["verdict"])
    check(s["depth_swap_tripwire"] is True, "orders swapped: the depth-swap tripwire FIRES, so the ink is not lost")

    check(not os.path.exists(os.path.join(out, "read_truncated", "read_stats.json")),
          "truncated reverse map: read_chart.py refused it and wrote no verdict")
    f = tifffile.imread(os.path.join(out, "forward.tif")); r = tifffile.imread(os.path.join(out, "reverse_truncated.tif"))
    m = tifffile.imread(os.path.join(out, "ct_mid.tif")) > 0
    res, _ = rule55.evaluate(f, r, m, 9.362, unit_origin="auto")
    margins = [u["margin"] for u in res["units"]["0.5cm2"]["valid_units"]]
    check(max(margins) > 3 * max(u[4] for u in EXPECTED_UNITS),
          "without the guard the same maps would report margins up to %+.4f (true maximum +0.0818)" % max(margins))
    print("\n%d checks failed" % len(fails) if fails else "\nALL CHECKS PASSED")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
