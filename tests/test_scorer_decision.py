# Provenance: Project HERCULES | owner the owner | [id removed]
"""End-to-end tests for spec K (score_decision) on synthetic reads with known answers."""

import copy
import dataclasses
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from hercules.scorer.canon import canonical_json
from hercules.scorer.display import DisplayMap
from hercules.scorer.null import arm_summed_mean_cnet
from hercules.scorer.score import score_decision
from hercules.scorer.synthetic import (
    perfect_text_letters,
    random_text_letters,
    reader_item,
    synthetic_seal,
)

UNIT_N_PERM = 500  # production default is 5000; unit tests stay small (4 shared cores)
UNIT_SEED = 1234
S = 30  # seal letters per text window


def build_decision():
    rng = np.random.default_rng(2026)
    seals = {
        "w1": synthetic_seal(rng, S, spacing=100.0, per_row=10, origin=(1000.0, 500.0)),
        "w2": synthetic_seal(rng, S, spacing=100.0, per_row=10, origin=(200.0, 300.0)),
        "w3": {"blank": True, "letters": []},
    }
    declaration = {
        "decision_id": "D-synthetic",
        "arms": [
            {"arm_id": "A", "readers": ["rA1", "rA2", "rA3"], "windows": ["w1", "w2", "w3"]},
            {"arm_id": "B", "readers": ["rB1", "rB2", "rB3"], "windows": ["w1", "w2", "w3"]},
        ],
    }
    display_maps = []
    reader_outputs = {}
    scales = {"rA1": 1.0, "rA2": 2.0, "rA3": 0.5, "rB1": 2.0, "rB2": 1.0, "rB3": 4.0}
    for rid in sorted(scales):
        items = []
        for k, wid in enumerate(["w1", "w2", "w3"]):
            # rA2 always sees the text order on the RIGHT; others alternate.
            left_text = (rid != "rA2") and (k % 2 == 0)
            dm = DisplayMap(
                reader_id=rid,
                item_id=f"{rid}-item{k}",
                window_id=wid,
                scale=scales[rid],
                y0=float(seals["w1"]["letters"][0]["y"] - 50.0) if wid == "w1" else 0.0,
                x0=float(900.0) if wid == "w1" else 0.0,
                side_order=("text", "nontext") if left_text else ("nontext", "text"),
            )
            display_maps.append(dm)
            if wid == "w3":
                text = [("\u0391", 100.0, 100.0), ("\u0392", 300.0, 100.0), ("?", 500.0, 100.0)]
                nontext = []
            elif rid.startswith("rA"):
                text = perfect_text_letters(seals[wid])
                nontext = [("\u039F", 400.0, 400.0), ("\u0395", 600.0, 400.0)]
            else:
                text = random_text_letters(rng, seals[wid])
                nontext = []
            items.append(reader_item(dm.item_id, dm, text, nontext))
        reader_outputs[rid] = {"items": items}
    return declaration, seals, reader_outputs, display_maps


@pytest.fixture(scope="module")
def decision():
    return build_decision()


@pytest.fixture(scope="module")
def result(decision):
    return score_decision(*decision, n_perm=UNIT_N_PERM, seed=UNIT_SEED)


def test_result_is_json_serialisable(result):
    text = canonical_json(result)
    assert json.loads(text) == json.loads(json.dumps(result))


def test_perfect_readers_recover_seal(result):
    for rid in ("rA1", "rA2", "rA3"):
        for wid in ("w1", "w2"):
            rec = result["windows"][wid]["readers"][rid]
            assert rec["C_all"]["R250"] == S
            assert rec["C_all"]["R150"] == S
            assert rec["n_named"] == S and rec["n_unknown"] == 0
            assert rec["C_net"] > 0
            assert rec["C_net"] == pytest.approx(S - rec["E_null"])
    n_firm = sum(result["windows"][w]["n_seal_firm"] for w in ("w1", "w2"))
    arm = result["arms"]["A"]
    assert arm["summed_mean_C_all"]["R250"] == 2 * S
    assert arm["summed_mean_C_firm"]["R250"] == n_firm
    assert arm["summed_mean_C_net"] > 10
    assert arm["p"] == pytest.approx(1 / (UNIT_N_PERM + 1))


def test_random_arm_is_weaker(result):
    a, b = result["arms"]["A"], result["arms"]["B"]
    assert b["summed_mean_C_net"] < a["summed_mean_C_net"]
    assert b["p"] > a["p"]


