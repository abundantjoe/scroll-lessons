# Provenance: Project HERCULES | owner the owner | [id removed]
"""Synthetic end-to-end test of tools/d1/score_d1.py (both stages) with redirected paths and crypto."""
import importlib.util
import json
import os

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    spec = importlib.util.spec_from_file_location("score_d1", os.path.join(HERE, "tools", "d1", "score_d1.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _px(v):  # canvas px -> D2 image px (half-pixel convention, scale 2)
    return (v + 0.5) / 2 - 0.5


def _l(ch, cx, cy):
    x, y = _px(cx), _px(cy)
    return {"ch": ch, "x": x, "y": y, "box": [x - 20, y - 20, x + 20, y + 20], "conf": "firm"}


SEAL = {"windows": {
    "J1": {"blank": False, "letters": [{"ch": "Κ", "x": 200.0, "y": 400.0, "firm": True},
                                       {"ch": "Α", "x": 1000.0, "y": 1000.0, "firm": True}]},
    "J2": {"blank": False, "letters": [{"ch": "Ο", "x": 500.0, "y": 500.0, "firm": False}]},
    "J3": {"blank": False, "letters": [{"ch": "Ν", "x": 300.0, "y": 300.0, "firm": False}]},
    "B1": {"blank": True, "letters": []}, "B2": {"blank": True, "letters": []}}}
WINS = {"J1": {"set": "J", "gate": {"pass": True}}, "J2": {"set": "J", "gate": {"pass": True}},
        "J3": {"set": "J", "gate": {"pass": False}}, "B1": {"set": "blank", "gate": {"pass": None}},
        "B2": {"set": "blank", "gate": {"pass": None}}, "CAN": {"set": "canary", "gate": {"pass": None}}}


@pytest.fixture
def env(tmp_path, monkeypatch):
    m = _load()
    for name, sub in (("D1", "d1"), ("SCORER", "scorer"), ("JOBS", "jobs"), ("SEALED", "sealed"), ("LOGS", "logs")):
        d = tmp_path / sub
        d.mkdir()
        monkeypatch.setattr(m, name, str(d))
    monkeypatch.setattr(m, "SEAL_PATH", str(tmp_path / "seal.age"))
    monkeypatch.setattr(m, "N_PERM", 200)
    (tmp_path / "scorer" / "seal.agekey.pub").write_text("age1test")
    answers = {}
    monkeypatch.setattr(m, "decrypt_logged", lambda path, purpose: SEAL)
    monkeypatch.setattr(m, "load_answer", lambda path, purpose: answers[os.path.basename(path)[:-4]])
    monkeypatch.setattr(m, "seal_encrypt", lambda obj, rcpt, out: "sha-test")
    return m, tmp_path, answers


def _write(tmp, stage, images, items, jobs, answers_by_job, answers):
    key = {"images": images, "windows": WINS}
    (tmp / "scorer" / "d1_key.json").write_text(json.dumps(key))
    (tmp / "scorer" / f"d1_items_{stage}.json").write_text(json.dumps(items))
    (tmp / "d1" / f"jobs_{stage}.json").write_text(json.dumps({"stage": stage, "gated_J": ["J1", "J2"], "jobs": jobs}))
    for j in jobs:
        (tmp / "jobs" / f"{j['job']}.json").write_text(json.dumps({"valid": True}))
    answers.update(answers_by_job)


def _item(iid, left, right=None):
    return {"id": iid, "left": {"rows": "Y" if left else "N", "letters": left},
            "right": {"rows": "Y" if right else "N", "letters": right or []}}


def test_ref_stage(env):
    m, tmp, answers = env
    images, items, jobs, ans = {}, {}, [], {}
    for arm in ("REF0", "REF015", "REF030", "REF045"):
        for w in ("J1", "J2", "B1", "B2", "CAN"):
            images[f"{arm}_{w}"] = {"window": w, "kind": arm, "order": "single", "state": "A"}
        for r in range(3):
            job = f"job_{arm}_{r}"
            b = "B1" if r % 2 == 0 else "B2"
            items[job] = {f"{arm}_J1": {"left": f"{arm}_J1", "right": None, "scored_window": "J1", "role": "window"},
                          f"{arm}_J2": {"left": f"{arm}_J2", "right": None, "scored_window": "J2", "role": "window"},
                          f"{arm}_CAN": {"left": f"{arm}_CAN", "right": None, "scored_window": "CAN", "role": "canary"},
                          f"{arm}_{b}": {"left": f"{arm}_{b}", "right": None, "scored_window": b, "role": "blank"}}
            jobs.append({"arm": arm, "reader": r, "job": job})
            good = arm in ("REF0", "REF015")
            ans[job] = {"items": [
                _item(f"{arm}_J1", [_l("Κ", 200, 400), _l("Α", 1000, 1000)] if good else []),
                _item(f"{arm}_J2", [_l("Ο", 500, 500)] if (good and arm == "REF0") else []),
                _item(f"{arm}_CAN", [_l("Τ", 50, 50)]),
                _item(f"{arm}_{b}", [])]}
    _write(tmp, "ref", images, items, jobs, ans, answers)
    m.main("ref")
    s = json.load(open(tmp / "logs" / "d1_ref_summary.json"))
    assert s["S_prime_gated"] == 3  # J3 failed the gate
    assert s["arms"]["REF0"]["summed_mean_C_all_R250"] == 3.0
    assert s["arms"]["REF015"]["summed_mean_C_all_R250"] == 2.0
    assert s["arms"]["REF030"]["summed_mean_C_all_R250"] == 0.0
    assert s["void"] is False
    assert s["sigma_crit_mm"] == 0.15
    assert s["arms"]["REF0"]["blank_namings_mean"] == 0.0
    assert s["canary_and_foreign"]["REF0_r0"] == {"canary_namings": 1, "foreign_items": 0}
    assert s["discarded"] == [] and s["full_results_sha256"] == "sha-test"


def test_model_stage_state_b_text_order_and_chance(env):
    m, tmp, answers = env
    images, items, jobs, ans = {}, {}, [], {}
    for st in ("A", "B"):
        for w in ("J1", "J2", "B1", "B2", "CAN"):
            for kind, orders in (("BASE", ("fwd", "rev")), ("RAW", ("F", "B"))):
                for o in orders:
                    images[f"{kind}_{o}_{st}_{w}"] = {"window": w, "kind": kind, "order": o, "state": st}
    nxt = {"J1": "J2", "J2": "J1"}
    for arm in ("BASE-A", "BASE-B", "RAW-A", "RAW-B", "CHANCE-A", "CHANCE-B"):
        kind, st = arm.split("-")
        k = "BASE" if kind == "CHANCE" else kind
        o_text, o_non = ("fwd", "rev") if k == "BASE" else ("F", "B")
        for r in range(3):
            job = f"job_{arm}_{r}"
            b = "B1" if r % 2 == 0 else "B2"
            its, al = {}, []
            for w, role in (("J1", "window"), ("J2", "window"), ("CAN", "canary"), (b, "blank")):
                src = nxt[w] if (kind == "CHANCE" and role == "window") else w
                iid = f"{arm}_{r}_{w}"
                # text panel on the RIGHT for this item, to exercise side handling
                its[iid] = {"left": f"{k}_{o_non}_{st}_{src}", "right": f"{k}_{o_text}_{st}_{src}", "scored_window": w, "role": role}
                letters = []
                if arm == "BASE-B" and w == "J1":  # correct letters in the state-B (mirrored) frame
                    letters = [_l("Κ", 2135 - 200, 400), _l("Α", 2135 - 1000, 1000)]
                if arm == "BASE-A" and w == "J1":  # same canvas positions but in the A frame on the non-text panel -> F_B
                    al.append(_item(iid, [_l("Κ", 200, 400)], right=[]))
                    continue
                al.append(_item(iid, [], right=letters))
            items[job] = its
            jobs.append({"arm": arm, "reader": r, "job": job})
            ans[job] = {"items": al}
    _write(tmp, "model", images, items, jobs, ans, answers)
    m.main("model", "fwd", "F")
    s = json.load(open(tmp / "logs" / "d1_model_summary.json"))
    fa = s["family_arms"]
    assert fa["BASE-B"]["summed_mean_C_all_R250"] == 2.0
    assert fa["BASE-A"]["summed_mean_C_all_R250"] == 0.0 and fa["BASE-A"]["F_B_mean_per_reader"] == 1.0
    assert s["best_family_arm"] == "BASE-B"
    assert s["chance_arms"]["CHANCE-B"]["summed_mean_C_all_R250"] == 0.0
    assert s["S_prime_gated"] == 3
    assert s["outcome"] == {"outcome": "VOID", "reason": "S' < 20"}  # synthetic seal is small; bars tested in d1drive
