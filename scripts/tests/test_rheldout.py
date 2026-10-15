"""Tests for scripts/rheldout.py (RULES.md R-HELDOUT), written before any held-out output existed.
Synthetic segment at 9.612 um/px: unit side 736, a 3 x 3 grid of full units; text (labelled ink in a stroke
pattern, forward 0.45 / reverse 0.30) fills unit rows 0-1, unit row 2 is supervised blank papyrus (0.30 / 0.30)."""
import os, sys
import numpy as np, pytest, tifffile, zarr

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import rheldout as H  # noqa: E402

S = 736
N = 3 * S


def make_segment(d, blind=False, label_shape=(N, N)):
    rng = np.random.default_rng(0)
    os.makedirs(d, exist_ok=True)
    ct = np.full((21, N, N), 90, np.uint8)
    g = zarr.open_group(os.path.join(d, "pooled.zarr"), mode="w")
    g.create_array("0", data=ct, chunks=(21, 256, 256))
    ink = np.zeros((N, N), np.uint8)
    ink[: 2 * S, :][(np.arange(2 * S) % 40 < 6)[:, None] & (np.arange(N) % 30 < 20)[None, :]] = 255   # strokes, phi ~0.1
    fwd = np.where(ink > 0, 0.75, 0.40) if not blind else np.full((N, N), 0.32)
    fwd = np.clip(fwd + rng.normal(0, 0.02, (N, N)), 0, 1); fwd[2 * S:] = 0.30 + rng.normal(0, 0.02, (S, N))
    rev = np.clip(0.30 + rng.normal(0, 0.02, (N, N)), 0, 1)
    if blind:
        rev = fwd.copy()
    tifffile.imwrite(os.path.join(d, "pred.tif"), np.round(fwd * 255).astype(np.uint8))
    tifffile.imwrite(os.path.join(d, "pred_reverse.tif"), np.round(rev * 255).astype(np.uint8))
    for name, arr in (("inklabels.zarr", ink), ("supervision.zarr", np.ones((N, N), np.uint8))):
        lg = zarr.open_group(os.path.join(d, "labels", name), mode="w")
        a = arr if label_shape == (N, N) else np.zeros(label_shape, np.uint8)
        lg.create_array("2", data=a, chunks=(512, 512))
    return d


def test_text_units_flag_blank_units_do_not_and_the_verdict_is_strong(tmp_path):
    d = make_segment(str(tmp_path / "seg"))
    s, _ = H.segment_result(d)
    assert s["n_valid"] == 9 and s["auc_forward"] > 0.95 and s["auc_reverse"] < 0.6
    assert s["text_units"]["n"] == 6 and s["text_units"]["flagged"] == 6
    assert s["blank_units"]["n"] == 3 and s["blank_units"]["flagged"] == 0
    assert s["largest_cluster"] == 6 and s["swapped_n_flagged"] == 0
    assert H.verdicts([s], s["auc_forward"], s["auc_reverse"]) == ("TRANSFERS", "STRONG")


def test_a_detector_with_no_depth_asymmetry_is_blind(tmp_path):
    d = make_segment(str(tmp_path / "seg"), blind=True)
    s, _ = H.segment_result(d)
    assert s["n_flagged"] == 0
    assert H.verdicts([s], 0.55, 0.55) == ("NO TRANSFER", "BLIND")


def test_partial_band_and_pass_without_cluster():
    seg = dict(largest_cluster=1, n_flagged=1)
    assert H.verdicts([seg], 0.70, 0.50) == ("PARTIAL", "PASS")
    assert H.verdicts([seg], 0.80, 0.65) == ("PARTIAL", "PASS")          # forward high but reverse too: not TRANSFERS


def test_labels_on_a_different_canvas_are_refused(tmp_path):
    d = make_segment(str(tmp_path / "seg"), label_shape=(N, N + 4))
    with pytest.raises(SystemExit):
        H.segment_result(d)


def test_cli_writes_pooled_numbers_and_both_verdicts(tmp_path, capsys):
    import json
    a = make_segment(str(tmp_path / "a")); b = make_segment(str(tmp_path / "b"), blind=True)
    out = tmp_path / "r.json"
    assert H.main([a, b, "--json", str(out)]) == 0
    j = json.load(open(out))
    assert j["pooled"]["n_valid"] == 18 and j["pooled"]["n_flagged"] == 6
    assert j["HELDOUT_RULE"] == "STRONG" and j["pooled"]["text_units"]["n"] == 12
    assert "HELDOUT-AUC" in capsys.readouterr().out
