"""Exact reproduction of published numbers.

The bundled example is checked against values recorded when it was built. When the full research data are on disk (data/s1/...),
the toolkit is also checked against the judge files and stroke-test records that the release cites, to the last digit.
"""
import json
import os

import numpy as np
import pytest

from inkeval import judge_classes, local_stroke_auc, pixel_auc, stroke_auc
from inkeval.example import run_demo

ROOT = os.path.dirname(os.path.dirname(__file__))
CROP = os.path.join(ROOT, "data", "s1", "20231005123336", "derived", "held2")


def test_demo_runs_and_controls_behave():
    r = run_demo(verbose=False)
    for k, per in r["judge"].items():
        assert per["e"]["pixel_auc"] > per["v7"]["pixel_auc"]          # learned beats hand-built on both crops
        assert per["team"]["pixel_auc"] > 0.9                           # positive control reads the text
    for t, v in r["null"].items():
        assert abs(v["mean"] - 0.5) < 0.1                               # negative control near chance


@pytest.mark.skipif(not os.path.exists(os.path.join(CROP, "s_bot_e.npy")), reason="full research data not on disk")
@pytest.mark.parametrize("tag", ["e", "team"])
def test_pixel_auc_equals_judge_record(tag):
    label = np.load(os.path.join(CROP, "label.npy"))
    mask = (np.load(os.path.join(CROP, "mask_top.npy")) > 0) & (np.load(os.path.join(CROP, "mask_bot.npy")) > 0)
    text, blank = judge_classes(label, mask, 2.4)
    assert (text == np.load(os.path.join(CROP, "cls_text.npy"))).all()
    assert (blank == np.load(os.path.join(CROP, "cls_blank.npy"))).all()
    s = np.load(os.path.join(CROP, f"s_bot_{tag}.npy")).astype(np.float32)
    rec = json.load(open(os.path.join(CROP, f"judge_{tag}.json")))["bot"]["auc_px"]
    assert pixel_auc(s, text, blank) == rec


@pytest.mark.skipif(not os.path.exists(os.path.join(CROP, "s_bot_e.npy")), reason="full research data not on disk")
def test_stroke_and_local_equal_records():
    label = np.load(os.path.join(CROP, "label.npy"))
    mask = (np.load(os.path.join(CROP, "mask_top.npy")) > 0) & (np.load(os.path.join(CROP, "mask_bot.npy")) > 0)
    s = np.load(os.path.join(CROP, "s_bot_e.npy")).astype(np.float32)
    S = json.load(open(os.path.join(ROOT, "stats", "stroke_test.json")))["20231005123336:held2"]["e"]
    L = json.load(open(os.path.join(ROOT, "stats", "local_stroke_test.json")))["20231005123336:held2"]["e"]
    a, n1, n0 = stroke_auc(s, label, mask)
    assert (round(a, 4), n1, n0) == (S["stroke_auc"], S["n_ink"], S["n_blank"])
    l, ni, nb, npair = local_stroke_auc(s, label, mask)
    assert (round(l, 4), ni, nb, npair) == (L["L"], L["n_ink"], L["n_blank"], L["n_paired"])
