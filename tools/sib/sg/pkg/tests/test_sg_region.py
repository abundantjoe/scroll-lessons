# Provenance: Project HERCULES | owner the owner | [id removed]
"""Unit tests for R (DECL-SG preamble) and the SG 11 layout metrics (hercules.sg.gate)."""

import ast
import builtins
import inspect
import math
import random
from pathlib import Path

import numpy as np
import pytest


from hercules.sg import constants as C
from hercules.sg import gate as G
from hercules.sg import synth as S

KINDS = S.CANONICAL_KINDS


def random_discovery(seed, n=30, span=6000.0, origin=1000.0):
    rng = np.random.default_rng(seed)
    pts = rng.uniform(origin, origin + span, (n, 2))
    kinds = [KINDS[int(i)] for i in rng.integers(0, 24, n)]
    out = {}
    for rid in ("a", "b", "c"):
        j = rng.uniform(-20, 20, (n, 2))
        keep = rng.random(n) < 0.85
        out[rid] = [{"ch": k, "x": float(p[0] + d[0]), "y": float(p[1] + d[1]), "conf": "tentative"}
                    for k, p, d, kp in zip(kinds, pts, j, keep) if kp]
    return out


# ------------------------------------------------------------------ R shape and optimality


@pytest.mark.parametrize("seed", range(8))
def test_R_shape_always_valid(seed):
    r = G.compute_R(random_discovery(seed), S.PPM, S.CANVAS_WH)
    assert r["status"] == "PASS"
    assert abs(r["area_cm2"] - 4.0) <= 0.04 and r["aspect"] <= 2.0 + 1e-9
    rect = r["rect"]
    assert 0 <= rect["x0"] and rect["x1"] <= S.CANVAS_WH[0] and 0 <= rect["y0"] and rect["y1"] <= S.CANVAS_WH[1]


@pytest.mark.parametrize("seed", range(4))
def test_R_maximises_agreed_letters_against_random_placements(seed):
    disc = random_discovery(seed)
    r = G.compute_R(disc, S.PPM, S.CANVAS_WH)
    pts = np.array([(g["x"], g["y"]) for g in G._agreed(disc)])
    area = 400.0 * S.PPM ** 2
    rng = np.random.default_rng(100 + seed)
    best = 0
    for _ in range(20000):
        w = rng.uniform(math.sqrt(area / 2), math.sqrt(area * 2))
        h = area / w
        x0, y0 = rng.uniform(0, S.CANVAS_WH[0] - w), rng.uniform(0, S.CANVAS_WH[1] - h)
        best = max(best, int(((pts[:, 0] >= x0) & (pts[:, 0] <= x0 + w) & (pts[:, 1] >= y0) & (pts[:, 1] <= y0 + h)).sum()))
    assert r["n_inside"] >= best


def test_R_exact_on_known_cluster():
    # 12 letters in a tight 10 x 5 mm cluster and 3 isolated letters far away
    L = S.text_letters(n_rows=2, per_row=6)
    disc = S.read(L, ("a", "b", "c"), seed=1, jitter=0)
    far = [{"ch": KINDS[i], "x": 7500.0, "y": 500.0 + 900 * i} for i in range(3)]
    for rid in ("a", "b"):
        disc[rid] += far
    r = G.compute_R(disc, S.PPM, S.CANVAS_WH)
    assert r["n_inside"] == 12 and r["n_agreed_discovery"] == 15
    # centred: equal margins left/right of the cluster
    xs = [l["x"] for l in L]
    rect = r["rect"]
    assert (min(xs) - rect["x0"]) == pytest.approx(rect["x1"] - max(xs), abs=1e-6)


def test_R_empty_discovery_fails():
    assert G.compute_R({"a": [], "b": [], "c": []}, S.PPM)["status"] == "FAIL"


def test_R_canvas_too_small():
    assert G.compute_R(random_discovery(0), S.PPM, (1000, 1000))["reason"] == "canvas_smaller_than_R"


def test_R_depends_on_px_per_mm_from_metadata():
    disc = random_discovery(1)
    r1 = G.compute_R(disc, G.px_per_mm(9.366), S.CANVAS_WH)
    r2 = G.compute_R(disc, G.px_per_mm(7.91), S.CANVAS_WH)
    for r, ppm in ((r1, G.px_per_mm(9.366)), (r2, G.px_per_mm(7.91))):
        w, h = r["rect"]["x1"] - r["rect"]["x0"], r["rect"]["y1"] - r["rect"]["y0"]
        assert w * h / ppm ** 2 == pytest.approx(400.0)


# ------------------------------------------------------------------ R never depends on image content


def test_R_signature_takes_no_image():
    params = list(inspect.signature(G.compute_R).parameters)
    assert params == ["discovery_text_readers", "ppm", "canvas_wh"]


def test_R_invariant_to_order_and_extra_fields():
    disc = random_discovery(3)
    r0 = G.compute_R(disc, S.PPM, S.CANVAS_WH)
    rnd = random.Random(0)
    for _ in range(5):
        ids = list(disc)
        rnd.shuffle(ids)
        shuffled = {}
        for rid in ids:
            ns = [dict(n, pixels=np.random.default_rng(1).random((8, 8)), image="x.png") for n in disc[rid]]
            rnd.shuffle(ns)
            shuffled[rid] = ns
        r = G.compute_R(shuffled, S.PPM, S.CANVAS_WH)
        assert r["rect"] == r0["rect"] and r["rect_sha256"] == r0["rect_sha256"]


