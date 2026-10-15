# Provenance: Project HERCULES | owner the owner | [id removed]
"""Spec B: normalisation of named characters to the Greek capital letter kinds.

All non-ASCII characters in this file are written as escapes so that Greek and Latin
look-alikes can be audited unambiguously.  The only canonical sigma is the capital lunate
sigma U+03F9, as written in the papyri.
"""

from __future__ import annotations

import unicodedata
from types import MappingProxyType

from .constants import INPUT_UNICODE_FORM

# The 24 canonical kinds, in Greek alphabetical order (lunate sigma in sigma's place).
CANONICAL_KINDS: tuple[str, ...] = (
    "\u0391",  # GREEK CAPITAL LETTER ALPHA
    "\u0392",  # GREEK CAPITAL LETTER BETA
    "\u0393",  # GREEK CAPITAL LETTER GAMMA
    "\u0394",  # GREEK CAPITAL LETTER DELTA
    "\u0395",  # GREEK CAPITAL LETTER EPSILON
    "\u0396",  # GREEK CAPITAL LETTER ZETA
    "\u0397",  # GREEK CAPITAL LETTER ETA
    "\u0398",  # GREEK CAPITAL LETTER THETA
    "\u0399",  # GREEK CAPITAL LETTER IOTA
    "\u039A",  # GREEK CAPITAL LETTER KAPPA
    "\u039B",  # GREEK CAPITAL LETTER LAMDA
    "\u039C",  # GREEK CAPITAL LETTER MU
    "\u039D",  # GREEK CAPITAL LETTER NU
    "\u039E",  # GREEK CAPITAL LETTER XI
    "\u039F",  # GREEK CAPITAL LETTER OMICRON
    "\u03A0",  # GREEK CAPITAL LETTER PI
    "\u03A1",  # GREEK CAPITAL LETTER RHO
    "\u03F9",  # GREEK CAPITAL LUNATE SIGMA SYMBOL
    "\u03A4",  # GREEK CAPITAL LETTER TAU
    "\u03A5",  # GREEK CAPITAL LETTER UPSILON
    "\u03A6",  # GREEK CAPITAL LETTER PHI
    "\u03A7",  # GREEK CAPITAL LETTER CHI
    "\u03A8",  # GREEK CAPITAL LETTER PSI
    "\u03A9",  # GREEK CAPITAL LETTER OMEGA
)

LUNATE_SIGMA = "\u03F9"

# Integer code of each kind (index into CANONICAL_KINDS); used for vectorised matching.
KIND_INDEX = MappingProxyType({k: i for i, k in enumerate(CANONICAL_KINDS)})

# Source character (after NFC) -> canonical kind.  Anything not listed maps to None.
LETTER_TABLE = MappingProxyType(
    {
        # --- Greek capitals map to themselves
        "\u0391": "\u0391",  # ALPHA
        "\u0392": "\u0392",  # BETA
        "\u0393": "\u0393",  # GAMMA
        "\u0394": "\u0394",  # DELTA
        "\u0395": "\u0395",  # EPSILON
        "\u0396": "\u0396",  # ZETA
        "\u0397": "\u0397",  # ETA
        "\u0398": "\u0398",  # THETA
        "\u0399": "\u0399",  # IOTA
        "\u039A": "\u039A",  # KAPPA
        "\u039B": "\u039B",  # LAMDA
        "\u039C": "\u039C",  # MU
        "\u039D": "\u039D",  # NU
        "\u039E": "\u039E",  # XI
        "\u039F": "\u039F",  # OMICRON
        "\u03A0": "\u03A0",  # PI
        "\u03A1": "\u03A1",  # RHO
        "\u03A4": "\u03A4",  # TAU
        "\u03A5": "\u03A5",  # UPSILON
        "\u03A6": "\u03A6",  # PHI
        "\u03A7": "\u03A7",  # CHI
        "\u03A8": "\u03A8",  # PSI
        "\u03A9": "\u03A9",  # OMEGA
        # --- every sigma form -> capital lunate sigma
        "\u03F9": "\u03F9",  # CAPITAL LUNATE SIGMA SYMBOL
        "\u03A3": "\u03F9",  # CAPITAL SIGMA
        "\u03C3": "\u03F9",  # SMALL SIGMA
        "\u03C2": "\u03F9",  # SMALL FINAL SIGMA
        "\u03F2": "\u03F9",  # SMALL LUNATE SIGMA SYMBOL
        "C": "\u03F9",  # LATIN CAPITAL C
        "c": "\u03F9",  # LATIN SMALL C
        # --- Greek lowercase -> capital
        "\u03B1": "\u0391",  # alpha
        "\u03B2": "\u0392",  # beta
        "\u03B3": "\u0393",  # gamma
        "\u03B4": "\u0394",  # delta
        "\u03B5": "\u0395",  # epsilon
        "\u03B6": "\u0396",  # zeta
        "\u03B7": "\u0397",  # eta
        "\u03B8": "\u0398",  # theta
        "\u03B9": "\u0399",  # iota
        "\u03BA": "\u039A",  # kappa
        "\u03BB": "\u039B",  # lamda
        "\u03BC": "\u039C",  # mu
        "\u03BD": "\u039D",  # nu
        "\u03BE": "\u039E",  # xi
        "\u03BF": "\u039F",  # omicron
        "\u03C0": "\u03A0",  # pi
        "\u03C1": "\u03A1",  # rho
        "\u03C4": "\u03A4",  # tau
        "\u03C5": "\u03A5",  # upsilon
        "\u03C6": "\u03A6",  # phi
        "\u03C7": "\u03A7",  # chi
        "\u03C8": "\u03A8",  # psi
        "\u03C9": "\u03A9",  # omega
        # --- Latin capital look-alikes (spec B lists capitals only)
        "A": "\u0391",  # ALPHA
        "B": "\u0392",  # BETA
        "E": "\u0395",  # EPSILON
        "Z": "\u0396",  # ZETA
        "H": "\u0397",  # ETA
        "I": "\u0399",  # IOTA
        "K": "\u039A",  # KAPPA
        "M": "\u039C",  # MU
        "N": "\u039D",  # NU
        "O": "\u039F",  # OMICRON
        "P": "\u03A1",  # RHO
        "T": "\u03A4",  # TAU
        "Y": "\u03A5",  # UPSILON
        "X": "\u03A7",  # CHI
    }
)


def normalize_letter(ch: object) -> str | None:
    """Return the canonical kind of a named character, or None when unknown.

    The input is brought to Unicode NFC first; it is then looked up in LETTER_TABLE.
    Non-strings, empty strings, multi-character strings, accented letters and every
    character not in the table return None (counted as 'unknown', never matched).
    """
    if not isinstance(ch, str) or not ch:
        return None
    return LETTER_TABLE.get(unicodedata.normalize(INPUT_UNICODE_FORM, ch))


def kind_code(ch: object) -> int:
    """Integer code of the normalised kind of ``ch``, or -1 when unknown."""
    k = normalize_letter(ch)
    return -1 if k is None else KIND_INDEX[k]
