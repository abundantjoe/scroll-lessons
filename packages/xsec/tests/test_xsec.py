import os, sys, json, numpy as np, zarr
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from xsec import synth, tifxyz, radial_gate, xsections

def _setup(tmp):
    cx = cy = 128.0; vol = synth.shell_volume((64, 256, 256), cx, cy, radii=[60, 70, 80]); zarr.save(os.path.join(tmp, "vol.zarr"), vol)
    on = os.path.join(tmp, "on"); jump = os.path.join(tmp, "jump")
    synth.save_patch(on, R=70, theta0=0.2, theta1=1.4, z0=10, z1=54, cx=cx, cy=cy)
    synth.save_patch(jump, R=70, theta0=0.2, theta1=1.4, z0=10, z1=54, cx=cx, cy=cy, jump_at=0.5, jump_dr=5)   # r=75: in the dark gap between the 70 and 80 shells
    return on, jump, cx, cy

def test_radial_gate_is_blind_to_a_layer_jump(tmp_path):
    on, jump, cx, cy = _setup(str(tmp_path))
    g1 = radial_gate.gate(*tifxyz.read(on), cx, cy); g2 = radial_gate.gate(*tifxyz.read(jump), cx, cy)
    assert g1["median_cos"] > 0.95 and g2["median_cos"] > 0.95       # both 'pass' the normal test
    assert g2["spread_vox"] > g1["spread_vox"] + 3                   # only the radial spread moves, and only because the jump is radial

def test_cross_section_and_on_bright_fraction(tmp_path):
    on, jump, cx, cy = _setup(str(tmp_path)); vol = os.path.join(tmp_path, "vol.zarr")
    r1 = xsections.main([on, vol, str(tmp_path / "on"), "--level", "0", "--scale", "1"])
    r2 = xsections.main([jump, vol, str(tmp_path / "jump"), "--level", "0", "--scale", "1"])
    assert os.path.exists(tmp_path / "on_xsec.png") and os.path.exists(tmp_path / "jump_xsec.png")
    assert r1["on_bright_fraction"] > 0.95
    assert 0.3 < r2["on_bright_fraction"] < 0.7   # half the jumped patch sits in the gap

def test_tifxyz_roundtrip(tmp_path):
    X, Y, Z = synth.cylinder_patch(50, 0, 1, 0, 10, n=8); d = str(tmp_path / "p"); tifxyz.write(d, X, Y, Z)
    X2, Y2, Z2 = tifxyz.read(d); assert np.allclose(X, X2) and np.allclose(Z, Z2)
