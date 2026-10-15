# Provenance: Project HERCULES | owner the owner | [id removed]
"""The planted-fault runner catches every fault in small random worlds with no false alarm."""

import json

from hercules.tribunal import faults as F
from hercules.tribunal import runner as Rn


def test_runner_small_suite_catches_everything(tmp_path):
    out = tmp_path / "suite.json"
    rc = Rn.main(["--worlds", "3", "--scale-trials", "12", "--seed", "4242", "--out", str(out)])
    s = json.loads(out.read_text())
    assert rc == 0 and s["verdict"] == "PASS"
    for f in F.FAULTS:
        assert s["faults"][f]["n"] == 3 and s["faults"][f]["catch_rate"] == 1.0
        assert s["faults"][f]["other_checks_fired"] == []  # clean attribution
    assert s["clean"]["false_alarm_rate"] == 0.0
    r = s["retrace_at_20vox"]
    assert r["caught"] == r["n"] == 12 and r["neighbour_false_alarms"] == 0 and r["far_same_sheet_false_alarms"] == 0


def test_runner_verdict_fails_on_a_miss():
    gate = [{"case": f, "passed": True, "failed": []} for f in F.FAULTS] + [{"case": "clean", "passed": True, "failed": []}]
    s = Rn.summarise(gate, [])
    assert s["verdict"] == "FAIL" and all(v["catch_rate"] == 0.0 for v in s["faults"].values())
