# Provenance: Project HERCULES | owner the owner | [id removed]
"""Synthetic tests of tools/sib/readcal2/score_rc2.py (no reader runs; synthetic seals and answers only)."""
import os
import sys
from fractions import Fraction

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, 'tools', 'sib', 'readcal2'))
sys.path.insert(0, os.path.join(REPO, 'src'))
import score_rc2 as S  # noqa: E402

LET = 'ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡϹΤΥΦΧΨΩ'


def make_seals(rng, n_win=3, n_let=8):
    seals = {}
    for i in range(n_win):
        ls = [{'ch': LET[int(rng.integers(0, 24))], 'x': float(rng.uniform(200, 1900)), 'y': float(rng.uniform(200, 1900)),
               'firm': bool(rng.random() < 0.5)} for _ in range(n_let)]
        seals[f'win{i}'] = {'blank': False, 'letters': ls}
    seals['blankA'] = {'blank': True, 'letters': []}
    return seals


def answer_for(seals, frac, rng, uuidmap, reader, blank_names=0):
    """Reader naming a fraction of each seal's letters correctly at the right place (image coords, scale 2)."""
    items, maps = [], []
    for w, s in sorted(seals.items()):
        iid = f'{reader}-{w}'
        uuidmap[iid] = w
        letters = []
        for l in s['letters']:
            if rng.random() < frac:
                x, y = (l['x'] + 0.5) / 2 - 0.5, (l['y'] + 0.5) / 2 - 0.5
                letters.append({'ch': l['ch'], 'x': x, 'y': y, 'box': [x - 40, y - 50, x + 40, y + 50], 'conf': 'tentative'})
        if s['blank']:
            letters = [{'ch': 'Ο', 'x': 300.0 + 10 * k, 'y': 300.0, 'box': [280, 250, 320, 350], 'conf': 'tentative'}
                       for k in range(blank_names)]
        items.append({'id': iid, 'left': {'rows': 'Y' if letters else 'N', 'letters': letters},
                      'right': {'rows': 'N', 'letters': []}})
    maps = S.single_maps(reader, {i['id']: uuidmap[i['id']] for i in items})
    return {'items': items}, maps


def test_interp_sigma_crit():
    r = S.interp_sigma_crit({0.0: 10.0, 0.15: 8.0, 0.30: 6.0, 0.45: 4.0, 0.60: 1.0})
    assert r['discrete'] == 0.30 and r['sigma_crit'] == pytest.approx(0.30 + 0.15 * 0.5)
    r = S.interp_sigma_crit({0.0: 10.0, 0.15: 9.0, 0.30: 9.0, 0.45: 8.0, 0.60: 7.0})
    assert r['censored'] and r['sigma_crit'] == 0.60
    assert S.interp_sigma_crit({0.0: 0.0, 0.15: 1.0})['sigma_crit'] is None
    # D1-REF-RESULT ladder reproduces the recorded discrete sigma_crit 0.30 mm
    d1 = S.interp_sigma_crit({0.0: 11.37, 0.15: 8.44, 0.30: 6.42, 0.45: 4.30})
    assert d1['discrete'] == 0.30 and 0.30 < d1['sigma_crit'] < 0.45


def test_permutation_contrast_exact():
    x = [[5.0, 6.0, 7.0], [4.0, 5.0, 6.0]]
    k = [[1.0, 2.0, 3.0], [0.0, 1.0, 2.0]]
    r = S.permutation_contrast(x, k)
    assert r['n_perm'] == 400 and r['p'] == '1/400' and r['T'] == pytest.approx(8.0)
    r2 = S.permutation_contrast(k, x)
    assert r2['p_float'] == 1.0
    same = S.permutation_contrast([[1.0, 1.0, 1.0]] * 2, [[1.0, 1.0, 1.0]] * 2)
    assert same['p_float'] == 1.0


def test_split_row_answer_is_schema_valid():
    from hercules.scorer.schema import validate_reader_output
    ans = {'items': [{'id': 'u1', 'left': {'rows': 'Y', 'row_lines': [{'y': 100, 'angle_deg': 1.5}],
                                           'letters': [{'ch': 'Α', 'x': 10, 'y': 90, 'box': [0, 70, 20, 101],
                                                        'conf': 'firm', 'row': 0}]},
                      'right': {'rows': 'N', 'letters': []}}]}
    clean, rows = S.split_row_answer(ans)
    validate_reader_output(clean)
    assert rows['u1']['rows'][0]['y'] == 100 and rows['u1']['letters'][0]['row'] == 0


