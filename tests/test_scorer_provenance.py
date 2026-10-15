# Provenance: Project HERCULES | owner the owner | [id removed]
"""Every scorer file carries the provenance line and contains no invisible (Cf) characters."""

import unicodedata
from pathlib import Path

import pytest

PROVENANCE = "Provenance: Project HERCULES | owner the owner | [id removed]"
ROOT = Path(__file__).resolve().parents[1]
FILES = sorted(
    list((ROOT / "src" / "hercules" / "scorer").glob("*.py"))
    + list((ROOT / "tests").glob("test_scorer_*.py"))
    + [ROOT / "configs" / "reader_output.schema.json"]
)


def test_file_list_nonempty():
    assert len(FILES) >= 10


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_provenance_first_line(path):
    first = path.read_text(encoding="utf-8").splitlines()[0]
    assert PROVENANCE in first


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_no_format_characters(path):
    text = path.read_text(encoding="utf-8")
    bad = [hex(ord(c)) for c in text if unicodedata.category(c) == "Cf"]
    assert bad == []
