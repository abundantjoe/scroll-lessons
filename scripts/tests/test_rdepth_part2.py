"""RULES R-DEPTH part 2: the runner must take its volume ids from the supervisor, never from a literal.

A guessed volume id has already produced one wrong read in this project (PHerc1203) and was about to produce a
second (PHerc0358: the guess 20250809160000 is not a volume at all; the real one is 20250821151737). This pins the
rule rather than the values, so the test keeps working when a scroll is added to COVERAGE.
"""
import os
import re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUP = os.path.join(HERE, "supervisor.sh")
RUNNER = os.path.join(HERE, "rdepth_part2.sh")


def coverage_map():
    cov = re.search(r'COVERAGE=\$\{COVERAGE:-"([^"]*)"\}', open(SUP).read()).group(1)
    return {p.split(":")[0]: p.split(":")[1] for p in cov.split()}


def code_only(path):
    """Executable lines only: a comment may quote a wrong id as the record of how it was caught."""
    return "\n".join(l for l in open(path).read().splitlines() if not l.lstrip().startswith("#"))


def test_the_runner_parses_coverage_and_holds_no_literal_volume_id():
    src = code_only(RUNNER)
    assert "COVERAGE" in src, "the runner must read the supervisor's COVERAGE string"
    for vol in coverage_map().values():
        assert vol not in src, "volume id %s is hardcoded in the runner" % vol
    assert not re.search(r"2025\d{10}", src), "a literal volume id is present in executable code"


def test_coverage_supplies_every_scroll_the_declared_set_names():
    import json
    D = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")
    path = os.path.join(D, "gates", "rdepth", "part2_set.json")
    if not os.path.exists(path):
        return
    vol = coverage_map()
    missing = sorted({r["scroll"] for r in json.load(open(path)) if r["scroll"].split("_")[0] not in vol})
    assert not missing, "no COVERAGE volume id for %s" % missing


def test_the_runner_reads_both_declared_windows_and_pauses_on_a_marker():
    src = code_only(RUNNER)
    assert "for w in high low" in src, "both off-centre windows are owed, not just the admitted one"
    assert "part2_paused" in src, "a long queue must be pausable without killing it"
    assert "--reread" in src, "the centre read exists under another dir tag and would otherwise skip the patch"
    assert "--no-tta" in src, "screening recipe is plain; TTA is reserved for protocol 9"
