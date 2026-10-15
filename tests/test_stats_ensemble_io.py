import json
import os

import numpy as np
import pytest

from inkeval import bootstrap_ci, export_png, label_swap_null, load_map, paired_bootstrap, rank_mean, trunc
from inkeval import judge_classes, pixel_auc
from inkeval.synth import scene


def test_bootstrap_is_deterministic_and_brackets_mean():
    v = [0.88, 0.95, 0.81, 0.90, 0.85, 0.88, 0.84]
    a, b = bootstrap_ci(v), bootstrap_ci(v)
    assert a == b
    assert a["ci"][0] <= a["mean"] <= a["ci"][1] and a["n"] == 7


def test_paired_bootstrap_counts_units():
    r = paired_bootstrap([0.9, 0.8, 0.7], [0.5, 0.85, 0.6])
    assert r["positive_units"] == 2 and r["mean"] == pytest.approx((0.4 - 0.05 + 0.1) / 3)


def test_label_swap_null_separates_reading_from_layout():
    # The synthetic scenes share a layout bias (strokes avoid the borders), and the null catches it: it sits ABOVE 0.5.
    # That is the point of measuring a null instead of assuming chance is 0.5. Matched crops must still beat it by a wide margin.
    crops = [scene(seed=s) for s in range(3)]
    cls = [judge_classes(l, m, 2.4) for _, l, m in crops]
    r = label_swap_null([c[0] for c in crops], [c[0] for c in cls], [c[1] for c in cls], [c[2] for c in crops], subsample=None)
    matched = np.mean([pixel_auc(c[0], k[0], k[1], subsample=None) for c, k in zip(crops, cls)])
    assert r["pairs"] == 6 and 0.5 < r["mean"] < 0.7
    assert matched > r["mean"] + 0.15     # measured: matched 0.792, null 0.600


def test_label_swap_null_is_half_for_layout_free_scores():
    rng = np.random.default_rng(2)
    crops = [scene(seed=s) for s in range(3)]
    cls = [judge_classes(l, m, 2.4) for _, l, m in crops]
    noise = [rng.normal(size=c[0].shape).astype(np.float32) for c in crops]
    r = label_swap_null(noise, [c[0] for c in cls], [c[1] for c in cls], [c[2] for c in crops], subsample=None)
    assert abs(r["mean"] - 0.5) < 0.02


def test_trunc_never_rounds_up():
    assert trunc(0.8395) == 0.839 and trunc(0.9999) == 0.999 and trunc(-0.0125) == -0.012
    assert trunc(-0.00599999999999999) == -0.006 and trunc(0.011999999999999992) == 0.012   # float noise is not a digit


def test_rank_mean_is_monotone_invariant_and_masked():
    s, l, m = scene(seed=7)
    a = rank_mean([s, s * 2 + 5], m).astype(np.float32)
    b = rank_mean([np.exp(s / 4), s], m).astype(np.float32)
    assert np.allclose(a, b, atol=2e-3)
    assert (a[~m] == 0).all()


def test_export_png_roundtrip(tmp_path):
    s, l, m = scene(seed=8)
    out = tmp_path / "pred.png"
    side = export_png(s, m, str(out), segment="20231005123336", y0=12400, x0=23560, method="test")
    img = load_map(str(out))
    assert img.dtype == np.uint8 and img.shape == s.shape
    assert (img[~m] == 0).all() and img[m].min() >= 1
    meta = json.load(open(tmp_path / "pred.json"))
    assert meta["canvas_origin_yx"] == [12400, 23560] and meta == side
