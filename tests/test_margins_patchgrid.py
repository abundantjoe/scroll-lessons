import numpy as np

from stripqc import margins, patchgrid


def test_positions_match_villa_rule():
    assert patchgrid.positions(240) == [0, 64, 112]
    assert patchgrid.positions(260) == [0, 64, 128, 132]
    assert patchgrid.positions(380) == [0, 64, 128, 192, 252]
    assert patchgrid.positions(400) == [0, 64, 128, 192, 256, 272]
    assert patchgrid.positions(100) == [0]


def test_blank_share_peaks_in_edge_patches_trough_in_middle():
    v = np.ones(260, bool)
    v[:30] = False
    v[230:] = False
    s = patchgrid.blank_share(v)
    assert s[64] > 0.95 and s[128] < s[64] and s[192] > s[128]


def test_edge_distance_and_band_mid():
    valid = np.zeros((100, 10), bool)
    valid[10:90] = True
    d = margins.edge_distance(valid)
    assert d[10, 0] == 0 and d[50, 0] == 39 and d[0, 0] == -1
    ink = np.zeros((100, 10))
    ink[(d >= 20) & (d <= 30)] = 10.0
    bm = margins.band_mid(ink, valid, band=(20, 30), mid=30)
    assert bm['band'] == 10.0 and bm['mid'] == 0.0 and bm['ratio'] is None


def test_top_margin_experiment_separates_margin_classes():
    H, W = 260, 600
    valid = np.zeros((H, W), bool)
    valid[30:230, :300] = True      # 30-row top margin
    valid[10:230, 300:] = True      # 10-row top margin
    ink = np.zeros((H, W))
    ink[50:90, :300] = 0.13         # artifact: depends on the margin, not on node rows
    ink[50:90, 300:] = 0.02
    res = margins.top_margin_experiment(ink, valid)
    assert abs(res[30][0] - 0.13) < 1e-9 and abs(res[10][0] - 0.02) < 1e-9
    assert res[30][1] >= 129 and res[10][1] >= 129


def test_validity_from_ct_not_from_ink():
    ct = np.zeros((5, 20, 20), np.uint8)
    ct[:, 5:15] = 100
    assert margins.valid_from_render(ct).sum() == 10 * 20
