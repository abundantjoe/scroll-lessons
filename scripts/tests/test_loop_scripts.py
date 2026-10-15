"""Queue loops must not be able to lose their queue.

On 2026-09-18 the G-GP part 4 dense loop reported "dense queue done" after ONE of 25 seeds. The cause was not
established -- a duplicate loop had been started by hand and then killed, which is the likelier explanation -- but
the shape of the loop made the failure unfalsifiable: a `while read` fed by a PIPE hands its stdin to every command
in the body, so a queue can be consumed silently by anything inside it. These tests pin the shape instead of the
symptom: the seed list is materialised before the loop, and the tracer call cannot read from it.
"""
import os, re, subprocess
import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOOPS = ["dense_loop.sh"]


@pytest.mark.parametrize("name", LOOPS)
def test_parses(name):
    assert subprocess.run(["bash", "-n", os.path.join(HERE, name)]).returncode == 0


@pytest.mark.parametrize("name", LOOPS)
def test_queue_is_materialised_before_the_loop(name):
    s = open(os.path.join(HERE, name)).read()
    assert "mapfile -t SEEDS" in s, "the seed list must be read into an array, not piped into `while read`"
    assert not re.search(r"\|\s*while read", s), "a pipe-fed `while read` can have its queue eaten by the loop body"


@pytest.mark.parametrize("name", LOOPS)
def test_the_tracer_call_cannot_read_the_queue(name):
    s = open(os.path.join(HERE, name)).read()
    line = [l for l in s.splitlines() if "vc_tools.sh trace" in l]
    assert line, "no tracer call found"
    body = " ".join(s.splitlines()[max(0, s.splitlines().index(line[0]) - 1):s.splitlines().index(line[0]) + 1])
    assert "</dev/null" in body, "the tracer call must have its stdin closed"


@pytest.mark.parametrize("name", LOOPS)
def test_the_loop_reports_its_progress(name):
    s = open(os.path.join(HERE, name)).read()
    assert "patches so far" in s, "a queue that ends early must be visible in its own log, not only in the patch count"
    assert "of ${#SEEDS[@]} seeds" in s, "the loop must log how many seeds it took, so a truncated queue is obvious"


def test_concurrent_dense_loops_take_disjoint_seeds():
    """Two loops share the trace slot pool; they must never contend for the same seed."""
    s = open(os.path.join(HERE, "dense_loop.sh")).read()
    assert "DENSE_PART" in s and "DENSE_PARTS" in s
    assert "% PARTS )) -eq \"$PART\"" in s, "the split must be by seed index modulo the number of parts"
    assert "dense_loop_$PART.pid" in s, "each part needs its own pid file or the supervisor cannot track both"


def test_the_loop_waits_for_an_orphaned_trace_of_the_same_seed():
    """The supervisor kills a loop holding a stale proxy, orphaning its docker trace and freeing the flock slot.

    Without this check the restarted loop traces the same seed again, and two traces of one seed are the same
    observation twice -- which is exactly what happened twice on 2026-09-18.
    """
    s = open(os.path.join(HERE, "dense_loop.sh")).read()
    assert "already being traced (orphaned run); waiting" in s
    assert "c_grow_seg_from_seed .*--target-dir" in s, "the check must match the running tracer argv"


def test_rbest2_volume_ids_match_the_supervisors_coverage_map():
    """A wrong volume id renders the wrong scroll's CT under a correct-looking ledger key."""
    import re
    sup = open(os.path.join(HERE, "supervisor.sh")).read()
    cov = re.search(r'^COVERAGE=\$\{COVERAGE:-"(.*?)"\}', sup, re.M).group(1)
    truth = {s.split(":")[0]: s.split(":")[1] for s in cov.split()}
    s = open(os.path.join(HERE, "rbest2.sh")).read()
    for scroll, vol in re.findall(r'(PHerc\d+\w*)\*?\)\s+vol=(\d+)', s):
        base = scroll.rstrip("*")
        assert base in truth, "unknown scroll %s" % base
        assert truth[base] == vol, "%s: rbest2 has %s, COVERAGE has %s" % (base, vol, truth[base])


