# Provenance: Project HERCULES | owner the owner | [id removed]
"""Every window-pipeline file carries the provenance line and no invisible
(Cf) characters. JSON outputs carry it as their first key."""

import json
import unicodedata
from pathlib import Path

import pytest

PROVENANCE = "Provenance: Project HERCULES | owner the owner | [id removed]"
ROOT = Path(__file__).resolve().parents[1]
CODE = sorted(list((ROOT / "src" / "hercules" / "pipeline").glob("*.py"))
              + list((ROOT / "tests").glob("test_pipeline_*.py")))
JSONS = sorted((ROOT / "logs" / "pipeline").glob("*.json"))


def test_file_list_nonempty():
    assert len(CODE) >= 8


@pytest.mark.parametrize("path", CODE, ids=lambda p: p.name)
def test_provenance_first_line(path):
    assert PROVENANCE in path.read_text(encoding="utf-8").splitlines()[0]


@pytest.mark.parametrize("path", CODE + JSONS, ids=lambda p: p.name)
def test_no_format_characters(path):
    text = path.read_text(encoding="utf-8")
    assert [hex(ord(c)) for c in text if unicodedata.category(c) == "Cf"] == []


@pytest.mark.parametrize("path", JSONS, ids=lambda p: p.name)
def test_json_provenance_first_key(path):
    d = json.loads(path.read_text(encoding="utf-8"))
    assert next(iter(d)) == "provenance" and d["provenance"] in PROVENANCE
