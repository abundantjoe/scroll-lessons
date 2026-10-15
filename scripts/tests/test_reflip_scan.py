"""Tests for scripts/reflip_scan.py (RULES R-FLIP applied retrospectively).
Run: python -m pytest scripts/tests/test_reflip_scan.py -q
"""
import json, os, sys
import numpy as np, tifffile
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import reflip_scan as rf  # noqa: E402
import rule55  # noqa: E402

UM = 9.362


def make_read(root, key, fwd, rev, onsheet):
    d = os.path.join(root, "PHerc0826", "auto_grown_x", "read_tag")
    os.makedirs(d, exist_ok=True)
    tifffile.imwrite(os.path.join(d, "m.tif"), np.clip(fwd * 255, 0, 255).astype(np.uint8))
    tifffile.imwrite(os.path.join(d, "m_reverse.tif"), np.clip(rev * 255, 0, 255).astype(np.uint8))
    Image.fromarray((onsheet * 255).astype(np.uint8)).save(os.path.join(d, "onsheet_mask.png"))
    sp = os.path.join(d, "read_stats.json")
    json.dump(dict(key=key, um_per_px=UM, verdict="BLANK", rule55=dict(unit_origin="fixed")), open(sp, "w"))
    return sp


def test_mirrored_read_fires_the_tripwire_without_touching_the_verdict(tmp_path):
    side = rule55.unit_side(UM)
    n = side * 2
    fwd = np.full((n, n), 0.30, np.float32)
    rev = np.full((n, n), 0.30, np.float32)
    rev[:side, :side] = 0.50; fwd[:side, :side] = 0.20        # all the signal in the map labelled 'reverse'
    sp = make_read(str(tmp_path), "PHerc0826|auto_grown_x|0|t|both", fwd, rev, np.ones((n, n), bool))
    assert rf.main(["--patches", str(tmp_path)]) == 0
    s = json.load(open(sp))
    assert s["depth_swap_tripwire"] is True
    assert s["rule55_depth_swapped"]["0.5cm2"]["n_flagged"] == 1
    assert s["verdict"] == "BLANK"                            # the ledger verdict is the signed rule, untouched
    assert rf.main(["--patches", str(tmp_path)]) == 0         # idempotent: a second pass skips it
    assert json.load(open(sp))["rule55_depth_swapped"]["0.5cm2"]["n_flagged"] == 1


def test_a_read_with_no_mirrored_signal_does_not_fire(tmp_path):
    side = rule55.unit_side(UM)
    n = side * 2
    fwd = np.full((n, n), 0.30, np.float32)
    rev = np.full((n, n), 0.30, np.float32)
    fwd[:side, :side] = 0.50; rev[:side, :side] = 0.20        # an ordinary forward detection
    sp = make_read(str(tmp_path), "PHerc0826|auto_grown_x|0|t|both", fwd, rev, np.ones((n, n), bool))
    rf.main(["--patches", str(tmp_path)])
    assert json.load(open(sp))["depth_swap_tripwire"] is False


def test_a_read_without_its_mask_is_skipped_not_guessed(tmp_path):
    side = rule55.unit_side(UM)
    n = side * 2
    z = np.full((n, n), 0.30, np.float32)
    sp = make_read(str(tmp_path), "PHerc0826|auto_grown_x|0|t|both", z, z, np.ones((n, n), bool))
    os.remove(os.path.join(os.path.dirname(sp), "onsheet_mask.png"))
    rf.main(["--patches", str(tmp_path)])
    assert "rule55_depth_swapped" not in json.load(open(sp))   # no mask, no invented on-sheet region
