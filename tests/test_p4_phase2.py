# Provenance: Project HERCULES | owner the owner | [id removed]
import importlib.util
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools', 'p4'))
_spec = importlib.util.spec_from_file_location('p4_phase2', os.path.join(os.path.dirname(__file__), '..', 'tools', 'p4', 'p4_phase2.py'))
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)


def _r(*lets):
    return P.known_letters([{'ch': ch, 'x': x, 'y': y, 'conf': 'tentative'} for ch, x, y in lets])


def test_pair_agreement_same_kind_radius_one_to_one():
    a = _r(('Α', 100, 100), ('Α', 110, 100), ('Β', 500, 500))
    b = _r(('Α', 105, 100), ('Β', 800, 800), ('Γ', 100, 100))
    assert P.pair_agreement(a, b) == 1          # one-to-one: two A near one A -> 1; B too far; kinds differ
    assert P.pair_agreement(a, b, radius=500) == 2


def test_sigma_forms_are_one_kind():
    a = _r(('Σ', 0, 0))
    b = _r(('Ϲ', 10, 10))
    assert P.pair_agreement(a, b) == 1


def test_unknown_kinds_not_counted():
    a = _r(('?', 0, 0), ('Α', 0, 0))
    assert len(a[1]) == 1


def test_candidate_decision_rules():
    five = [('Α', 0, 0), ('Β', 200, 0), ('Γ', 400, 0), ('Δ', 600, 0), ('Ε', 800, 0)]
    r1, r2 = _r(*five), _r(*[(ch, x + 20, y) for ch, x, y in five])
    r3 = _r(('Α', 0, 0))
    d = P.candidate_decision([r1, r2, r3], n0_max=4)
    assert d['P4_CANDIDATE'] and d['best_pair_agreed'] == 5 and d['n_readers_ge5'] == 2
    d = P.candidate_decision([r1, r2, r3], n0_max=5)
    assert not d['P4_CANDIDATE'] and not d['crit_c_gt_n0max']
    d = P.candidate_decision([r1, r3, r3], n0_max=0)
    assert not d['P4_CANDIDATE'] and not d['crit_a_2of3_ge5']
    four = _r(*five[:4])
    d = P.candidate_decision([r1, _r(*[(ch, x + 20, y) for ch, x, y in five[:4]] + [('Ω', 900, 900)]), four], n0_max=0)
    assert d['best_pair_agreed'] == 4 and not d['crit_b_agree_ge5']


def test_n0_best_pair_uses_all_pairs_without_letter_filter():
    a, b = _r(('Ο', 0, 0), ('Ι', 50, 0)), _r(('Ο', 5, 0), ('Ι', 55, 0))
    assert P.best_pair([a, b]) == 2
    assert P.best_pair([a, b], min_letters=5) == 0


def test_n0_count_rule():
    import math
    assert [P.GROUP * math.ceil(n / P.GROUP) for n in (1, 4, 5, 20)] == [4, 4, 8, 20]
