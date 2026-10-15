# Provenance: Project HERCULES | owner the owner | [id removed]
"""Synthetic end-to-end test of tools/d1/score_d3.py with redirected paths and crypto.

The seal needs enough distinct letters per window that the identity permutation (which reproduces
the observed count) is rare; with 6 and 5 letters it has probability 1/86400, so p_max can reach 1/201."""
import importlib.util
import json
import os

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    spec = importlib.util.spec_from_file_location("score_d3", os.path.join(HERE, "tools", "d1", "score_d3.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _px(v):
    return (v + 0.5) / 2 - 0.5


def _l(ch, cx, cy):
    x, y = _px(cx), _px(cy)
    return {"ch": ch, "x": x, "y": y, "box": [x - 20, y - 20, x + 20, y + 20], "conf": "firm"}


J1 = [("Κ", 200.0, 400.0), ("Α", 1000.0, 1000.0), ("Ρ", 1500.0, 300.0), ("Ε", 400.0, 1800.0),
      ("Τ", 1800.0, 1000.0), ("Μ", 700.0, 700.0)]
J2 = [("Ο", 500.0, 500.0), ("Ν", 1600.0, 1600.0), ("Λ", 300.0, 1500.0), ("Π", 1500.0, 300.0), ("Δ", 1000.0, 1000.0)]
SEAL = {"windows": {
    "J1": {"blank": False, "letters": [{"ch": c, "x": x, "y": y, "firm": True} for c, x, y in J1]},
    "J2": {"blank": False, "letters": [{"ch": c, "x": x, "y": y, "firm": True} for c, x, y in J2]},
    "B1": {"blank": True, "letters": []}, "B2": {"blank": True, "letters": []}}}
WINS = {"J1": {"set": "J", "gate": {"pass": True}}, "J2": {"set": "J", "gate": {"pass": True}},
        "B1": {"set": "blank", "gate": {"pass": None}}, "B2": {"set": "blank", "gate": {"pass": None}},
        "CAN": {"set": "canary", "gate": {"pass": None}}}


@pytest.fixture
def env(tmp_path, monkeypatch):
    m = _load()
    for name, sub in (("D3", "d3"), ("SCORER", "scorer"), ("JOBS", "jobs"), ("SEALED", "sealed"), ("LOGS", "logs")):
        (tmp_path / sub).mkdir()
        monkeypatch.setattr(m, name, str(tmp_path / sub))
    monkeypatch.setattr(m, "SEAL_PATH", str(tmp_path / "seal.age"))
    monkeypatch.setattr(m, "N_PERM", 200)
    (tmp_path / "scorer" / "seal.agekey.pub").write_text("age1test")
    answers = {}
    monkeypatch.setattr(m, "decrypt_logged", lambda path, purpose: SEAL)
    monkeypatch.setattr(m, "load_answer", lambda path, purpose: answers[os.path.basename(path)[:-4]])
    monkeypatch.setattr(m, "seal_encrypt", lambda obj, rcpt, out: "sha-test")
    return m, tmp_path, answers


def _item(iid, left, right):
    return {"id": iid, "left": {"rows": "Y" if left else "N", "letters": left},
            "right": {"rows": "Y" if right else "N", "letters": right}}


def test_fa_passes_against_silent_controls(env):
    m, tmp, answers = env
    images, items, jobs = {}, {}, []
    for arm in ("FA", "NULLA", "REVA", "CTRL"):
        for st in ("A", "B"):
            for w in ("J1", "J2", "B1", "B2", "CAN"):
                for o in ("fwd", "rev"):
                    images[f"{arm}_{st}_{w}_{o}"] = {"window": w, "arm": arm, "kind": "BASE", "order": o, "state": st}
            for r in range(3):
                job = f"job_{arm}_{st}_{r}"
                b = "B1" if r % 2 == 0 else "B2"
                its, al = {}, []
                for w, role in (("J1", "window"), ("J2", "window"), ("CAN", "canary"), (b, "blank")):
                    iid = f"{job}_{w}"
                    its[iid] = {"left": f"{arm}_{st}_{w}_rev", "right": f"{arm}_{st}_{w}_fwd", "scored_window": w, "role": role}
                    letters = []
                    if arm == "FA" and st == "A" and w in ("J1", "J2"):
                        letters = [_l(c, x, y) for c, x, y in (J1 if w == "J1" else J2)]
                    al.append(_item(iid, [], letters))  # text (fwd) panel is RIGHT
                items[job] = its
                jobs.append({"arm": f"{arm}-{st}", "reader": r, "job": job})
                answers[job] = {"items": al}
                (tmp / "jobs" / f"{job}.json").write_text(json.dumps({"valid": True}))
    (tmp / "scorer" / "d3_key.json").write_text(json.dumps({"images": images, "windows": WINS}))
    (tmp / "scorer" / "d3_items.json").write_text(json.dumps(items))
    (tmp / "d3" / "jobs_d3.json").write_text(json.dumps({"stage": "d3", "gated_J": ["J1", "J2"], "jobs": jobs}))
    blob = tmp / "blob.json"
    blob.write_text(json.dumps({"B1": 0.01, "B2": 0.02}))
    m.main(str(blob))
    s = json.load(open(tmp / "logs" / "d3_summary.json"))
    assert s["S_prime_gated"] == 11
    assert s["arms"]["FA-A"]["summed_mean_C_all_R250"] == 11.0
    assert s["arms"]["CTRL-A"]["summed_mean_C_all_R250"] == 0.0 and s["arms"]["FA-B"]["summed_mean_C_all_R250"] == 0.0
    assert s["arms"]["FA-A"]["summed_mean_C_net"] > 3.0
    assert s["outcome"]["best_fa_state"] == "A"
    assert s["outcome"]["outcome"] == "PASS", s["outcome"]
    assert s["canary_and_foreign"]["FA-A_r0"] == {"canary_namings": 0, "foreign_items": 0}


def test_blob_keys_must_match_blanks(env):
    m, tmp, answers = env
    (tmp / "scorer" / "d3_key.json").write_text(json.dumps({"images": {}, "windows": WINS}))
    (tmp / "scorer" / "d3_items.json").write_text(json.dumps({}))
    (tmp / "d3" / "jobs_d3.json").write_text(json.dumps({"stage": "d3", "gated_J": ["J1", "J2"], "jobs": []}))
    blob = tmp / "blob.json"
    blob.write_text(json.dumps({"B1": 0.01}))
    with pytest.raises(AssertionError):
        m.main(str(blob))
