# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-P4-17 block variant: schema, counting and candidate rules (METRIC-HASH-38)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'p4'))
sys.path.insert(0, os.path.join(ROOT, 'src'))

from block_schema import validate_block, validate_for_variant  # noqa: E402
from score_p4 import candidates, tile_answer, tile_answer_full  # noqa: E402

LET = {"ch": "Α", "x": 1, "y": 2, "box": [0, 0, 3, 4], "conf": "firm"}
MARK = {"kind": "dash", "x": 5, "y": 6, "box": [1, 1, 9, 9], "conf": "tentative"}


def _ans(left):
    return {"items": [{"id": "u1", "left": left, "right": {"rows": "N", "letters": []}}]}


def test_block_schema_accepts_marks_and_lines():
    ok, err = validate_block(_ans({"rows": "Y", "lines": 2, "letters": [LET], "marks": [MARK]}))
    assert ok, err


def test_block_schema_accepts_plain_answer():
    assert validate_block(_ans({"rows": "N", "letters": []}))[0]


def test_pinned_schema_still_rejects_marks():
    ok, _ = validate_for_variant(_ans({"rows": "Y", "letters": [LET], "marks": [MARK]}), 'sigma2t')
    assert not ok


def test_block_schema_rejects_bad_mark():
    bad = dict(MARK, kind="letter")
    assert not validate_block(_ans({"rows": "Y", "letters": [], "marks": [bad]}))[0]
    assert not validate_block(_ans({"rows": "Y", "lines": -1, "letters": []}))[0]
    assert not validate_block(_ans({"rows": "Y", "letters": [], "marks": [dict(MARK, x=float('nan'))]}))[0]


def test_tile_answer_full_counts_marks():
    items = _ans({"rows": "Y", "lines": 3, "letters": [LET, LET], "marks": [MARK]})["items"]
    assert tile_answer_full(items, "u1") == ("Y", 2, 2, False, 1, 3)
    assert tile_answer(items, "u1") == ("Y", 2, 2, False)


def test_candidates_block_count_and_cmin():
    cen = {
        'a': {'strip': 'w010-027', 'r': 0, 'c': 3, 'rows': 'Y', 'n_letters': 2, 'n_count': 6},
        'b': {'strip': 'w010-027', 'r': 0, 'c': 11, 'rows': 'Y', 'n_letters': 3, 'n_count': 7},
        'c': {'strip': 'w010-027', 'r': 1, 'c': 12, 'rows': 'Y', 'n_letters': 4, 'n_count': 4},
    }
    pos, cand = candidates(cen, 0.0, {}, 9)
    assert pos == ['a', 'b'] and cand == ['b']
    pos, cand = candidates(cen, 0.0, {})
    assert cand == ['b', 'a']


def test_candidates_letters_unchanged_without_count():
    cen = {'a': {'strip': 'w010-027', 'r': 0, 'c': 3, 'rows': 'Y', 'n_letters': 5},
           'b': {'strip': 'w010-027', 'r': 0, 'c': 4, 'rows': 'Y', 'n_letters': 4}}
    assert candidates(cen, 0.0, {}) == (['a'], ['a'])
