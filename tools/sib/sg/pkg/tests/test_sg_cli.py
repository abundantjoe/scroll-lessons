# Provenance: Project HERCULES | owner the owner | [id removed]
"""End-to-end tests of hercules.sg.cli (synthetic inputs only)."""

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from hercules.sg import synth as S

ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src")}


def run(*args):
    return subprocess.run([sys.executable, "-m", "hercules.sg.cli", *map(str, args)], capture_output=True, text=True,
                          cwd=ROOT, env=ENV)


def test_cli_synthetic_passes(tmp_path):
    out = tmp_path / "r.json"
    p = run("--synthetic", "--out", out)
    assert p.returncode == 0, p.stderr
    r = json.loads(out.read_text())
    assert r["overall"] == "PASS" and "sha256" in p.stdout


def test_cli_failing_inputs_exit_1(tmp_path):
    inp = S.passing_inputs(n_null_disc=200, n_null_sg=40)
    inp.pop("_sealers_for_band")
    inp["batches"][0]["canary"]["score"] = 0.1
    f = tmp_path / "in.json"
    f.write_text(json.dumps(inp))
    out = tmp_path / "r.json"
    p = run(f, "--out", out)
    r = json.loads(out.read_text())
    assert p.returncode == 1 and r["items"]["2"]["status"] == "FAIL" and r["not_passed"] == ["2"]


def test_cli_copy_test_from_npz(tmp_path):
    inp = S.passing_inputs()
    inp.pop("_sealers_for_band")
    inp.pop("copy_test")
    f = tmp_path / "in.json"
    f.write_text(json.dumps(inp))
    rng = np.random.default_rng(0)
    np.savez(tmp_path / "c.npz", **{f"l{i:02d}": rng.random((30, 30)) for i in range(21)})
    np.savez(tmp_path / "p.npz", **{f"p{i:02d}": rng.random((40, 40)) for i in range(4)})
    out = tmp_path / "r.json"
    p = run(f, "--out", out, "--crops", tmp_path / "c.npz", "--patches", tmp_path / "p.npz")
    assert p.returncode == 0, p.stdout + p.stderr
    assert json.loads(out.read_text())["items"]["7"]["n_letters"] == 21


def test_cli_error_exit_2(tmp_path):
    f = tmp_path / "in.json"
    f.write_text(json.dumps({"no": "metadata"}))
    assert run(f, "--out", tmp_path / "r.json").returncode == 2
