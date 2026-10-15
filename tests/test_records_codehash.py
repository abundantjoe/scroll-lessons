"""Tests for hercules.records.codehash (metric-code hashing).

Provenance: Project HERCULES | owner the owner | [id removed]
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from hercules.records import codehash

SRC = Path(__file__).resolve().parents[1] / "src"


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "pkg").mkdir()
    files = {"pkg/b.py": b"print('b')\n", "pkg/a.py": b"print('a')\n", "z.txt": b"zz"}
    for rel, data in files.items():
        (tmp_path / rel).write_bytes(data)
    return tmp_path, files


def expected_combined(files: dict[str, bytes]) -> str:
    lines = "".join(f"{p}\t{hashlib.sha256(files[p]).hexdigest()}\n" for p in sorted(files))
    return hashlib.sha256(lines.encode()).hexdigest()


def test_per_file_and_combined(tree):
    root, files = tree
    pairs, combined = codehash.hash_paths([str(root / p) for p in files], root=str(root))
    assert pairs == sorted((p, hashlib.sha256(d).hexdigest()) for p, d in files.items())
    assert combined == expected_combined(files)


def test_order_and_spelling_independent(tree, monkeypatch):
    root, files = tree
    _, c1 = codehash.hash_paths([str(root / p) for p in files], root=str(root))
    monkeypatch.chdir(root / "pkg")
    _, c2 = codehash.hash_paths(["../z.txt", "b.py", "./a.py", "a.py"], root=str(root))
    assert c1 == c2


def test_content_change_changes_combined(tree):
    root, files = tree
    paths = [str(root / p) for p in files]
    _, before = codehash.hash_paths(paths, root=str(root))
    (root / "pkg/a.py").write_bytes(b"print('A')\n")
    _, after = codehash.hash_paths(paths, root=str(root))
    assert before != after


def test_rejects_directory_and_missing(tree):
    root, _ = tree
    with pytest.raises(ValueError, match="not a regular file"):
        codehash.hash_paths([str(root / "pkg")], root=str(root))
    with pytest.raises(ValueError, match="not a regular file"):
        codehash.hash_paths([str(root / "nope.py")], root=str(root))


def test_cli_output(tree):
    root, files = tree
    env = dict(os.environ, PYTHONPATH=str(SRC))
    proc = subprocess.run(
        [sys.executable, "-m", "hercules.records.codehash", "--root", str(root),
         *(str(root / p) for p in files)],
        capture_output=True, text=True, env=env, check=True)
    lines = proc.stdout.splitlines()
    assert lines[:-1] == [f"{hashlib.sha256(files[p]).hexdigest()}  {p}" for p in sorted(files)]
    assert lines[-1] == f"combined_sha256 {expected_combined(files)}"
    bad = subprocess.run([sys.executable, "-m", "hercules.records.codehash", str(root)],
                         capture_output=True, text=True, env=env)
    assert bad.returncode == 2
