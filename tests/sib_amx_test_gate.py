# Provenance: Project HERCULES | owner the owner | [id removed]
"""Unit tests for tools/sib/amx/amx_gate.py on synthetic arrays only (no scroll data)."""
import importlib.util
import json
import os

import numpy as np
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("amx_gate", os.path.join(_HERE, "..", "tools", "sib", "amx", "amx_gate.py"))
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

H = W = 200


def _scene(seed=0):
    """Labels: ink square in a blank field, a ring of ignored pixels; fp32 forward map separates ink from blank,
    fp32 reverse map is label-independent noise."""
    rng = np.random.default_rng(seed)
    lab = np.zeros((H, W), np.int8)
    lab[60:140, 60:140] = 1
    lab[55:60, :] = -1
    fwd = np.clip(np.where(lab == 1, 200, 60) + rng.normal(0, 15, (H, W)), 0, 255).astype(np.uint8)
    rev = np.clip(120 + rng.normal(0, 20, (H, W)), 0, 255).astype(np.uint8)
    valid = np.ones((H, W), bool)
    valid[:, :5] = False
    return lab, fwd, rev, valid


def _jitter(m, rng, k=1):
    return np.clip(m.astype(np.int16) + rng.integers(-k, k + 1, m.shape), 0, 255).astype(np.uint8)


def test_identical_maps_pass_with_zero_diff():
    lab, fwd, rev, valid = _scene()
    r = G.gate(fwd, fwd.copy(), lab, valid, rev, rev.copy())
    assert r["verdict"] == "PASS"
    assert r["max_abs_diff"] == 0 and r["frac_within_2"] == 1.0
    assert r["pearson"] == pytest.approx(1.0)
    assert r["orders"]["forward"]["frac_identical"] == 1.0
    assert r["auc_forward"] > 0.99 and 0.4 < r["auc_reverse"] < 0.6
    assert r["orders"]["forward"]["delta_auc_bf16_minus_fp32"] == 0.0


def test_small_jitter_passes_and_counts_are_exact():
    lab, fwd, rev, valid = _scene()
    rng = np.random.default_rng(1)
    r = G.gate(fwd, _jitter(fwd, rng), lab, valid, rev, _jitter(rev, rng))
    assert r["verdict"] == "PASS"
    assert r["max_abs_diff"] <= 1 and r["frac_within_2"] == 1.0
    f = r["orders"]["forward"]
    assert f["n_valid"] == int(valid.sum()) and sum(f["abs_diff_hist_0_1_2_3_4_5plus"]) == f["n_valid"]
    assert r["n_ink"] == int(((lab == 1) & valid).sum()) and r["n_blank"] == int(((lab == 0) & valid).sum())


def test_pearson_matches_numpy_on_valid_pixels():
    lab, fwd, rev, valid = _scene()
    b = _jitter(fwd, np.random.default_rng(2), k=20)
    r = G.gate(fwd, b, lab, valid)
    ref = np.corrcoef(fwd[valid].astype(float), b[valid].astype(float))[0, 1]
    assert r["orders"]["forward"]["pearson"] == pytest.approx(ref, abs=1e-12)


def test_within_two_bar_fails_when_too_many_pixels_move():
    lab, fwd, rev, valid = _scene()
    b = fwd.copy()
    idx = np.flatnonzero(valid.ravel())[: int(0.002 * valid.sum())]  # 0.2 % of valid pixels moved by 3 levels
    flat = b.ravel()
    flat[idx] = np.where(flat[idx] > 127, flat[idx] - 3, flat[idx] + 3)
    r = G.gate(fwd, b, lab, valid, rev, rev.copy())
    assert r["max_abs_diff"] == 3
    assert r["orders"]["forward"]["frac_within_2"] == pytest.approx(1 - len(idx) / valid.sum())
    assert r["checks"]["frac_within_2_forward"] is False and r["verdict"] == "FAIL"
    assert r["checks"]["pearson_forward"] is True  # Pearson alone would not catch it


