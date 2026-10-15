# Provenance: Project HERCULES | owner the owner | [id removed]
"""Tests for spec B: letter normalisation to the Greek capital kind set."""

import unicodedata

import pytest

from hercules.scorer.letters import CANONICAL_KINDS, LETTER_TABLE, normalize_letter

LUNATE_SIGMA = "\u03F9"  # GREEK CAPITAL LUNATE SIGMA SYMBOL


def test_canonical_kinds_are_24_greek_capitals_with_lunate_sigma():
    assert len(CANONICAL_KINDS) == 24
    assert len(set(CANONICAL_KINDS)) == 24
    assert LUNATE_SIGMA in CANONICAL_KINDS
    assert "\u03A3" not in CANONICAL_KINDS  # regular capital sigma is not canonical
    for k in CANONICAL_KINDS:
        name = unicodedata.name(k)
        assert name.startswith("GREEK CAPITAL"), name


def test_every_canonical_kind_maps_to_itself():
    for k in CANONICAL_KINDS:
        assert normalize_letter(k) == k


@pytest.mark.parametrize("ch", ["\u03A3", "\u03C3", "\u03C2", "\u03F2", "C", "c", LUNATE_SIGMA])
def test_sigma_variants_map_to_lunate_sigma(ch):
    assert normalize_letter(ch) == LUNATE_SIGMA


def test_greek_lowercase_maps_to_capital():
    for cp in range(0x03B1, 0x03CA):  # alpha .. omega (includes final sigma U+03C2)
        ch = chr(cp)
        out = normalize_letter(ch)
        assert out is not None, unicodedata.name(ch)
        assert out in CANONICAL_KINDS
        if ch in ("\u03C2", "\u03C3"):
            assert out == LUNATE_SIGMA
        else:
            assert out == ch.upper()


@pytest.mark.parametrize(
    "latin,greek_name",
    [
        ("A", "GREEK CAPITAL LETTER ALPHA"),
        ("B", "GREEK CAPITAL LETTER BETA"),
        ("E", "GREEK CAPITAL LETTER EPSILON"),
        ("Z", "GREEK CAPITAL LETTER ZETA"),
        ("H", "GREEK CAPITAL LETTER ETA"),
        ("I", "GREEK CAPITAL LETTER IOTA"),
        ("K", "GREEK CAPITAL LETTER KAPPA"),
        ("M", "GREEK CAPITAL LETTER MU"),
        ("N", "GREEK CAPITAL LETTER NU"),
        ("O", "GREEK CAPITAL LETTER OMICRON"),
        ("P", "GREEK CAPITAL LETTER RHO"),
        ("T", "GREEK CAPITAL LETTER TAU"),
        ("Y", "GREEK CAPITAL LETTER UPSILON"),
        ("X", "GREEK CAPITAL LETTER CHI"),
    ],
)
def test_latin_lookalikes(latin, greek_name):
    assert unicodedata.name(normalize_letter(latin)) == greek_name


@pytest.mark.parametrize(
    "ch",
    [
        "D", "a", "o", "x", "0", "1", "", " ", "\u0391\u0392",  # two letters
        "\u0386",  # GREEK CAPITAL LETTER ALPHA WITH TONOS (accented forms are not in the table)
        "\u03AC",  # small alpha with tonos
        "\u03DC",  # digamma
        "\u0410",  # CYRILLIC CAPITAL LETTER A
        "?", "\u200B",  # zero-width space (escape only; category Cf)
        None, 5, 1.0,
    ],
)
def test_everything_else_is_unknown(ch):
    assert normalize_letter(ch) is None


def test_decomposed_accent_is_nfc_composed_then_unknown():
    assert normalize_letter("\u0391\u0301") is None


def test_table_values_all_canonical_and_no_format_chars():
    for k, v in LETTER_TABLE.items():
        assert v in CANONICAL_KINDS
        assert len(k) == 1
        assert unicodedata.category(k) != "Cf"