def test_merge_ms_answer_maps_quadrants_to_canvas_and_dedupes():
    key = {'ov': {'window': 'w', 'part': 'OV', 'scale': 2.0, 'y0': 0, 'x0': 0},
           'br': {'window': 'w', 'part': 'BR', 'scale': 1.0, 'y0': 1068, 'x0': 1068}}
    # the same Alpha at canvas (1500, 1500): overview image px 749.75, quadrant image px 432
    ans = {'items': [
        {'id': 'ov', 'left': {'rows': 'Y', 'letters': [{'ch': 'Α', 'x': 749.75, 'y': 749.75, 'box': [700, 700, 800, 800], 'conf': 'tentative'}]}, 'right': {'rows': 'N', 'letters': []}},
        {'id': 'br', 'left': {'rows': 'N', 'letters': [{'ch': 'Α', 'x': 432.0, 'y': 432.0, 'box': [400, 400, 460, 460], 'conf': 'firm'},
                                                       {'ch': 'Ο', 'x': 10.0, 'y': 10.0, 'box': [0, 0, 20, 20], 'conf': 'tentative'}]}, 'right': {'rows': 'N', 'letters': []}}]}
    merged, ids = S.merge_ms_answer(ans, key)
    it = merged['items'][0]
    assert ids == {'w': 'ms::w'} and it['left']['rows'] == 'Y'
    a = [l for l in it['left']['letters'] if l['ch'] == 'Α']
    assert len(a) == 1 and a[0]['conf'] == 'firm' and a[0]['x'] == pytest.approx(1500.0)
    o = [l for l in it['left']['letters'] if l['ch'] == 'Ο'][0]
    assert o['x'] == pytest.approx(1078.0)


def test_score_cell_end_to_end_orders_arms_and_chance_is_low():
    rng = np.random.default_rng(5)
    seals = make_seals(rng)
    arms = {}
    for arm, frac, bn in (('K_D2', 0.3, 0), ('EX', 0.9, 0), ('EXPL', 0.3, 3)):
        readers, maps = {}, []
        for j in range(3):
            rid = f'{arm}_r{j}'
            ans, mp = answer_for(seals, frac, rng, {}, rid, blank_names=bn)
            readers[rid] = ans
            maps += mp
        arms[arm] = {'readers': readers, 'maps': maps, 'windows': sorted(seals)}
    res, res_c = S.score_cell(arms, seals, n_perm=200)
    cn = {a: res['arms'][a]['summed_mean_C_net'] for a in arms}
    assert cn['EX'] > cn['K_D2'] > 0
    bl = {a: S.reader_blank_namings(res, a) for a in arms}
    assert all(v == 0 for v in bl['EX'].values()) and all(v == 3 for v in bl['EXPL'].values())
    ch = res_c['arms']['CHANCE_EX']['summed_mean_C_all'][S.R250]
    assert ch < res['arms']['EX']['summed_mean_C_all'][S.R250]
    rs = S.reader_summed(res, 'EX')
    assert set(rs) == {'EX_r0', 'EX_r1', 'EX_r2'}


def test_arm_outcome_bars():
    lad_k = {0.0: 10.0, 0.15: 8.0, 0.30: 5.5, 0.45: 3.0, 0.60: 1.0}
    lad_x = {0.0: 10.0, 0.15: 9.0, 0.30: 8.0, 0.45: 6.5, 0.60: 3.0}
    lad_p = {0.0: 10.0, 0.15: 8.0, 0.30: 5.0, 0.45: 3.0, 0.60: 1.0}
    mr = {'ladder': {'K_D2': lad_k, 'EX': lad_x, 'EXPL': lad_p},
          'reader_cnet': {'K_D2': {0.30: [5, 5.5, 6], 0.45: [3, 3, 3]}, 'EX': {0.30: [8, 8, 8], 0.45: [6, 6.5, 7]},
                          'EXPL': {0.30: [5, 5, 5], 0.45: [3, 3, 3]}},
          'blank_mean': {'K_D2': 0.0, 'EX': 0.0, 'EXPL': 0.0}, 'chance_c_all': {'K_D2': 1.0, 'EX': 1.3, 'EXPL': 1.0}}
    o = S.arm_outcome(mr, 'EX', placebo='EXPL')
    assert o['outcome'] == 'GAIN_PENDING_REPLICATION', o['checks']
    mr['blank_mean']['EX'] = 1.0
    assert S.arm_outcome(mr, 'EX', placebo='EXPL')['outcome'] == 'NO_GAIN'
    mr['blank_mean']['EX'] = 0.0
    mr['precision'] = {'K_D2': {0.30: 0.5, 0.45: 0.4}, 'EX': {0.30: 0.45, 0.45: 0.2}, 'EXPL': {0.30: 0.5, 0.45: 0.4}}
    assert S.arm_outcome(mr, 'EX', placebo='EXPL')['checks']['precision_not_down'] is False
    del mr['precision']
    mr['ladder']['EXPL'] = lad_x  # placebo gains as much: priming, not acuity
    assert S.arm_outcome(mr, 'EX', placebo='EXPL')['checks']['gain_exceeds_placebo_gain'] is False


def test_holm():
    r = S.holm({'EX': 1 / 400, 'MS': 0.02, 'ROW': 0.012, 'EXPL': 0.5})
    assert r['EX']['reject'] and r['ROW']['reject'] and r['MS']['reject'] and not r['EXPL']['reject']
    assert r['MS']['threshold'] == 0.025 and S.holm({'EX': 0.03, 'MS': 0.03})['MS']['reject'] is False
    assert r['EX']['threshold'] == 0.0125
    r = S.holm({'a': 0.2, 'b': 0.001})
    assert r['b']['reject'] and not r['a']['reject']
