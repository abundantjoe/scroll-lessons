"""Behavioural tests of the metrics on synthetic scenes: each test checks a property the release relies on."""
import numpy as np
import pytest

from inkeval import auc, judge_classes, local_stroke_auc, pixel_auc, stroke_auc
from inkeval.synth import scene


def test_auc_basic_and_ties():
    assert auc([2, 3], [0, 1]) == 1.0
    assert auc([0, 1], [2, 3]) == 0.0
    assert auc([1, 1], [1, 1]) == 0.5          # ties count one half
    assert auc([], [1]) is None


def test_auc_matches_bruteforce():
    rng = np.random.default_rng(1)
    a, b = rng.normal(0.5, 1, 200), rng.normal(0, 1, 150)
    brute = np.mean([(x > y) + 0.5 * (x == y) for x in a for y in b])
    assert auc(a, b) == pytest.approx(brute, abs=1e-12)


def test_judge_classes_geometry():
    lab = np.zeros((200, 200), bool); lab[90:110, 90:110] = True
    mask = np.ones_like(lab)
    text, blank = judge_classes(lab, mask, pitch_um=10.0, blank_min_mm=0.3, zone_mm=1.0)
    assert text.sum() == lab.sum()
    assert not (blank & lab).any()
    # blank pixels are at least 0.3 mm (30 px) and at most 1 mm (100 px), Euclidean, from the nearest label pixel
    ys, xs = np.nonzero(blank)
    d = np.hypot(np.maximum(np.maximum(90 - ys, ys - 109), 0), np.maximum(np.maximum(90 - xs, xs - 109), 0))
    assert d.min() >= 30 - 1e-9 and d.max() <= 100 + 1e-9


def test_perfect_and_null_detectors():
    score, label, mask = scene(signal=1.0, texture=0.0, seed=3)
    text, blank = judge_classes(label, mask, pitch_um=2.4)
    assert pixel_auc(score, text, blank, subsample=None) > 0.99
    noise = np.random.default_rng(0).normal(size=score.shape).astype(np.float32)
    assert abs(pixel_auc(noise, text, blank, subsample=None) - 0.5) < 0.02


def test_stroke_defined_when_components_merge():
    # one giant merged component: a component-based letter test has nothing to average; the stroke test still works
    score, label, mask = scene(n_strokes=25, width_px=60, signal=1.0, texture=1.0, seed=4)
    a, n_ink, n_blank = stroke_auc(score, label, mask, pitch_um=10.0)
    assert a is not None and n_ink >= 20 and n_blank >= 20 and a > 0.8


def test_local_L_cancels_regional_gradient():
    # a pure left-to-right brightness gradient plus labels concentrated on one side: global stroke AUC is fooled, L is not
    rng = np.random.default_rng(5)
    h = w = 800
    label = np.zeros((h, w), bool)
    for _ in range(25):
        y, x = rng.integers(50, h - 50), rng.integers(w // 2, w - 60)
        label[y - 25:y + 25, x - 14:x + 14] = True
    ramp = np.linspace(0, 1, w)[None, :] * np.ones((h, 1))
    texture = rng.normal(0, 0.02, (h, w))
    score = (ramp + texture).astype(np.float32)
    mask = np.ones((h, w), bool)
    g, _, _ = stroke_auc(score, label, mask, pitch_um=2.4, r_mm=0.02, blank_mm=0.05, max_n=500)
    L, *_ = local_stroke_auc(score, label, mask, pitch_um=2.4, r_mm=0.02, blank_mm=0.05, near_mm=0.25, max_ink=500)
    assert g > 0.7          # fooled by geography (measured 0.783)
    assert abs(L - 0.5) < 0.05  # sees no letter-level signal (measured 0.510)


def test_metrics_are_rank_invariant():
    score, label, mask = scene(seed=6)
    text, blank = judge_classes(label, mask, 2.4)
    a1 = pixel_auc(score, text, blank); a2 = pixel_auc(np.exp(score / 3), text, blank)
    assert a1 == pytest.approx(a2, abs=1e-12)
