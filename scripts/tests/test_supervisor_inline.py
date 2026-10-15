"""The supervisor used to build its long-running jobs as single-quoted strings for `bash -c`. `bash -n` on the
supervisor does NOT parse such a string, so a stray quote inside one is invisible until the job dies at runtime — and
a regex that re-extracts the body cannot catch it either, because the stray quote is what decides where the body ends.
That is how the disk guard was killed on 2026-09-18.

The fix is structural: long bodies live in their own files, which parse. This test enforces that every script in
scripts/ parses, and that the disk guard in particular is a file rather than an inline string.

Run: python -m pytest scripts/tests/test_supervisor_inline.py -q
"""
import glob, os, subprocess

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def test_every_shell_script_parses():
    for sh in sorted(glob.glob(os.path.join(SCRIPTS, "*.sh"))):
        r = subprocess.run(["bash", "-n", sh], capture_output=True, text=True)
        assert r.returncode == 0, f"{os.path.basename(sh)} does not parse:\n{r.stderr}"


def test_the_disk_guard_is_a_file_not_an_inline_string():
    guard = os.path.join(SCRIPTS, "disk_guard.sh")
    assert os.path.exists(guard), "the disk guard must stay a file so bash -n can parse it"
    sup = open(os.path.join(SCRIPTS, "supervisor.sh")).read()
    assert "disk_guard.sh" in sup
    assert "logs/disk_guard.pid; while true" not in sup, "the guard body is inline again; keep it in its own file"


def test_rdepth_is_exempt_from_the_stale_proxy_restart():
    """R-DEPTH makes no network call; restarting it for a stale proxy only destroys work (77 minutes, once)."""
    import os
    s = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "supervisor.sh")).read()
    blk = s.split("# 4c. RULES R-DEPTH", 1)[1].split("# 5. disk guard", 1)[0]
    assert '[ "$job" != rdepth ]' in blk, "R-DEPTH must not be killed for holding a stale proxy"
    assert "stale_proxy" in blk, "R-BEST does render, so the check must still exist for it"


def test_both_declared_experiments_are_supervised():
    import os
    s = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "supervisor.sh")).read()
    blk = s.split("# 4c. RULES R-DEPTH", 1)[1].split("# 5. disk guard", 1)[0]
    assert "for job in rdepth rdepth_part2 rbest rbest2" in blk
    assert "every population member has its +tta read" in blk, "R-BEST needs a completion test or it restarts forever"


def test_rdepth_part2_is_gated_on_an_ADMITTED_verdict_and_has_a_completion_test():
    """Part 2 is owed only if R-DEPTH admitted an off-centre window; and a queue with no completion test
    restarts forever, which is how a finished job silently burns four cores."""
    import os
    s = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "supervisor.sh")).read()
    blk = s.split("# 4c. RULES R-DEPTH", 1)[1].split("# 5. disk guard", 1)[0]
    assert "rdepth_part2" in blk
    assert "'ADMITTED'" in blk or '"ADMITTED"' in blk, "part 2 must not run on a PENDING or FAILED verdict"
    assert "part2_paused" in blk, "the queue must stay pausable by marker"
    assert 'grep -q "queue done"' in blk, "part 2 needs a completion test"


def test_ggp5_consensus_build_is_armed_and_cannot_fire_twice():
    """The hours between the last part-5 trace and the consensus build must not be spent waiting for a check-in."""
    import os
    s = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "supervisor.sh")).read()
    assert "ggp5_when_ready.sh" in s
    blk = s.split("# 4b2. RULES G-GP part 5", 1)[1].split("# 4c. RULES R-DEPTH", 1)[0]
    assert "cons_part5" in blk, "it must not rebuild a consensus that already exists"
    assert "pgrep -f" in blk, "two copies of the builder must not race"
    w = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ggp5_when_ready.sh")).read()
    assert "dense_paused" in w, "a paused queue must not trigger a build"
    assert 'have" -ge "$need' in w, "the build waits for every declared seed, not for some of them"
    assert "PART=5" in w and "ggp4_consensus.sh" in w, "it must use the declared builder, not a new one"