def test_R_reads_no_file(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("compute_R touched a file or an image loader")
    import cv2
    monkeypatch.setattr(builtins, "open", boom)
    monkeypatch.setattr(np, "load", boom)
    monkeypatch.setattr(np, "fromfile", boom)
    monkeypatch.setattr(cv2, "imread", boom)
    assert G.compute_R(random_discovery(2), S.PPM, S.CANVAS_WH)["status"] == "PASS"


def test_gate_module_imports_no_image_library():
    tree = ast.parse(Path(G.__file__).read_text(encoding="utf-8"))
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module.split(".")[0])
    assert not mods & {"cv2", "PIL", "tifffile", "zarr", "imageio", "skimage", "matplotlib"}


# ------------------------------------------------------------------ layout (SG 11)


def boxes_for(letters):
    return [[l["x"] - 0.4 * l["h"], l["y"] - 0.5 * l["h"], l["x"] + 0.4 * l["h"], l["y"] + 0.5 * l["h"]] for l in letters]


def test_layout_passes_regular_text():
    r = G.layout_metrics(boxes_for(S.text_letters()), S.PPM)
    assert r["status"] == "PASS" and r["n_rows"] == 3 and r["pitch_cv"] == pytest.approx(0.0, abs=1e-9)
    assert r["letter_height_mm_median"] == pytest.approx(3.0) and r["pitch_mm_mean"] == pytest.approx(5.0)


@pytest.mark.parametrize("angle,ok", [(9.5, True), (-9.5, True), (10.5, False), (-11.0, False)])
def test_layout_baseline_angle(angle, ok):
    L = S.text_letters(angle_deg=angle)
    r = G.layout_metrics(boxes_for(L), S.PPM)
    assert r["rows_ok"] is ok
    if ok:
        assert all(abs(abs(a) - abs(angle)) < 0.01 for a in r["row_angles_deg"])


@pytest.mark.parametrize("h,ok", [(1.9, False), (2.0, True), (4.0, True), (4.2, False)])
def test_layout_letter_height(h, ok):
    L = S.text_letters(height_mm=h, pitch_mm=max(5.0, 1.8 * h))
    r = G.layout_metrics(boxes_for(L), S.PPM)
    assert r["rows_ok"] and r["heights_ok"] is ok


def test_layout_pitch_cv():
    L = S.text_letters(n_rows=4)
    # rows at 0, 5, 10, 15 mm -> move the last row to 19 mm: pitches 5, 5, 9 (CV 0.28)
    for l in L[21:]:
        l["y"] += 4 * S.PPM
    r = G.layout_metrics(boxes_for(L), S.PPM)
    assert r["n_rows_within_10deg"] == 4 and r["pitch_cv"] > C.SG11_PITCH_CV_MAX and r["status"] == "FAIL"
    L = S.text_letters(n_rows=4)
    for l in L[21:]:
        l["y"] += 1 * S.PPM  # pitches 5, 5, 6 (CV 0.087)
    assert G.layout_metrics(boxes_for(L), S.PPM)["status"] == "PASS"


def test_layout_needs_two_rows_of_three():
    L = S.text_letters(n_rows=2, per_row=2)  # rows of 2 letters are not fitted
    assert G.layout_metrics(boxes_for(L), S.PPM)["n_rows"] == 0
    L = S.text_letters(n_rows=1, per_row=12)
    assert G.layout_metrics(boxes_for(L), S.PPM)["status"] == "FAIL"


def test_layout_scattered_letters_have_no_rows():
    rng = np.random.default_rng(0)
    L = [{"x": float(x), "y": float(y), "h": 3.0 * S.PPM} for x, y in rng.uniform(0, 4000, (15, 2))]
    r = G.layout_metrics(boxes_for(L), S.PPM)
    assert r["status"] == "FAIL"


# ------------------------------------------------------------------ rulings B8, B9


def test_B8_revised_fraction_reported_not_barred():
    L = S.text_letters()
    for l in L[:5]:  # 5 of 21 letters at 4.5 mm: median 3.0 mm, 16/21 = 76 % in band
        l["h"] = 4.5 * S.PPM
    r = G.layout_metrics(boxes_for(L), S.PPM)
    assert r["letter_height_mm_median"] == pytest.approx(3.0) and r["letter_height_mm_frac_in_band"] == pytest.approx(16 / 21)
    assert C.SG11_HEIGHT_FRACTION_MIN is None and r["letter_height_frac_bar"] is None
    assert r["heights_ok"] is True and r["status"] == "PASS"  # no fraction bar until declared
    assert len(r["letter_heights_mm"]) == 21 and max(r["letter_heights_mm"]) == pytest.approx(4.5)


def test_B8_median_alone_fails():
    L = S.text_letters()
    for l in L[:11]:  # 11 of 21 at 4.5 mm -> median 4.5 mm, outside 2-4 mm
        l["h"] = 4.5 * S.PPM
    r = G.layout_metrics(boxes_for(L), S.PPM)
    assert r["letter_height_mm_median"] == pytest.approx(4.5) and r["heights_ok"] is False
    assert r["rows_ok"] and r["pitch_ok"] and r["status"] == "FAIL"


def test_B9_two_rows_fail_with_cv_not_evaluated():
    L = S.text_letters(n_rows=2)
    r = G.layout_metrics(boxes_for(L), S.PPM)
    assert r["n_rows_within_10deg"] == 2 and r["pitch_cv_status"] == "NOT_EVALUATED"
    assert r["rows_ok"] is False and r["status"] == "FAIL"
    assert G.layout_metrics(boxes_for(S.text_letters(n_rows=3)), S.PPM)["status"] == "PASS"