def test_p_max_family_wise(result):
    dec = result["decision"]
    assert dec["argmax_arm"] == "A"
    assert dec["p_max"] >= min(result["arms"][a]["p"] for a in ("A", "B"))
    assert dec["p_max"] == pytest.approx(1 / (UNIT_N_PERM + 1))
    assert dec["observed_max_summed_mean_C_net"] == result["arms"]["A"]["summed_mean_C_net"]


def test_arm_statistic_matches_public_helper(result):
    for aid in ("A", "B"):
        cnet = {
            w: {r: result["windows"][w]["readers"][r]["C_net"] for r in result["arms"][aid]["readers_scored"]}
            for w in result["arms"][aid]["windows"]
        }
        assert arm_summed_mean_cnet(cnet) == pytest.approx(result["arms"][aid]["summed_mean_C_net"], abs=1e-9)


def test_side_order_assignment(result):
    # rA2 always had text on the RIGHT; others alternate. All perfect readers match everything.
    for wid in ("w1", "w2"):
        rec = result["windows"][wid]["readers"]["rA2"]
        assert len(rec["items"]) == 1
        assert rec["items"][0]["side_order"] == ["nontext", "text"]
        assert rec["C_all"]["R250"] == S
        assert rec["items"][0]["rows"] == {"text": "Y", "nontext": "N"}
    assert result["windows"]["w1"]["readers"]["rA1"]["items"][0]["side_order"] == ["text", "nontext"]
    assert result["windows"]["w2"]["readers"]["rA1"]["items"][0]["side_order"] == ["nontext", "text"]
    match = result["windows"]["w1"]["readers"]["rA1"]["matches"][0]
    assert match[0] == "rA1-item0" and isinstance(match[1], int) and isinstance(match[2], int)


def test_swapped_display_key_reassigns_orders(decision):
    declaration, seals, reader_outputs, display_maps = copy.deepcopy(decision)
    # Flip the scorer's key for rA1/w1: the letters the reader wrote now count as non-text.
    flipped = []
    for dm in display_maps:
        if dm.reader_id == "rA1" and dm.window_id == "w1":
            dm = dataclasses.replace(dm, side_order=tuple(reversed(dm.side_order)))
        flipped.append(dm)
    res = score_decision(declaration, seals, reader_outputs, flipped, n_perm=50, seed=UNIT_SEED)
    rec = res["windows"]["w1"]["readers"]["rA1"]
    assert rec["C_all"]["R250"] == 0
    assert rec["n_named"] == 2
    assert rec["F_B"] == S
    assert rec["F_B_matched"]["R250"] == S


def test_f_b_counts(result):
    for wid in ("w1", "w2"):
        for rid in ("rA1", "rA2", "rA3"):
            rec = result["windows"][wid]["readers"][rid]
            assert rec["F_B"] == 2
            assert rec["F_B_unknown"] == 0
        for rid in ("rB1", "rB2", "rB3"):
            assert result["windows"][wid]["readers"][rid]["F_B"] == 0
    assert result["arms"]["A"]["F_B_total"] == 12
    assert result["arms"]["A"]["F_B_mean_per_reader"] == pytest.approx(4.0)


def test_blank_window_namings(result):
    assert result["windows"]["w3"]["blank"] is True
    for rid in ("rA1", "rB2"):
        rec = result["windows"]["w3"]["readers"][rid]
        assert rec["blank_namings"] == 2  # two known letters; the '?' is unknown
        assert rec["n_unknown"] == 1
        assert rec["C_all"]["R250"] == 0
        assert rec["C_net"] == 0
    assert result["windows"]["w1"]["readers"]["rA1"]["blank_namings"] == 0
    assert result["arms"]["A"]["blank_namings_total"] == 6
    assert result["arms"]["A"]["blank_windows"] == ["w3"]


def test_determinism_same_process(decision):
    a = canonical_json(score_decision(*decision, n_perm=100, seed=UNIT_SEED))
    b = canonical_json(score_decision(*copy.deepcopy(decision), n_perm=100, seed=UNIT_SEED))
    assert a == b


def test_seed_changes_null_but_not_observed(decision):
    a = score_decision(*decision, n_perm=100, seed=1)
    b = score_decision(*decision, n_perm=100, seed=2)
    assert a["input_sha256"] != b["input_sha256"]
    ra, rb = a["windows"]["w1"]["readers"]["rB1"], b["windows"]["w1"]["readers"]["rB1"]
    assert ra["C_all"] == rb["C_all"]
    assert ra["E_null"] != rb["E_null"]


_SUBPROCESS_SCRIPT = """
import hashlib, sys
sys.path.insert(0, {tests!r})
from test_scorer_decision import build_decision
from hercules.scorer.canon import canonical_json
from hercules.scorer.score import score_decision
out = canonical_json(score_decision(*build_decision(), n_perm=60, seed=7))
print(hashlib.sha256(out.encode("utf-8")).hexdigest())
"""