def test_the_check_in_runs_both_integrity_audits():
    """A truncated reverse map inflates the rule 5.5 margin, so it pushes toward false positives, and an unledgered
    read cannot be reconstructed once its maps are pruned. Neither can wait for someone to happen to look."""
    import os
    s = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "supervisor.sh")).read()
    assert "map_integrity.py" in s and "ledger_audit.py" in s
    blk = s.split("# 4b1. Integrity audits", 1)[1].split("# 4b3.", 1)[0]
    assert "SUSPECT" in blk, "a suspect map must reach the supervisor log, not only the json"
    assert "tail -40" not in blk, "reporting the whole log repeated the clean summary and buried the one line that matters"
    assert 'grep -n "^checked .* pairs;"' in blk, "only the LATEST audit is reported"
    assert "LEDGER AUDIT FAILED" in blk, "an unledgered read must be reported loudly"


def test_a_finished_dense_queue_is_not_resumed():
    """G-GP part 5 finished at 07:41 UTC and the block kept announcing 'dense queue resumed' afterwards: the loop
    started, found every seed done and exited, leaving a log line that read as if the campaign were still running."""
    import os
    s = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "supervisor.sh")).read()
    # Do NOT split on "done": the first occurrence is inside the ".done" marker name and truncates the block.
    blk = s.split("for spec in $DENSE;", 1)[1].split("\ndone\n", 1)[0]
    assert "alldone" in blk and '[ "$alldone" = yes ] && continue' in blk
    assert "_dense/logs" in blk, "completion is judged by the loops' own per-seed markers"


def _sup():
    import os
    return open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "supervisor.sh")).read()


def test_the_reduced_budget_read_loop_covers_rs2_as_well_as_small():
    s = _sup()
    assert "RSMALL_SUFFIXES:-_small _rs2" in s, "R-SMALL-2 writes into _rs2 and needs a reader"
    assert "sd=$D/patches/${sc}${suf}" in s, "the patch dir must use the suffix variable, not a literal"


def test_the_suffix_loop_is_closed_and_the_script_parses():
    import subprocess, os, sys
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "supervisor.sh")
    assert subprocess.run(["bash", "-n", p], capture_output=True).returncode == 0


def test_the_pid_file_and_log_are_per_suffix_so_two_loops_cannot_collide():
    s = _sup()
    i = s.index("RSMALL_SUFFIXES")
    blk = s[i:i + 2500]
    assert "read_loop_${sc}${suf}.log" in blk, "the log name must carry the suffix"
    assert "spidf=$sd/read_loop.pid" in blk and "sd=$D/patches/${sc}${suf}" in blk
    assert "read_loop_${sc}_small.log" not in blk, "the literal _small log name would collide across suffixes"


def test_the_1203_subset_queue_stands_down_when_the_full_phase1_queue_is_alive():
    s = _sup()
    i = s.index("n1203=")
    blk = s[i:i + 1600]
    assert "rcrest_power.pid" in blk, "the subset queue must check the full queue's pid, not just its own marker"
    assert "stands down" in blk
    # the guard must come BEFORE the block that starts the subset queue
    assert blk.index("rcrest_power.pid") < blk.index("rcrest_power_1203.sh")


def test_one_queue_is_the_invariant_not_the_pause_marker():
    s = _sup()
    i = s.index("n1203=")
    blk = s[i:i + 1600]
    assert "ONE QUEUE" in blk, "the reason must be recorded where the guard lives"


def test_the_supervisor_sweeps_killed_reads_leftovers_every_checkin():
    s = _sup()
    assert "sweep_partial_reads.py --go" in s
    # it must run as a standalone statement, not inside the map-integrity case block
    i = s.index("sweep_partial_reads.py --go")
    assert "case \"$summary\"" not in s[i - 400:i], "must not be inserted inside the case statement"
