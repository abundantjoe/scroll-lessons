# Provenance: Project HERCULES | owner the owner | [id removed]
"""Manifest-driven control builders: scroll guard, completeness, hash verification, build."""

import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from hercules.tribunal import controls as K
from hercules.tribunal import manifest as M

EXAMPLE = Path(__file__).resolve().parents[1] / "logs" / "sib" / "tribunal" / "controls_manifest_example.json"


def _arr(seed):
    a = np.random.default_rng(seed).integers(20, 230, (256, 256)).astype(np.uint8)
    return a, hashlib.sha256(a.tobytes()).hexdigest()


SRC = {f"src{i}": _arr(i) for i in range(3)}


def _loader(src):
    return SRC[src["source"]]


def _filled():
    return {
        "manifest_version": 1, "batch_id": "T",
        "voxel": {"metadata_source": "s3://x/PHerc0139/volumes/v.zarr/metadata.json", "voxel_um": 9.362},
        "display": {"window": "raw", "display_scale": 0.5},
        "positive_canaries": [{"canary_id": "pc1", "tile": {"scroll": "PHerc0139", "segment": "s", "window": {}},
                               "ref_map": {"source": "src0", "sha256": SRC["src0"][1]}, "sigma_mm": 0.2,
                               "ref_ceiling": {"recall": 0.8, "rows_found": 1.0}}],
        "baits": [{"bait_id": "b1", "kind": "wrong_order", "tile": {"scroll": "PHerc0139"},
                   "map": {"source": "src1", "sha256": SRC["src1"][1]}},
                  {"bait_id": "b2", "kind": "blank", "tile": {"scroll": "PHerc0139"}, "map": None,
                   "blank_mode": "phase_scramble", "derive_from": "pc1"}],
        "mirror_canaries": {"glyphs": "EKRCGBN", "letter_height_mm": 1.0, "sigma_mm": 0.0, "canvas_hw": [256, 256],
                            "font_sha256": K.font_sha256()},
    }


def test_filled_manifest_builds(tmp_path):
    res = M.build_from_manifest(_filled(), _loader, tmp_path, rng=np.random.default_rng(0))
    kinds = [k["type"] for k in res["keys"]]
    assert kinds.count("positive_canary") == 1 and kinds.count("bait") == 2 and kinds.count("mirror_canary") == 14
    for k in res["keys"]:
        assert (tmp_path / k["image"]["name"]).exists()
        assert set(K.png_chunks((tmp_path / k["image"]["name"]).read_bytes())) <= K.ALLOWED_PNG_CHUNKS
    b = next(c for c in res["controls"] if c["control_id"] == "b1")
    assert b["area_cm2"] == pytest.approx((256 * 9.362e-4) ** 2)


def test_hash_mismatch_aborts(tmp_path):
    m = _filled()
    m["baits"][0]["map"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash mismatch"):
        M.build_from_manifest(m, _loader, tmp_path, rng=np.random.default_rng(0))


@pytest.mark.parametrize("scroll", ["PHerc0841", "PHerc0814", sorted(M.eligible_scrolls())[0]])
def test_positive_scroll_guard(scroll):
    m = _filled()
    m["positive_canaries"][0]["tile"]["scroll"] = scroll
    assert any("not allowed for positives" in e for e in M.validate_manifest(m, for_build=True))


def test_forbidden_bait_sources():
    m = _filled()
    m["baits"][0]["tile"]["scroll"] = "PHerc0841"
    assert any("forbidden" in e for e in M.validate_manifest(m, for_build=True))
    m["baits"][0]["tile"]["scroll"] = sorted(M.eligible_scrolls())[-1]
    assert any("forbidden" in e for e in M.validate_manifest(m, for_build=True))


def test_eligible_list_has_23_scrolls_without_0139():
    e = M.eligible_scrolls()
    assert len(e) >= 20 and "PHerc0139" not in e and "PHerc0841" not in e


def test_missing_numbers_refused(tmp_path):
    m = copy.deepcopy(_filled())
    m["positive_canaries"][0]["sigma_mm"] = None
    with pytest.raises(ValueError, match="sigma_mm"):
        M.build_from_manifest(m, _loader, tmp_path, rng=np.random.default_rng(0))


def test_example_manifest_is_clean_0139_and_structurally_valid():
    m = json.loads(EXAMPLE.read_text())
    assert M.validate_manifest(m, for_build=False) == []
    assert M.validate_manifest(m, for_build=True)  # placeholders: never buildable as shipped
    scrolls = {c["tile"]["scroll"] for c in m["positive_canaries"]} | {b["tile"]["scroll"] for b in m["baits"]}
    assert scrolls == {"PHerc0139"}
    assert all("w024" in c["tile"]["segment"] or "w053" in c["tile"]["segment"] for c in m["positive_canaries"])
