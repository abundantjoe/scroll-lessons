# Provenance: Project HERCULES | owner the owner | [id removed]
from hercules.scorer.handed import count_votes, verdict

KEY = {"i1": {"left": "A", "right": "B"}, "i2": {"left": "B", "right": "A"},
       "i3": {"left": "A", "right": "B"}, "i4": {"left": "B", "right": "A"}}


def test_all_a():
    out = {"pairs": [{"id": "i1", "normal": "LEFT"}, {"id": "i2", "normal": "RIGHT"},
                     {"id": "i3", "normal": "LEFT"}, {"id": "i4", "normal": "RIGHT"}]}
    v = count_votes([out] * 3, KEY)
    assert v == {"A": 12, "B": 0, "none": 0} and verdict(v) == ("A", 1)


def test_ambiguous_and_unsure():
    out1 = {"pairs": [{"id": "i1", "normal": "LEFT"}, {"id": "i2", "normal": "LEFT"},
                      {"id": "i3", "normal": "UNSURE"}]}
    v = count_votes([out1] * 3, KEY)
    assert v == {"A": 3, "B": 3, "none": 6} and verdict(v)[0] == "AMBIGUOUS"


def test_b_wins_at_bar():
    out = {"pairs": [{"id": "i1", "normal": "RIGHT"}, {"id": "i2", "normal": "LEFT"},
                     {"id": "i3", "normal": "RIGHT"}, {"id": "i4", "normal": "LEFT"}]}
    outs = [out, out, {"pairs": [{"id": "i1", "normal": "RIGHT"}, {"id": "i2", "normal": "LEFT"}]}]
    v = count_votes(outs, KEY)
    assert v["B"] == 10 and verdict(v) == ("B", -1)
