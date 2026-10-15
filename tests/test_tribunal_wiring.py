# Provenance: Project HERCULES | owner the owner | [id removed]
"""No image reaches a reader without a passed TRIBUNAL certificate."""


import numpy as np
import pytest

from hercules.tribunal import controls as K
from hercules.tribunal import wiring as Wr
from hercules.tribunal.preread import TribunalFault


def _img(tmp, seed):
    a = np.random.default_rng(seed).integers(0, 256, (32, 32)).astype(np.uint8)
    w = K.write_image(a, tmp / "imgs")
    return tmp / "imgs" / w["name"]


def test_passed_gate_certifies_and_failed_gate_refuses(tmp_path):
    p = _img(tmp_path, 0)
    Wr.certify_window({"window_id": "w", "passed": True, "failed": []}, [p], tmp_path / "cert")
    Wr.assert_images_certified([p], tmp_path / "cert")
    q = _img(tmp_path, 1)
    with pytest.raises(TribunalFault):
        Wr.certify_window({"window_id": "w2", "passed": False, "failed": ["mirror"]}, [q], tmp_path / "cert")
    with pytest.raises(TribunalFault):
        Wr.assert_images_certified([p, q], tmp_path / "cert")


def test_changed_bytes_lose_certification(tmp_path):
    p = _img(tmp_path, 2)
    Wr.certify_window({"window_id": "w", "passed": True, "failed": []}, [p], tmp_path / "cert")
    p.write_bytes(p.read_bytes() + b"\0")
    with pytest.raises(TribunalFault):
        Wr.assert_images_certified([p], tmp_path / "cert")


def test_control_certificates(tmp_path):
    img, key = K.build_bait("blank", np.full((64, 64), 60.0), bait_id="b", blank_mode="constant")
    keys = K.write_controls([(img, key)], tmp_path / "imgs")
    Wr.certify_controls(keys, tmp_path / "imgs", tmp_path / "cert")
    Wr.assert_images_certified([tmp_path / "imgs" / keys[0]["image"]["name"]], tmp_path / "cert")


def test_harness_make_refuses_uncertified_images(tmp_path, monkeypatch):
    """The single hook in hercules.harness.jobs.make: no reader job without certificates."""
    from hercules.harness import jobs
    rcpt = tmp_path / "rcpt.pub"
    rcpt.write_text("age1testrecipient\n")
    monkeypatch.setattr(jobs, "JOBS", str(tmp_path / "jobs"))
    monkeypatch.setattr(jobs, "IO", str(tmp_path / "io"))
    monkeypatch.setattr(jobs, "RECIPIENT_FILE", str(rcpt))
    monkeypatch.setattr(jobs, "TRIBUNAL_CERTS", str(tmp_path / "cert"))
    monkeypatch.setattr(jobs, "_utc", lambda: "2026-01-01T00:00:00Z")
    p = _img(tmp_path, 7)
    with pytest.raises(TribunalFault):
        jobs.make("reader", "task", [str(p)])
    assert not (tmp_path / "jobs").exists()  # refused before anything was written
    Wr.certify_window({"window_id": "w", "passed": True, "failed": []}, [p], tmp_path / "cert")
    job, brief = jobs.make("reader", "task", [str(p)])
    assert (tmp_path / "jobs" / f"{job}.json").exists() and str(p) in brief
