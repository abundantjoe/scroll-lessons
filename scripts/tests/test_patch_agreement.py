"""RULES G-GP part 3/4: the same-sheet agreement precondition for vc_grow_seg_from_segments."""
import importlib.util, json, os, sys
import numpy as np, pytest, tifffile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("patch_agreement", os.path.join(HERE, "patch_agreement.py"))
pa = importlib.util.module_from_spec(spec); spec.loader.exec_module(pa)


def write(d, P):
    os.makedirs(d, exist_ok=True)
    for i, n in enumerate("xyz"):
        tifffile.imwrite(os.path.join(d, n + ".tif"), P[..., i].astype(np.float32))
    json.dump({"scale": [0.05, 0.05], "format": "tifxyz"}, open(os.path.join(d, "meta.json"), "w"))
    return d


def sheet(rows, cols, z, step=20.0, x0=1000.0, y0=1000.0):
    u, v = np.meshgrid(np.arange(cols) * step, np.arange(rows) * step)
    return np.stack([x0 + u, y0 + v, np.full_like(u, float(z))], -1)


def test_patches_on_the_same_sheet_agree(tmp_path):
    dirs = [write(str(tmp_path / ("p%d" % i)), sheet(20, 20, 500.0)) for i in range(3)]
    occ, used = pa.agreement(dirs, 24.0)
    assert used == 3
    counts = np.array([len(s) for s in occ.values()])
    assert counts.min() == 3, "identical sheets must agree everywhere"


def test_patches_on_wraps_further_apart_than_the_cell_do_not_agree(tmp_path):
    """48 voxels is the measured wrap spacing; two sheets that far apart must not be counted as one."""
    dirs = [write(str(tmp_path / "a"), sheet(20, 20, 500.0)),
            write(str(tmp_path / "b"), sheet(20, 20, 548.0))]
    occ, _ = pa.agreement(dirs, 24.0)
    counts = np.array([len(s) for s in occ.values()])
    assert counts.max() == 1, "sheets one wrap apart were counted as agreeing"


def test_a_patch_counts_once_per_cell_however_many_of_its_nodes_land_there(tmp_path):
    """A dense grid must not be able to satisfy a consensus threshold on its own."""
    fine = sheet(60, 60, 500.0, step=2.0)          # many nodes inside a single 24-voxel cell
    occ, _ = pa.agreement([write(str(tmp_path / "dense"), fine)], 24.0)
    counts = np.array([len(s) for s in occ.values()])
    assert counts.max() == 1


def test_explicit_dirs_population(tmp_path, capsys):
    d = write(str(tmp_path / "only"), sheet(20, 20, 500.0))
    pa.main(["--dirs", d, "--label", "one", "--thresholds", "1", "2"])
    out = capsys.readouterr().out
    assert "one: 1 patches" in out and ">=  2 patches agree:       0 cells" in out


def test_curve_reports_every_prefix(tmp_path, capsys):
    dirs = [write(str(tmp_path / ("p%d" % i)), sheet(20, 20, 500.0)) for i in range(3)]
    pa.main(["--dirs", *dirs, "--label", "camp", "--curve", "--thresholds", "2", "3"])
    lines = [l for l in capsys.readouterr().out.splitlines() if l.strip().startswith(("1 ", "2 ", "3 "))]
    assert len(lines) >= 3, "the curve must have a row per prefix"


def test_two_traces_from_the_same_seed_count_once(tmp_path):
    """A duplicate trace is the same observation twice; it must not manufacture consensus support."""
    a = write(str(tmp_path / "a"), sheet(20, 20, 500.0))
    b = write(str(tmp_path / "b"), sheet(20, 20, 500.0))
    for d in (a, b):
        m = json.load(open(os.path.join(d, "meta.json")))
        m["seed"] = [100.0, 200.0, 300.0]
        json.dump(m, open(os.path.join(d, "meta.json"), "w"))
    occ, used = pa.agreement([a, b], 24.0)
    assert used == 1
    assert max(len(s) for s in occ.values()) == 1, "a duplicated seed inflated the agreement count"


def test_the_teams_placeholder_zero_seed_does_not_collapse_distinct_segments(tmp_path):
    dirs = []
    for i, z in enumerate((500.0, 500.0)):
        d = write(str(tmp_path / ("t%d" % i)), sheet(20, 20, z))
        m = json.load(open(os.path.join(d, "meta.json")))
        m["seed"] = [0.0, 0.0, 0.0]
        json.dump(m, open(os.path.join(d, "meta.json"), "w"))
        dirs.append(d)
    occ, used = pa.agreement(dirs, 24.0)
    assert used == 2, "a placeholder seed of [0,0,0] must not merge distinct published segments"


def test_consensus_outputs_are_not_counted_as_independent_sources(tmp_path, capsys):
    """A *_cons surface is grown FROM these patches; counting it would feed a derivative back in as support."""
    root = tmp_path / "patches"
    for sub in ("PHerc9999", "PHerc9999_cons"):
        d = root / sub / "auto_grown_1"
        write(str(d), sheet(20, 20, 500.0))
    pa.main(["--scrolls", "PHerc9999", "--patches", str(root), "--thresholds", "1", "2"])
    out = capsys.readouterr().out
    assert "PHerc9999: 1 patches" in out, "the consensus output was counted as a source patch"
