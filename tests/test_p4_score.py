# Provenance: Project HERCULES | owner the owner | [id removed]
import importlib.util
import os

_spec = importlib.util.spec_from_file_location('score_p4', os.path.join(os.path.dirname(__file__), '..', 'tools', 'p4', 'score_p4.py'))
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)


def _t(strip, r, c, rows='Y', n=6):
    return {'strip': strip, 'r': r, 'c': c, 'rows': rows, 'n_letters': n}


def test_clusters_4_connected():
    comps = S.clusters({(0, 0), (0, 1), (1, 1), (3, 3), (4, 4)})
    assert sorted(len(c) for c in comps) == [1, 1, 3]


def test_threshold_and_rows():
    census = {'a': _t('w010-027', 0, 0, 'Y', 5), 'b': _t('w010-027', 0, 2, 'N', 9), 'c': _t('w010-027', 0, 4, 'Y', 4)}
    pos, cand = S.candidates(census, 3.0, {})
    assert pos == ['a'] and cand == ['a']
    pos, cand = S.candidates(census, 5.5, {})
    assert pos == [] and cand == []


def test_inner_strip_all_positive_are_candidates_outer_only_small_clusters():
    census = {}
    for i in range(6):
        census[f'big{i}'] = _t('w028-037', 0, i, 'Y', 10)
    census['small'] = _t('w028-037', 5, 5, 'Y', 7)
    census['inner'] = _t('w010-027', 9, 9, 'Y', 6)
    pos, cand = S.candidates(census, 0.0, {})
    assert set(cand) == {'small', 'inner'}
    assert cand[0] == 'small'


def test_labelled_adjacent_excluded_and_cap():
    census = {f'u{i:02d}': _t('w010-027', 0, 2 * i, 'Y', 30 - i) for i in range(25)}
    pos, cand = S.candidates(census, 0.0, {'u00': True})
    assert 'u00' not in cand and len(cand) == 20 and cand[0] == 'u01'


def test_tile_answer_left_only():
    items = [{'id': 'x', 'left': {'rows': 'Y', 'letters': [{'ch': 'Α', 'conf': 'firm'}, {'ch': 'Ο', 'conf': 'tentative'}]},
              'right': {'rows': 'N', 'letters': []}}]
    assert S.tile_answer(items, 'x') == ('Y', 2, 1, False)
    assert S.tile_answer(items, 'y') is None


def test_segment_prefixed_inner_strip_name_uses_every_positive_rule():
    census = {f'big{i}': _t('20260623142658-w028-037', 0, i, 'Y', 10) for i in range(6)}
    census['inner'] = _t('20260623141924-w010-027', 3, 3, 'Y', 6)
    census['inner2'] = _t('20260623141924-w010-027', 3, 4, 'Y', 7)
    census['inner3'] = _t('20260623141924-w010-027', 4, 3, 'Y', 7)
    census['inner4'] = _t('20260623141924-w010-027', 4, 4, 'Y', 7)
    census['inner5'] = _t('20260623141924-w010-027', 5, 4, 'Y', 7)
    pos, cand = S.candidates(census, 0.0, {})
    assert {'inner', 'inner2', 'inner3', 'inner4', 'inner5'} <= set(cand)
    assert not any(c.startswith('big') for c in cand)
