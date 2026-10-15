# Provenance: Project HERCULES | owner the owner | [id removed]
"""Spiral pitch-angle winding estimator (tools/sib/handed/spiral_sense.py)
on synthetic axial slices. Numbers only.
Run: PYTHONPATH=src /opt/hv/bin/python -m pytest -q tests/sib_handed_spiral.py"""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "sib" / "handed"))
sys.path.insert(0, str(ROOT / "src"))
import spiral_sense as SS  # noqa: E402
import synth as S  # noqa: E402


def slice_of(w, pitch, squash=1.0, centre_err=(0.0, 0.0)):
    sp = S.Spiral(centre=(100.0, 100.0), r_outer=90.0, pitch=pitch, turns=(90 - 15) / pitch, phi_start=0.3, w=w)
    vol = S.spiral_glyph_volume((3, 200, 200), sp, np.zeros((5, 5), np.float32), k_glyph=0, phi_g=0.0, z_c=1.0,
                                pix=1.0, envelope=0.0).vol
    img = vol[1]
    if squash != 1.0:  # crushed scroll: compress y about the centre
        yy, xx = np.mgrid[0:200, 0:200].astype(np.float32)
        from scipy.ndimage import map_coordinates
        img = map_coordinates(img, [100 + (yy - 100) / squash, xx], order=1)
    img = (img * 255 / img.max()).astype(np.uint8)
    yy, xx = np.mgrid[0:200, 0:200]
    m = np.hypot(xx - 100, (yy - 100) / squash) < 92
    return SS.slice_psi(img, m, 100.0 + centre_err[0], 100.0 + centre_err[1], 1)


@pytest.mark.parametrize("w", [1, -1])
@pytest.mark.parametrize("pitch", [9.0, 4.0, 2.5])
def test_sign_and_magnitude(w, pitch):
    r = slice_of(w, pitch)
    expected = np.degrees(np.mean([np.arctan(pitch / (2 * np.pi * rr)) for rr in np.linspace(20, 90, 50)]))
    assert np.sign(r["psi_mean_deg"]) == w
    assert abs(r["psi_mean_deg"]) == pytest.approx(expected, rel=0.35)
    assert np.sign(r["a0_vox"]) == w and abs(r["a0_vox"]) == pytest.approx(pitch / (2 * np.pi), rel=0.35)


@pytest.mark.parametrize("w", [1, -1])
def test_robust_to_centre_error_and_crushing(w):
    for r in (slice_of(w, 4.0, centre_err=(6.0, -4.0)), slice_of(w, 4.0, squash=0.6),
              slice_of(w, 2.5, centre_err=(15.0, 10.0)), slice_of(w, 4.0, squash=0.45),
              slice_of(w, 4.0, centre_err=(15.0, 10.0))):
        assert np.sign(r["a0_vox"]) == w, r


def test_documented_resolution_limit():
    """Applicability limit (recorded, not hidden): when crushing compresses the
    sheet spacing to ~1 px at the analysis level the sign is unreliable, so
    real volumes are analysed at a level where spacing is >= 4 px."""
    r = [slice_of(w, 2.5, squash=0.45)["a0_vox"] * w for w in (1, -1)]
    assert min(r) < 0  # fails for at least one sense: unresolved regime