def test_determinism_across_processes_and_hash_seeds():
    tests_dir = str(Path(__file__).resolve().parent)
    src_dir = str(Path(__file__).resolve().parents[1] / "src")
    digests = []
    for hash_seed in ("0", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONPATH=src_dir)
        proc = subprocess.run(
            [sys.executable, "-c", _SUBPROCESS_SCRIPT.format(tests=tests_dir)],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        digests.append(proc.stdout.strip())
    local = hashlib.sha256(
        canonical_json(score_decision(*build_decision(), n_perm=60, seed=7)).encode("utf-8")
    ).hexdigest()
    assert digests[0] == digests[1] == local


def test_input_hash_tracks_content_not_order(decision):
    declaration, seals, reader_outputs, display_maps = copy.deepcopy(decision)
    base = score_decision(declaration, seals, reader_outputs, display_maps, n_perm=20, seed=UNIT_SEED)
    reordered = score_decision(
        declaration,
        dict(reversed(list(seals.items()))),
        dict(reversed(list(reader_outputs.items()))),
        list(reversed(display_maps)),
        n_perm=20,
        seed=UNIT_SEED,
    )
    assert canonical_json(base) == canonical_json(reordered)
    reader_outputs["rB1"]["items"][0]["left"]["letters"].append(
        {"ch": "A", "x": 1.0, "y": 1.0, "box": [0, 0, 2, 2], "conf": "firm"}
    )
    changed = score_decision(declaration, seals, reader_outputs, display_maps, n_perm=20, seed=UNIT_SEED)
    assert changed["input_sha256"] != base["input_sha256"]


def test_malformed_reader_is_not_repaired(decision):
    declaration, seals, reader_outputs, display_maps = copy.deepcopy(decision)
    reader_outputs["rA1"]["items"][0]["left"]["letters"][0]["conf"] = "maybe"
    with pytest.raises(ValueError, match="rA1"):
        score_decision(declaration, seals, reader_outputs, display_maps, n_perm=20, seed=UNIT_SEED)


def test_discarded_reader_and_missing_item(decision):
    declaration, seals, reader_outputs, display_maps = copy.deepcopy(decision)
    del reader_outputs["rA3"]  # discarded by the caller
    reader_outputs["rA2"]["items"] = [it for it in reader_outputs["rA2"]["items"] if not it["id"].endswith("item1")]
    res = score_decision(declaration, seals, reader_outputs, display_maps, n_perm=50, seed=UNIT_SEED)
    arm = res["arms"]["A"]
    assert arm["readers_missing"] == ["rA3"]
    assert arm["readers_scored"] == ["rA1", "rA2"]
    assert arm["missing_items"] == [["rA2", "w2"]]
    assert res["readers"]["rA3"]["status"] == "missing"
    rec = res["windows"]["w2"]["readers"]["rA2"]
    assert rec["status"] == "missing_item" and rec["C_all"]["R250"] == 0 and rec["C_net"] == 0
    # Mean over the two scored readers: w1 contributes S, w2 contributes S/2.
    assert arm["summed_mean_C_all"]["R250"] == pytest.approx(S + S / 2)


def test_item_without_display_map_raises(decision):
    declaration, seals, reader_outputs, display_maps = copy.deepcopy(decision)
    display_maps = [dm for dm in display_maps if dm.item_id != "rB2-item0"]
    with pytest.raises(ValueError, match="display map"):
        score_decision(declaration, seals, reader_outputs, display_maps, n_perm=20, seed=UNIT_SEED)


def test_missing_seal_raises(decision):
    declaration, seals, reader_outputs, display_maps = copy.deepcopy(decision)
    del seals["w2"]
    with pytest.raises(ValueError, match="seal"):
        score_decision(declaration, seals, reader_outputs, display_maps, n_perm=20, seed=UNIT_SEED)


def test_shifted_reader_end_to_end():
    # Sparse seal (letters 1000 px apart): shifts of 200 px match at R=250 only; 260 px never.
    rng = np.random.default_rng(8)
    seal = synthetic_seal(rng, 12, spacing=1000.0, per_row=4)
    decl = {
        "decision_id": "D-shift",
        "arms": [{"arm_id": a, "readers": [a], "windows": ["w"]} for a in ("s200", "s260")],
    }
    dms, outs = [], {}
    for rid, shift in (("s200", 200.0), ("s260", 260.0)):
        dm = DisplayMap(reader_id=rid, item_id="i", window_id="w", scale=2.0, y0=0.0, x0=0.0,
                        side_order=("text", "nontext"))
        dms.append(dm)
        outs[rid] = {"items": [reader_item("i", dm, perfect_text_letters(seal, shift=(shift * 0.6, shift * 0.8)))]}
    res = score_decision(decl, {"w": seal}, outs, dms, n_perm=50, seed=3)
    r200 = res["windows"]["w"]["readers"]["s200"]
    r260 = res["windows"]["w"]["readers"]["s260"]
    assert r200["C_all"] == {"R150": 0, "R250": 12}
    assert r260["C_all"] == {"R150": 0, "R250": 0}


def test_random_readers_null_calibration():
    """200 simulated random readers: mean C_net ~ 0 and p roughly uniform."""
    rng = np.random.default_rng(4242)
    n_readers = 200
    decl = {"decision_id": "D-null", "arms": []}
    seals, outs, dms = {}, {}, []
    for i in range(n_readers):
        rid, wid = f"r{i:03d}", f"w{i:03d}"
        seals[wid] = synthetic_seal(rng, 40, spacing=100.0, per_row=8)
        dm = DisplayMap(reader_id=rid, item_id="i", window_id=wid, scale=1.0, y0=0.0, x0=0.0,
                        side_order=("text", "nontext") if i % 2 else ("nontext", "text"))
        dms.append(dm)
        outs[rid] = {"items": [reader_item("i", dm, random_text_letters(rng, seals[wid]))]}
        decl["arms"].append({"arm_id": rid, "readers": [rid], "windows": [wid]})
    res = score_decision(decl, seals, outs, dms, n_perm=UNIT_N_PERM, seed=99)
    cnet = np.array([res["arms"][f"r{i:03d}"]["summed_mean_C_net"] for i in range(n_readers)])
    p = np.array([res["arms"][f"r{i:03d}"]["p"] for i in range(n_readers)])
    se = cnet.std(ddof=1) / np.sqrt(n_readers)
    assert abs(cnet.mean()) < 4 * se
    assert 0.01 <= (p < 0.05).mean() <= 0.12
    # C_all is discrete and p counts ties as >= (conservative), so P(p < 0.5) sits below 0.5
    # (about 0.40 in larger simulations); the bound only guards against gross miscalibration.
    assert 0.25 <= (p < 0.5).mean() <= 0.60
    assert res["decision"]["p_max"] >= p.min()


def test_tiles_of_one_window_are_pooled_with_builder_style_keys():
    """Two overlapping tiles (own offsets, own side order) of one window, builder-style keys.

    The reader names every seal letter it can see in each tile, so letters in the overlap
    are named twice; one-to-one matching still counts each seal letter once.
    """
    rng = np.random.default_rng(31)
    seal = synthetic_seal(rng, 20, spacing=100.0, per_row=10, origin=(0.0, 0.0))
    tiles = [
        # builder key format: side_order as a mapping, extra fields ignored by the scorer
        {"window_id": "w", "scale": 2.0, "y0": 0.0, "x0": 0.0, "layout": "D1Q", "px_per_mm_image": 1.0,
         "side_order": {"left": "text", "right": "nontext"}},
        {"window_id": "w", "scale": 2.0, "y0": 0.0, "x0": 450.0, "layout": "D1Q", "px_per_mm_image": 1.0,
         "side_order": {"left": "nontext", "right": "text"}},
    ]
    dms, items = [], []
    for k, key in enumerate(tiles):
        dm = DisplayMap.from_dict(key, reader_id="r", item_id=f"tile{k}")
        dms.append(dm)
        x_lo, x_hi = key["x0"], key["x0"] + 600.0
        visible = [l for l in perfect_text_letters(seal) if x_lo <= l[1] < x_hi]
        items.append(reader_item(dm.item_id, dm, visible, [("\u039F", key["x0"] + 10.0, 5.0)]))
    n_named = sum(len(it["left"]["letters"]) + len(it["right"]["letters"]) for it in items) - 2
    assert n_named > 20  # overlap: some letters named twice
    decl = {"decision_id": "D-tiles", "arms": [{"arm_id": "A", "readers": ["r"], "windows": ["w"]}]}
    res = score_decision(decl, {"w": seal}, {"r": {"items": items}}, dms, n_perm=50, seed=5)
    rec = res["windows"]["w"]["readers"]["r"]
    assert [it["item_id"] for it in rec["items"]] == ["tile0", "tile1"]
    assert [it["side_order"] for it in rec["items"]] == [["text", "nontext"], ["nontext", "text"]]
    assert rec["n_named"] == n_named
    assert rec["C_all"]["R250"] == 20
    assert rec["F_B"] == 2
