import os, sys, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cluster_power as C


def test_a_surface_with_fewer_than_three_valid_units_can_never_produce_a_candidate():
    for n in (0, 1, 2):
        g = np.zeros((2, 2), bool); g.flat[:n] = True
        assert C.p_triple(g, p=1.0, trials=50) == 0.0


def test_three_units_in_a_line_all_flagged_is_a_candidate():
    g = np.zeros((1, 3), bool); g[0, :] = True
    assert C.p_triple(g, p=1.0, trials=50) == 1.0


def test_three_units_that_are_not_4_connected_are_not_a_candidate_even_when_all_flag():
    g = np.zeros((3, 3), bool)
    g[0, 0] = g[1, 1] = g[2, 2] = True        # diagonal: 8-connected but not 4-connected
    assert C.p_triple(g, p=1.0, trials=50) == 0.0


def test_the_probability_rises_with_the_flag_rate():
    g = np.ones((3, 3), bool)
    lo = C.p_triple(g, p=0.05, trials=4000, rng=np.random.default_rng(1))
    hi = C.p_triple(g, p=0.50, trials=4000, rng=np.random.default_rng(1))
    assert 0.0 <= lo < hi <= 1.0


def test_a_big_grid_beats_several_small_ones_at_the_same_unit_count():
    big = np.ones((3, 4), bool)                                  # 12 units, contiguous
    smalls = [np.ones((2, 2), bool) for _ in range(3)]           # 12 units, in three 2x2 islands
    rng = np.random.default_rng(3)
    pb = C.p_triple(big, p=0.0986, trials=8000, rng=rng)
    ps = sum(C.p_triple(s, p=0.0986, trials=8000, rng=rng) for s in smalls)
    assert pb > ps, (pb, ps)


def test_the_control_rate_is_the_controls_own_measured_rate_not_a_choice():
    assert abs(C.P_CONTROL - 7.0 / 71.0) < 1e-12


def test_a_consensus_builds_two_outputs_are_counted_once():
    g = np.ones((2, 3), bool)
    out = {("PHerc0826_cons_part5", "auto_grown_1"): g.copy(),
           ("PHerc0826_cons_part5", "auto_trace_1_seed"): g.copy()}
    assert len(C.dedupe_consensus(out)) == 1


def test_two_DIFFERENT_consensus_surfaces_are_both_kept():
    a = np.ones((2, 3), bool); b = np.ones((2, 3), bool); b[0, 0] = False
    out = {("PHerc0826_cons_part5", "auto_grown_1"): a,
           ("PHerc0826_cons_part5", "auto_trace_1_seed"): b}
    assert len(C.dedupe_consensus(out)) == 2


def test_different_consensus_PARTS_are_never_merged():
    g = np.ones((2, 3), bool)
    out = {("PHerc0826_cons_part5", "auto_grown_1"): g.copy(),
           ("PHerc0826_cons_part6", "auto_grown_2"): g.copy()}
    assert len(C.dedupe_consensus(out)) == 2


def test_ordinary_traces_are_never_deduped_even_with_identical_layouts():
    g = np.ones((2, 2), bool)
    out = {("PHerc0826", "auto_grown_a"): g.copy(), ("PHerc0826", "auto_grown_b"): g.copy()}
    assert len(C.dedupe_consensus(out)) == 2


def _stats(rows, cols, valid, swapped_only=False):
    units = [dict(row=r, col=c) for r, c in valid]
    t = dict(n_valid=len(valid), grid_rows=rows, grid_cols=cols, valid_units=[] if swapped_only else units)
    j = dict(rule55=dict(units={"0.5cm2": t}))
    if swapped_only:
        j["rule55_depth_swapped"] = {"0.5cm2": dict(valid_units=units)}
    return j


def test_grid_from_read_stats_uses_the_recorded_layout_and_falls_back_to_the_swapped_table():
    valid = [(0, 0), (0, 2), (1, 1)]                      # a checkerboard: no two units 4-connected
    for swapped_only in (False, True):
        g = C.grid_from_read_stats(_stats(2, 3, valid, swapped_only))
        assert g.shape == (2, 3) and int(g.sum()) == 3
        assert all(g[r, c] for r, c in valid)
        assert C.p_triple(g, p=1.0, trials=20) == 0.0     # three valid units, none adjacent: never a candidate
    assert C.grid_from_read_stats(dict(rule55=None)) is None
    assert C.grid_from_read_stats(_stats(2, 2, [])) is None


def test_read_stats_cli_scores_a_read_without_touching_the_corpus(tmp_path, capsys):
    import json
    f = tmp_path / "read_stats.json"
    f.write_text(json.dumps(_stats(1, 3, [(0, 0), (0, 1), (0, 2)])))
    assert C.main(["--read-stats", str(f), "--p", "1.0", "--trials", "20"]) == 0
    out = capsys.readouterr().out
    assert "valid units 3" in out and "= 1.0000" in out and "expected candidates over 1 read(s): 1.0000" in out