def test_within_two_bar_boundary_is_inclusive():
    lab, fwd, rev, valid = _scene()
    b = fwd.copy()
    n_move = int(np.floor(0.001 * valid.sum()))  # exactly at the 99.9 % bar (or just inside it)
    idx = np.flatnonzero(valid.ravel())[:n_move]
    flat = b.ravel()
    flat[idx] = np.where(flat[idx] > 127, flat[idx] - 3, flat[idx] + 3)
    r = G.gate(fwd, b, lab, valid, rev, rev.copy())
    assert r["orders"]["forward"]["frac_within_2"] >= 0.999
    assert r["checks"]["frac_within_2_forward"] is True


def test_invalid_pixels_are_ignored():
    lab, fwd, rev, valid = _scene()
    b = fwd.copy()
    b[:, :5] = 255 - b[:, :5]  # large differences only where valid is False
    r = G.gate(fwd, b, lab, valid, rev, rev.copy())
    assert r["max_abs_diff"] == 0 and r["verdict"] == "PASS"


def test_reverse_auc_bar_fails_when_reverse_map_reads_ink():
    lab, fwd, rev, valid = _scene()
    r = G.gate(fwd, fwd.copy(), lab, valid, fwd.copy(), fwd.copy())  # reverse order as discriminative as forward
    assert r["checks"]["auc_reverse"] is False and r["verdict"] == "FAIL"


def test_forward_auc_bar_fails_on_weak_map():
    lab, fwd, rev, valid = _scene()
    r = G.gate(rev, rev.copy(), lab, valid, rev, rev.copy())
    assert r["checks"]["auc_forward"] is False and r["verdict"] == "FAIL"


def test_missing_reverse_is_incomplete_and_half_pair_raises():
    lab, fwd, rev, valid = _scene()
    r = G.gate(fwd, fwd.copy(), lab, valid)
    assert r["checks"]["auc_reverse"] is None and r["verdict"] == "INCOMPLETE"
    with pytest.raises(ValueError):
        G.gate(fwd, fwd.copy(), lab, valid, rev, None)


def test_type_and_shape_checks():
    lab, fwd, rev, valid = _scene()
    with pytest.raises(TypeError):
        G.gate(fwd.astype(np.float32), fwd, lab, valid)
    with pytest.raises(ValueError):
        G.gate(fwd, fwd[:-1], lab, valid)
    with pytest.raises(ValueError):
        G.gate(fwd, fwd, lab, np.zeros_like(valid))


def test_binarize_labels_matches_c3_rule():
    raw = np.array([[0, 255, 100, 128], [127, 0, 255, 200]], np.uint8)
    b = G.binarize_labels(raw)
    assert b.tolist() == [[0, 1, -1, 1], [-1, 0, 1, 1]]  # ink = raw > 127.5, blank = raw == 0, rest ignored


def test_cli_end_to_end(tmp_path):
    lab, fwd, rev, valid = _scene()
    rng = np.random.default_rng(3)
    raw = np.where(lab == 1, 255, np.where(lab == 0, 0, 100)).astype(np.uint8)
    files = dict(f32f=fwd, b16f=_jitter(fwd, rng), f32r=rev, b16r=_jitter(rev, rng), lab=raw, val=valid.astype(np.uint8))
    for k, v in files.items():
        np.save(tmp_path / f"{k}.npy", v)
    out = tmp_path / "gate.json"
    rc = G.main(["--fp32-fwd", str(tmp_path / "f32f.npy"), "--bf16-fwd", str(tmp_path / "b16f.npy"),
                 "--fp32-rev", str(tmp_path / "f32r.npy"), "--bf16-rev", str(tmp_path / "b16r.npy"),
                 "--labels", str(tmp_path / "lab.npy"), "--valid", str(tmp_path / "val.npy"), "--out", str(out)])
    res = json.loads(out.read_text())
    assert rc == 0 and res["verdict"] == "PASS"
    assert set(res["inputs"]) == {"fp32_fwd", "bf16_fwd", "fp32_rev", "bf16_rev", "labels", "valid"}
    assert all(len(v["sha256"]) == 64 for v in res["inputs"].values())
    direct = G.gate(fwd, files["b16f"], G.binarize_labels(raw), valid, rev, files["b16r"])
    assert res["pearson"] == pytest.approx(direct["pearson"]) and res["auc_forward"] == pytest.approx(direct["auc_forward"])