def test_rcrest_power_queues_honour_a_pause_marker():
    """Killing an inference alone only makes its queue retry the same surface; the marker must stop the queue."""
    for name, marker in (("rcrest_power_1203.sh", "rcrest_power_1203_paused"),
                         ("rcrest_power.sh", "rcrest_power_paused")):
        s = open(os.path.join(HERE, name)).read()
        assert marker in s, "%s does not check its pause marker" % name
        assert 'break;' in s.split(marker, 1)[1][:120], "%s must break out of its queue when paused" % name
    sup = open(os.path.join(HERE, "supervisor.sh")).read()
    for var, guard in (("n1203", "rcrest_power_1203_paused ] && n1203=0"),
                       ("rcp_left", "rcrest_power_paused ] && rcp_left=0")):
        assert guard in sup, "the supervisor would resume a paused queue (%s)" % var
        assert sup.index(guard) < sup.index('if [ "$%s" -gt 0 ]' % var), \
            "the pause for %s is tested after the queue is resumed, not before" % var


def test_rbest_loops_do_not_start_a_second_read_of_the_same_surface():
    """A read in progress has no read_stats.json either, so the retry pass started a duplicate inference on one
    render -- two processes writing one output. Both loops must check for a running read first."""
    for name in ("rbest.sh", "rbest2.sh"):
        s = open(os.path.join(HERE, name)).read()
        assert "already being read; not starting a second inference" in s, "%s can duplicate a read" % name
        assert "nk_detection.inference.infer $D/patches/$sc/$patch/render.zarr" in s, \
            "%s must match the running inference by its exact render path" % name


# ---------- a patches DIRECTORY is not a scroll name (fixed 2026-09-19 03:05 UTC)

def _src(name):
    import os
    return open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), name)).read()


def test_read_loops_pass_the_real_scroll_not_the_patches_directory():
    """PHerc0826_small / _src / _cons_part4 / _dense are one scroll and one volume; only the directory differs.
    Passing the directory as --scroll raises KeyError in volume_info, which is what rbest2 did on every
    PHerc0826_small member of its declared population until this was fixed."""
    r2 = _src("rbest2.sh")
    assert "base=${sc%%_*}" in r2
    assert "--scroll $base" in r2 and "--scroll $sc " not in r2
    assert "PHerc0826*)" not in r2, "the case must match the base scroll exactly, not a directory prefix"
    rd = _src("rdepth_part2.sh")
    assert '--scroll "${scroll%%_*}"' in rd


def test_read_loops_still_use_the_directory_for_the_patches_path():
    """The fix must not send the reader looking in patches/<scroll> for a surface that lives in a sub-campaign dir."""
    r2 = _src("rbest2.sh")
    assert "run_patch_dir.py $D/patches/$sc" in r2, "the patches path stays the directory"
    rd = _src("rdepth_part2.sh")
    assert '"$(dirname "$dir")"' in rd


# ---------- R-SMALL-2 reuses the R-SMALL loop rather than copying it

def test_rsmall_loop_is_parameterised_and_keeps_rsmall_defaults():
    s = _src("rsmall_loop.sh")
    assert "RS_SUFFIX:-_small" in s, "the default must stay exactly R-SMALL's, so R-SMALL is unchanged"
    assert "RS_SEEDS:-$R/seeds/${sc}_interior.json" in s
    for guard in ("rsmall_paused", "flock -n 9", "RSMALL_MAX"):
        assert guard in s, "R-SMALL-2 must inherit the %s guard, not lose it to a copied loop" % guard


def test_rsmall_loop_materialises_its_queue_and_closes_stdin():
    """A `while read` fed by a pipe hands its stdin to whatever runs inside it - how dense_loop.sh lost 24 seeds."""
    s = _src("rsmall_loop.sh")
    assert "mapfile -t SEEDLIST" in s
    assert "| while read X Y Z" not in s
    assert "vc_tools.sh trace" in s and "</dev/null" in s


def test_rsmall2_starter_waits_for_part5_and_cannot_double_start():
    s = _src("rsmall2_when_ready.sh")
    assert "part5_seeds.json" in s and 'have" -lt "$need' in s, "it must be a no-op while part 5 still traces"
    assert "rsmall_loop.pid" in s and "kill -0" in s, "a second loop for the same scroll must be refused"
    assert "RS_SUFFIX=_rs2" in s and "TRACE_GENERATIONS=40" in s, "the declared budget and directory"
    assert "_rsmall2.json" in s, "it must use the declared population file"
