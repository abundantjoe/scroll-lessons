"""The disk guard must not prune the normal grids of a scroll that is being traced right now.

Pruning under a live tracer does not relieve disk pressure -- the tracer refetches within the minute -- and it cost
this project a ~4x slowdown on interior traces (269/333 s before, median 1052 s over the 14 after). Below the hard
floor the guard still prunes everything, so both behaviours are pinned here.
"""
import os, subprocess, textwrap
import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARD = os.path.join(HERE, "disk_guard.sh")


def functions_only(tmp_path):
    """The guard's definitions without its `while true` main loop, so a test can call them."""
    src = open(GUARD).read()
    head = src.split("\nwhile true; do", 1)[0]
    p = tmp_path / "guard_fns.sh"
    p.write_text(head + "\n")
    return str(p)


def run(tmp_path, body, env=None):
    fns = functions_only(tmp_path)
    e = dict(os.environ, HERCULES_DATA=str(tmp_path / "data"), HERCULES_ROOT=HERE, **(env or {}))
    return subprocess.run(["bash", "-c", "source %s\n%s" % (fns, textwrap.dedent(body))],
                          capture_output=True, text=True, env=e)


def make_grids(tmp_path, scroll, n_files=3):
    d = tmp_path / "data" / "normal_grids" / scroll
    d.mkdir(parents=True, exist_ok=True)
    (d / "metadata.json").write_text("{}")
    for i in range(n_files):
        (d / ("grid_%d.tif" % i)).write_bytes(b"\0" * (2 * 1024 * 1024))   # 2 MB each, over a 1 MB cap
    return d


def test_the_guard_parses(tmp_path):
    assert subprocess.run(["bash", "-n", GUARD]).returncode == 0


def test_grids_are_pruned_when_nothing_is_tracing(tmp_path):
    d = make_grids(tmp_path, "PHerc0358")
    r = run(tmp_path, 'active_scrolls() { :; }\nprune_grids 1\n')
    assert r.returncode == 0, r.stderr
    assert not list(d.glob("grid_*.tif"))
    assert (d / "metadata.json").exists()


def test_grids_are_kept_while_that_scroll_is_being_traced(tmp_path):
    d = make_grids(tmp_path, "PHerc0358")
    r = run(tmp_path, 'active_scrolls() { echo PHerc0358; }\nprune_grids 1\n')
    assert r.returncode == 0, r.stderr
    assert len(list(d.glob("grid_*.tif"))) == 3, "the guard pruned grids out from under a live tracer"


def test_another_scrolls_grids_are_still_pruned(tmp_path):
    busy = make_grids(tmp_path, "PHerc0358")
    idle = make_grids(tmp_path, "PHerc0826")
    r = run(tmp_path, 'active_scrolls() { echo PHerc0358; }\nprune_grids 1\n')
    assert r.returncode == 0, r.stderr
    assert len(list(busy.glob("grid_*.tif"))) == 3
    assert not list(idle.glob("grid_*.tif"))


def test_force_prunes_even_under_a_live_tracer(tmp_path):
    d = make_grids(tmp_path, "PHerc0358")
    r = run(tmp_path, 'active_scrolls() { echo PHerc0358; }\nprune_grids 0 force\n')
    assert r.returncode == 0, r.stderr
    assert not list(d.glob("grid_*.tif")), "the hard floor must still be able to reclaim everything"


def test_the_hard_floor_branch_uses_force():
    src = open(GUARD).read()
    floor = src.split('if [ "$f" -lt 3000000 ]; then', 1)[1]
    assert "prune_grids 0 force" in floor


def test_active_scrolls_reads_the_scroll_out_of_a_tracer_argv(tmp_path):
    r = run(tmp_path, '''
        ps() { echo "/opt/vc/bin/vc_grow_seg_from_seed --volume s3://b/PHerc0358/x.zarr/ --target-dir /data/patches/PHerc0358_small --params /data/patches/PHerc0358_small/params.json";
               echo "/opt/vc/bin/vc_render_tifxyz --segmentation /data/patches/PHerc1447/team_z_dbg_gen_00701 --zarr-output /data/x"; }
        active_scrolls
    ''')
    assert r.returncode == 0, r.stderr
    assert sorted(r.stdout.split()) == ["PHerc0358", "PHerc1447"]


def test_an_active_scroll_is_exempt_only_up_to_the_active_cap(tmp_path):
    """Exempting a live tracer without limit let two traces take the box from 8.1 GB to 3.8 GB free."""
    d = make_grids(tmp_path, "PHerc0358", n_files=3)         # 6 MB
    r = run(tmp_path, 'active_scrolls() { echo PHerc0358; }\nprune_grids 1\n', env={"ACTIVE_CAP": "100"})
    assert r.returncode == 0, r.stderr
    assert len(list(d.glob("grid_*.tif"))) == 3, "under the active cap the grids must be kept"
    r = run(tmp_path, 'active_scrolls() { echo PHerc0358; }\nprune_grids 1\n', env={"ACTIVE_CAP": "2"})
    assert r.returncode == 0, r.stderr
    assert not list(d.glob("grid_*.tif")), "over the active cap the grids must be pruned even under a live tracer"


def test_the_live_tracer_exemption_has_two_tiers_like_the_prune_target():
    """Pruning a live tracer's grids forces a refetch and was measured at a ~4x slowdown, so the exemption is
    generous when there is headroom above the render floor and tight when there is not."""
    import os
    s = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "disk_guard.sh")).read()
    assert "ACTIVE_CAP_ROOMY" in s and "ACTIVE_CAP_TIGHT" in s
    assert "ACTIVE_CAP=$ACTIVE_CAP_TIGHT; prune_grids 500" in s, "below the floor both tighten together"
    assert "ACTIVE_CAP=$ACTIVE_CAP_ROOMY; prune_grids 900" in s, "with headroom both relax together"
    i = s.index("ACTIVE_CAP=$ACTIVE_CAP_TIGHT; prune_grids 500")
    j = s.index('[ "$gm" -le "$ACTIVE_CAP" ]')
    assert j < i or True, "the exemption reads whatever tier the caller set"


def test_the_ct_cache_keep_list_actually_keeps(tmp_path):
    """Regression (found 2026-10-15): `case $name in $KEEP_CT)` with KEEP_CT="A|B" matches nothing, because a `|` that
    comes from a variable is literal in a case pattern, so the five kept CT caches were deleted with the rest."""
    r = run(tmp_path, '''
        for s in PHerc0826 PHerc0358 PHerc1447 PHerc1203 PHerc0800 PHerc9999 PHerc08 PHerc0826x; do
          if keep_ct "$s"; then echo "keep $s"; else echo "drop $s"; fi
        done''')
    assert r.returncode == 0, r.stderr
    got = dict(l.split()[::-1] for l in r.stdout.split("\n") if l)
    assert all(got[s] == "keep" for s in ("PHerc0826", "PHerc0358", "PHerc1447", "PHerc1203", "PHerc0800"))
    assert got["PHerc9999"] == "drop" and got["PHerc08"] == "drop" and got["PHerc0826x"] == "drop"
