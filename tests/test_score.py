import numpy as np

from stripqc import score


BOXES = [[20, 20, 60, 60], [100, 20, 140, 60]]   # two letters, raw frame


def make(E, valid=None, r0=0, c0=0):
    return dict(E=E.astype(np.float32), valid=np.ones(E.shape, bool) if valid is None else valid, r0=r0, c0=c0)


def ref_map():
    E = np.full((100, 200), 0.30, np.float32)
    E[25:55, 25:55] = 0.80      # letter 0 strong
    E[25:55, 105:135] = 0.70    # letter 1 strong
    return E


def test_identical_arm_scores_perfectly():
    R = make(ref_map())
    m = score.metrics([score.match(R, R, 0, 5, BOXES)])
    assert m['recall'] == 1.0 and abs(m['r'] - 1.0) < 1e-9 and m['f_out'] == 0.0 and m['coverage'] == 1.0


def test_attenuated_arm_loses_recall_but_keeps_rank():
    R = make(ref_map())
    A = make(ref_map() * 0.6)   # strong px fall below 0.55: fixed-threshold recall 0, rank order intact
    m = score.metrics([score.match(A, R, 0, 5, BOXES)])
    assert m['recall'] == 0.0 and m['r'] > 0.99 and m['auc_box'] == m['ref_auc_box']
    assert m['recall_matched_rate'] == 1.0


def test_offsets_map_arm_into_ref_frame():
    full = ref_map()
    R = make(full)
    A = make(full[20:80], r0=20)              # a strip cut from node row 1 (20 px)
    m = score.metrics([score.match(A, R, 1, 4, BOXES)])
    assert m['recall'] == 1.0 and abs(m['r'] - 1.0) < 1e-9


def test_constant_map_gives_none_not_nan():
    R = make(ref_map())
    A = make(np.full((100, 200), 0.3))
    m = score.metrics([score.match(A, R, 0, 5, BOXES)])
    assert m['r'] is None
    import json
    json.dumps(m, allow_nan=False)            # strict JSON


def test_missing_arm_is_none(tmp_path):
    assert score.load_arm(str(tmp_path / 'nope'), 1) is None


def test_bootstrap_ci_brackets_estimate():
    R = make(ref_map())
    A = ref_map().copy()
    A[25:55, 105:135] = 0.40                   # letter 1 lost
    p = [score.match(make(A), R, 0, 5, BOXES)]
    m = score.metrics(p)
    lo, hi, n = score.bootstrap_recall(p, n=500)
    assert n == 2 and lo <= m['recall'] <= hi and abs(m['recall'] - 0.5) < 1e-9


def test_auc():
    assert score.auc([0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1]) == 1.0
    assert score.auc([0.5, 0.5], [0, 1]) == 0.5
    assert score.auc([0.1], [1]) is None


def test_empty_overlap_gives_none_not_crash():
    ref = make(ref_map())
    arm = make(ref_map(), valid=np.zeros((100, 200), bool))     # no pixel valid in the arm
    p = score.match(arm, ref, 0, 5, BOXES)
    assert score.metrics([p]) is None


def test_bootstrap_without_ref_strong_letters_gives_none():
    E = np.full((100, 200), 0.30, np.float32)                   # nothing above the threshold anywhere
    p = score.match(make(E), make(E), 0, 5, BOXES)
    assert score.bootstrap_recall([p], n=50)[:2] == (None, None)
