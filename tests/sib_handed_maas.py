# Provenance: Project HERCULES | owner the owner | [id removed]
"""Column-slant (Maas's law) estimator on synthetic binary layouts: numbers
only. Run: PYTHONPATH=src /opt/hv/bin/python -m pytest -q tests/sib_handed_maas.py"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "sib" / "handed"))
import maas as M  # noqa: E402


@pytest.mark.parametrize("slant", [1.5, 3.0])
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_slant_sign_mirror_and_rotation(slant, seed):
    img = M.synthetic_layout(slant_deg=slant, seed=seed)
    r = M.layout_slant(img, 12)
    assert r["n_measured"] == 3 and r["n_left_neg"] == 3
    assert r["median_slant_left_deg"] == pytest.approx(-slant, abs=0.8)
    lr = M.layout_slant(img[:, ::-1], 12)  # mirror reverses the slant
    assert lr["n_left_pos"] == 3 and lr["median_slant_left_deg"] == pytest.approx(slant, abs=0.8)
    rot = M.layout_slant(img[::-1, ::-1], 12)  # 180 deg rotation keeps it
    assert rot["n_left_neg"] == 3


def test_robust_to_line_tilt():
    img = M.synthetic_layout(slant_deg=3.0, seed=4)
    tilted = (M.rotate(np.pad(img, 40), 5.0) > 0.5).astype(np.uint8)
    r = M.layout_slant(tilted, 12)
    assert r["n_left_neg"] == r["n_measured"] >= 2


def test_null_layout_has_no_consistent_slant():
    signs = []
    for seed in range(6):
        r = M.layout_slant(M.synthetic_layout(slant_deg=0.0, seed=seed), 12)
        assert abs(r["median_slant_left_deg"]) < 0.8
        signs.append(np.sign(r["median_slant_left_deg"]))
    assert abs(sum(signs)) < 6  # not all one direction


def test_patches_without_column_edges_are_not_measured():
    """Label patches narrower than a column (as in the 0139 labels) yield no
    measurement rather than a spurious sign."""
    img = M.synthetic_layout(slant_deg=3.0, seed=0, col_w=40, gap=60, n_lines=5)
    r = M.layout_slant(img, 12)
    assert r["n_measured"] == 0
