# Provenance: Project HERCULES | owner the owner | [id removed]
"""Tests for spec J: canonical JSON and age-based seal tooling (throwaway keys only)."""

import hashlib
import json
import os
import shutil
import stat

import pytest

from hercules.scorer.canon import canonical_bytes, canonical_json
from hercules.scorer.seal import keygen, seal_decrypt, seal_encrypt

needs_age = pytest.mark.skipif(
    shutil.which("age") is None or shutil.which("age-keygen") is None, reason="age not installed"
)

SEAL_OBJ = {
    "window_id": "w-01",
    "blank": False,
    "letters": [
        {"ch": "\u0391", "x": 10.5, "y": 20.0, "firm": True},
        {"ch": "\u03F9", "x": 100.0, "y": 20.25, "firm": False},
    ],
}


def test_canonical_json_sorted_compact_utf8():
    s = canonical_json({"b": 1, "a": ["\u0391", 2.5]})
    assert s == '{"a":["\u0391",2.5],"b":1}'
    assert canonical_bytes({"b": 1, "a": ["\u0391", 2.5]}) == s.encode("utf-8")


def test_canonical_json_insertion_order_invariant():
    a = {"x": {"q": 1, "p": 2}, "y": [3, {"k": 1, "j": 2}]}
    b = {"y": [3, {"j": 2, "k": 1}], "x": {"p": 2, "q": 1}}
    assert canonical_json(a) == canonical_json(b)


@pytest.mark.parametrize(
    "obj",
    [
        {"a": "x\u200By"},  # zero-width space (written as an escape here)
        {"a\u2060": 1},  # word joiner in a key
        ["\uFEFF"],  # BOM
        {"a": float("nan")},
        {"a": float("inf")},
    ],
)
def test_canonical_json_rejects_format_chars_and_nonfinite(obj):
    with pytest.raises(ValueError):
        canonical_json(obj)


@needs_age
def test_keygen_permissions_and_pubkey(tmp_path):
    key = tmp_path / "throwaway.agekey"
    pub = keygen(key)
    assert pub.startswith("age1") and len(pub) == 62
    assert stat.S_IMODE(os.stat(key).st_mode) == 0o400
    with pytest.raises(FileExistsError):
        keygen(key)


@needs_age
def test_seal_round_trip(tmp_path):
    key = tmp_path / "throwaway.agekey"
    pub = keygen(key)
    out = tmp_path / "w-01.seal.age"
    digest = seal_encrypt(SEAL_OBJ, pub, out)
    data = out.read_bytes()
    assert digest == hashlib.sha256(data).hexdigest()
    assert b"\xce\x91" not in data and b"letters" not in data  # ciphertext does not leak plaintext
    assert seal_decrypt(out, key) == json.loads(canonical_json(SEAL_OBJ))
    assert seal_decrypt(out, key) == SEAL_OBJ


@needs_age
def test_seal_refuses_overwrite_and_bad_inputs(tmp_path):
    key = tmp_path / "throwaway.agekey"
    pub = keygen(key)
    out = tmp_path / "s.age"
    seal_encrypt(SEAL_OBJ, pub, out)
    with pytest.raises(FileExistsError):
        seal_encrypt(SEAL_OBJ, pub, out)
    with pytest.raises(ValueError):
        seal_encrypt(SEAL_OBJ, "not-a-key", tmp_path / "t.age")
    with pytest.raises(ValueError):
        seal_encrypt({"a": "x\u200By"}, pub, tmp_path / "u.age")
    assert not (tmp_path / "u.age").exists()
    assert not (tmp_path / "t.age").exists()


@needs_age
def test_decrypt_with_wrong_key_fails(tmp_path):
    k1, k2 = tmp_path / "k1.agekey", tmp_path / "k2.agekey"
    pub1 = keygen(k1)
    keygen(k2)
    out = tmp_path / "s.age"
    seal_encrypt(SEAL_OBJ, pub1, out)
    with pytest.raises(RuntimeError):
        seal_decrypt(out, k2)


@needs_age
def test_ciphertext_is_randomised_but_plaintext_stable(tmp_path):
    key = tmp_path / "k.agekey"
    pub = keygen(key)
    d1 = seal_encrypt(SEAL_OBJ, pub, tmp_path / "a.age")
    d2 = seal_encrypt(dict(reversed(list(SEAL_OBJ.items()))), pub, tmp_path / "b.age")
    assert d1 != d2  # age uses a fresh file key each time
    assert seal_decrypt(tmp_path / "a.age", key) == seal_decrypt(tmp_path / "b.age", key)
