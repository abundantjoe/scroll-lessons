"""Protocol 9 must not be debugged while a candidate is on the table.

The dry run exists because three separate path bugs were found in this project's scripts on 2026-09-19 alone.
It runs nothing, checks every input, and prints every command.
"""
import os
import subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P9 = os.path.join(HERE, "protocol9.sh")


def run_dry(patch):
    env = dict(os.environ, P9_DRY="1")
    return subprocess.run(["bash", P9, "PHerc0826", "20250821151701", "9.362", patch],
                          capture_output=True, text=True, env=env)


def test_step_six_reads_the_candidate_where_it_actually_lives(tmp_path):
    """It used to look in patches/<scroll>, which is wrong for every surface the concentrated campaign produces."""
    src = open(P9).read()
    assert 'run_patch_dir.py "$home"' in src, "step 6 must use the candidate's own parent directory"
    assert "run_patch_dir.py $D/patches/$sc " not in src, "the hardcoded patches/<scroll> path is back"


def test_dry_run_runs_nothing_and_prints_every_command(tmp_path):
    patch = tmp_path / "auto_trace_x"
    patch.mkdir()
    for n in "xyz":
        (patch / (n + ".tif")).write_bytes(b"")
    out = run_dry(str(patch))
    text = out.stdout + out.stderr
    assert "WOULD RUN" in text
    for step in ("vc_tools.sh flatten", "mesh_distortion.py", "rcross.sh", "run_patch_dir.py"):
        assert step in text, "the dry run must print the %s step" % step
    assert "hybrid_3d2d-seed43" in text, "the confirmatory reader must appear"
    assert not (tmp_path / "flat").exists()


def test_dry_run_fails_loudly_when_an_input_is_missing(tmp_path):
    patch = tmp_path / "auto_trace_y"
    patch.mkdir()                       # deliberately no x/y/z tifs
    out = run_dry(str(patch))
    assert out.returncode != 0
    assert "MISSING" in (out.stdout + out.stderr)


def test_the_judgement_steps_are_printed_and_not_automated():
    src = open(P9).read()
    for phrase in ("Never lower the count", "never resample the map", "Stop conditions"):
        assert phrase in src
    assert "SUBMISSION READY" in src, "the script must state when the owner may be told"


# ---------- the launcher that derives its own arguments

def test_launcher_derives_scroll_um_and_volume_and_never_hardcodes_a_volume_id():
    """At the moment a candidate appears the one thing that must not go wrong is composing the command."""
    import re
    src = open(os.path.join(HERE, "protocol9_for.sh")).read()
    code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
    assert "COVERAGE" in code, "the volume id must come from the supervisor, not from memory"
    assert not re.search(r"2025\d{10}", code), "a literal volume id is present in executable code"
    assert "um_per_px" in code, "um must come from the read's own stats"
    assert "sc=${dir%%_*}" in code, "_cons_partN / _small / _dense are the same scroll"


def test_launcher_always_dry_runs_first_and_needs_an_explicit_go():
    src = open(os.path.join(HERE, "protocol9_for.sh")).read()
    assert "P9_DRY=1" in src
    i, j = src.index("P9_DRY=1"), src.index('"$go" = "--go"')
    assert i < j, "the dry run must come before the decision to execute"
    assert "DRY RUN FAILED" in src, "a failed dry run must stop it"


def test_launcher_refuses_an_unknown_scroll(tmp_path):
    import json, subprocess
    d = tmp_path / "NoSuchScroll_cons_part9" / "auto_trace_1" / "read_t"
    d.mkdir(parents=True)
    (d / "read_stats.json").write_text(json.dumps({"um_per_px": 9.362, "verdict": "BLANK"}))
    out = subprocess.run(["bash", os.path.join(HERE, "protocol9_for.sh"), str(d / "read_stats.json")],
                         capture_output=True, text=True)
    assert out.returncode != 0
    assert "no COVERAGE volume id" in (out.stdout + out.stderr)
