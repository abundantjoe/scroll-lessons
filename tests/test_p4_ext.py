# Provenance: Project HERCULES | owner the owner | [id removed]
import importlib.util
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools', 'p4'))
_spec = importlib.util.spec_from_file_location('p4_ext', os.path.join(os.path.dirname(__file__), '..', 'tools', 'p4', 'p4_ext.py'))
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)
K = E.known_letters

WORD = [('Α', 100, 500), ('Β', 250, 500), ('Γ', 400, 500), ('Δ', 550, 500), ('Ε', 700, 500), ('Ζ', 850, 500)]


def _jit(lets, rng, sd=20):
    return K([{'ch': c, 'x': x + rng.gauss(0, sd), 'y': y + rng.gauss(0, sd)} for c, x, y in lets])


def _noise(rng, n=5):
    kinds = 'ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡϹΤΥΦΧΨΩ'
    return K([{'ch': rng.choice(kinds), 'x': rng.uniform(0, 1068), 'y': rng.uniform(0, 1068)} for _ in range(n)])


def test_text_confirms_noise_does_not():
    rng = random.Random(1)
    u = [_jit(WORD, rng) for _ in range(9)]
    r = [_noise(rng) for _ in range(9)]
    n0 = [E.best_pair([_noise(rng) for _ in range(3)]) for _ in range(48)]
    d = E.decide(u, r, n0)
    assert d['EXT_CONFIRMED'] and d['u_triples'] == [6, 6, 6] and d['perm_p'] < 0.01
    d = E.decide(r, u, n0)
    assert not d['EXT_CONFIRMED']


def test_same_texture_upright_and_rotated_fails_iii():
    rng = random.Random(2)
    u = [_jit(WORD, rng) for _ in range(9)]
    r = [_jit(WORD, rng) for _ in range(9)]
    d = E.decide(u, r, [0] * 48)
    assert d['crit_i_median_u_gt_n0max'] and d['crit_ii_every_u_triple_ge5'] and not d['crit_iii_u_gt_r_p001']
    assert not d['EXT_CONFIRMED']


def test_null_max_blocks():
    rng = random.Random(3)
    u = [_jit(WORD, rng) for _ in range(9)]
    r = [_noise(rng) for _ in range(9)]
    d = E.decide(u, r, [0] * 47 + [6])
    assert not d['crit_i_median_u_gt_n0max'] and not d['EXT_CONFIRMED']


def test_assign_n0_each_three_times_no_dupes():
    import collections
    n0 = [f'n{i}' for i in range(E.N_N0)]
    sess = E._assign_n0(n0, random.Random(4))
    assert len(sess) == E.N_SESS and all(len(s) == E.PER_N0 and len(set(s)) == E.PER_N0 for s in sess)
    assert set(collections.Counter(u for s in sess for u in s).values()) == {3}
