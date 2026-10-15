"""Provenance: Project HERCULES | owner the owner | [id removed]"""
import importlib
import os
import stat


def test_logged_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("HERCULES_SEAL_KEY", str(tmp_path / "k" / "seal.agekey"))
    import hercules.scorer.keyaccess as ka
    ka = importlib.reload(ka)
    from hercules.scorer.seal import seal_encrypt
    pub = ka.ensure_key()
    assert pub.startswith("age1")
    assert stat.S_IMODE(os.stat(ka.KEY_PATH).st_mode) == 0o400
    p = tmp_path / "s.age"
    seal_encrypt({"window_id": "W", "blank": False, "letters": []}, pub, p)
    log = tmp_path / "reads.tsv"
    obj = ka.decrypt_logged(str(p), "unit-test", log_path=str(log))
    assert obj["window_id"] == "W"
    lines = log.read_text().splitlines()
    assert len(lines) == 2 and "unit-test" in lines[1]
