# Provenance: Project HERCULES | owner the owner | [id removed]
"""Integration tests of the D2 trainer on SYNTHETIC data with the real base checkpoint (numbers only).

1. determinism: the same config and data twice -> identical loss curves and bitwise-identical weights (fp32, 1 thread),
   for P128-like and P384-like (full and stitched forward, NULL, REV, rotations, micro-batching) configs;
2. resume: an interrupted run resumed from (a) the local state and (b) ONLY the remote git shards after the local run
   directory is deleted gives the same loss curve and bitwise-identical final weights as an uninterrupted run;
3. D3 equivalence: tools/d3/d3_train.py (paths redirected to synthetic pools) and this trainer in D3 layout give
   identical per-step losses and identical final weights for CTRL, FA, NULLA and REVA;
4. bf16 training is refused without a passing AMX gate record.
Needs /opt/hv-ink and /work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth. Run:
/opt/hv-ink/bin/python -m pytest -q tests/sib_trainer_integration_test.py   (about 10-15 min on 4 cores)"""
import json
import os
import shutil
import subprocess
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TD = os.path.join(ROOT, "tools", "sib", "trainer")
sys.path.insert(0, TD)
import d2_data  # noqa: E402

PY = "/opt/hv-ink/bin/python"
CK = "/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth"
TR = os.path.join(TD, "d2_train.py")
pytestmark = pytest.mark.skipif(not (os.path.exists(PY) and os.path.exists(CK)), reason="needs hv-ink env + base ckpt")
torch = pytest.importorskip("torch")


def run(args, threads=1, check=True):
    env = dict(os.environ, OMP_NUM_THREADS=str(threads), MKL_NUM_THREADS=str(threads))
    r = subprocess.run([PY, *args], capture_output=True, text=True, env=env)
    if check and r.returncode != 0:
        raise AssertionError(f"rc={r.returncode}\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
    return r


def make_cfg(path, *extra):
    run([TR, "make-config", "--out", path, *extra])
    return path


def losses(out):
    return [json.loads(l)["loss"] for l in open(os.path.join(out, "train_log.jsonl")) if '"loss"' in l]


def weights(out):
    return torch.load(os.path.join(out, "model_final.pth"), map_location="cpu", weights_only=False)["model"]


def same_weights(a, b):
    return a.keys() == b.keys() and all(torch.equal(a[k], b[k]) for k in a)


@pytest.fixture(scope="module")
def syn(tmp_path_factory):
    d = tmp_path_factory.mktemp("syn")
    return dict(r400=d2_data.write_synthetic_registry(str(d / "r400"), n=12, size=400, seed=11, shard_n=6),
                r560=d2_data.write_synthetic_registry(str(d / "r560"), n=6, size=560, seed=12, shard_n=6),
                d=d)


@pytest.mark.parametrize("name,flags", [
    ("p128", ["--arm", "P128", "--batch", "2", "--steps", "3"]),
    ("p384_null_micro", ["--arm", "NULL", "--batch", "2", "--micro-batch", "1", "--steps", "2"]),
    ("p384_rev_stitched", ["--arm", "REV", "--batch", "1", "--steps", "2", "--forward", "stitched"]),
])
def test_determinism_twice_identical(syn, tmp_path, name, flags):
    src = syn["r560"] if "p384" in name else syn["r400"]
    cfg = make_cfg(str(tmp_path / "c.json"), "--seed", "3", "--threads", "1", "--log-every", "1",
                   "--source", f"syn=pairs:{src}", *flags)
    a, b = str(tmp_path / "a"), str(tmp_path / "b")
    run([TR, "train", "--config", cfg, "--out", a])
    run([TR, "train", "--config", cfg, "--out", b])
    la, lb = losses(a), losses(b)
    assert len(la) == json.load(open(cfg))["steps"] and la == lb
    assert same_weights(weights(a), weights(b))
    sa = json.load(open(os.path.join(a, "summary.json")))
    if "null" in name:
        assert sa["checks"]["null_fixed_points"] == 0
    if "rev" in name:
        assert sa["checks"]["rev_syn_exact_depth_reverse"] is True
    ra = json.load(open(os.path.join(a, "checkpoint_registry.json")))
    rb = json.load(open(os.path.join(b, "checkpoint_registry.json")))
    assert ra["patch_registry"]["sha256"] == rb["patch_registry"]["sha256"]
    assert ra["config_sha256"] == rb["config_sha256"] and ra["patch_registry"]["fl09_ready"]
    assert ra["model_final"]["sha256"] == rb["model_final"]["sha256"]


def test_paired_sampling_p384_null_rev(syn, tmp_path):
    """Same seed and pool: P384, NULL and REV draw the identical (patch, z offset, rotation) sequence."""
    dig, los = {}, {}
    for arm in ("P384", "NULL", "REV"):
        cfg = make_cfg(str(tmp_path / f"{arm}.json"), "--arm", arm, "--seed", "7", "--threads", "1", "--batch", "2",
                       "--steps", "2", "--log-every", "1", "--source", f"syn=pairs:{syn['r560']}")
        run([TR, "train", "--config", cfg, "--out", str(tmp_path / arm)])
        s = json.load(open(tmp_path / arm / "summary.json"))
        dig[arm], los[arm] = s["sample_digest_final"], s["losses"]
    assert dig["P384"] == dig["NULL"] == dig["REV"] and len(dig["P384"]) == 64
    assert los["P384"] != los["NULL"] and los["P384"] != los["REV"]


def test_subtile_p128_covers_grid(syn, tmp_path):
    """P128 with --subtile on 400 px patches: 9 sub-tiles per patch, every drawn index maps to a stored patch."""
    cfg = make_cfg(str(tmp_path / "c.json"), "--arm", "P128", "--seed", "2", "--threads", "1", "--batch", "4",
                   "--steps", "2", "--log-every", "1", "--subtile", "--source", f"syn=pairs:{syn['r400']}")
    out = str(tmp_path / "o")
    run([TR, "train", "--config", cfg, "--out", out])
    s = json.load(open(os.path.join(out, "summary.json")))
    assert s["checks"]["subtiles_per_patch"] == {"syn": 9}
    with np.load(os.path.join(out, "patch_registry.npz")) as z:
        assert int(z["s0_draws"].sum()) == 8


def test_seed_changes_the_run(syn, tmp_path):
    outs = []
    for s in ("3", "4"):
        cfg = make_cfg(str(tmp_path / f"c{s}.json"), "--arm", "P128", "--seed", s, "--threads", "1", "--batch", "2",
                       "--steps", "1", "--log-every", "1", "--source", f"syn=pairs:{syn['r400']}")
        run([TR, "train", "--config", cfg, "--out", str(tmp_path / s)])
        outs.append(losses(str(tmp_path / s)))
    assert outs[0] != outs[1]


def test_resume_local_and_remote_bitwise(syn, tmp_path):
    remote = str(tmp_path / "remote.git")
    subprocess.run(["git", "init", "-q", "--bare", remote], check=True)
    ref = "refs/heads/test-ckpt"
    common = ["--arm", "P128", "--seed", "5", "--threads", "1", "--batch", "2", "--steps", "5", "--log-every", "1",
              "--ckpt-every", "2", "--source", f"syn=pairs:{syn['r400']}"]
    cfg_ref = make_cfg(str(tmp_path / "cref.json"), *common)
    cfg_rem = make_cfg(str(tmp_path / "crem.json"), *common, "--remote-ref", ref)
    ref_out = str(tmp_path / "ref")
    run([TR, "train", "--config", cfg_ref, "--out", ref_out])
    # (a) local: die after step 3 (last save at step 2), re-run resumes from the local state
    loc = str(tmp_path / "loc")
    r = run([TR, "train", "--config", cfg_ref, "--out", loc, "--die-after", "3"], check=False)
    assert r.returncode == 99
    run([TR, "train", "--config", cfg_ref, "--out", loc])
    s = json.load(open(os.path.join(loc, "summary.json")))
    assert [x["from_step"] for x in s["resumptions"]] == [2] and s["resumptions"][0]["source"] == "local"
    assert s["losses"] == json.load(open(os.path.join(ref_out, "summary.json")))["losses"]
    assert same_weights(weights(loc), weights(ref_out))
    # (b) remote: die after step 3 with shards pushed at steps 2; delete the run dir; resume from the shards only
    rem = str(tmp_path / "rem")
    r = run([TR, "train", "--config", cfg_rem, "--out", rem, "--die-after", "3", "--remote-url", remote], check=False)
    assert r.returncode == 99
    shutil.rmtree(rem)
    run([TR, "train", "--config", cfg_rem, "--out", rem, "--remote-url", remote])
    s = json.load(open(os.path.join(rem, "summary.json")))
    assert len(s["resumptions"]) == 1 and s["resumptions"][0]["source"].startswith(f"remote {ref}")
    assert s["resumptions"][0]["from_step"] == 2
    assert s["losses"] == json.load(open(os.path.join(ref_out, "summary.json")))["losses"]
    assert same_weights(weights(rem), weights(ref_out))
    reg = json.load(open(os.path.join(rem, "checkpoint_registry.json")))
    assert reg["model_final"]["remote"]["pushed"]
    cnt = subprocess.run(["git", "--git-dir", remote, "rev-list", "--count", ref], capture_output=True, text=True)
    assert cnt.stdout.strip() == "1"          # single orphan commit (final weights replaced the resume state)


def _patched_d3(tmp_path, fa, rp):
    src = open(os.path.join(ROOT, "tools", "d3", "d3_train.py")).read()
    assert src.count('POOL_FA, POOL_RP = "/work/d3/pool_fa", "/work/d3/pool_replay"') == 1
    src = src.replace('POOL_FA, POOL_RP = "/work/d3/pool_fa", "/work/d3/pool_replay"',
                      f'POOL_FA, POOL_RP = "{fa}", "{rp}"')
    p = str(tmp_path / "d3_train_synthetic_paths.py")
    open(p, "w").write(src)
    return p


@pytest.mark.parametrize("arm", ["CTRL", "FA", "NULLA", "REVA"])
def test_d3_equivalence(tmp_path, arm):
    fa = d2_data.write_synthetic_d3_pool(str(tmp_path / "fa"), 10, seed=21)
    rp = d2_data.write_synthetic_d3_pool(str(tmp_path / "rp"), 12, seed=22)
    d3 = _patched_d3(tmp_path, fa, rp)
    steps = "3"
    d3_out = str(tmp_path / "d3")
    run([d3, "--arm", arm, "--steps", steps, "--out", d3_out, "--log-every", "1", "--ckpt-every", "0"], threads=3)
    if arm == "CTRL":
        srcs = ["--source", f"rp=d3_pool:{rp}:replay:8:1"]
    else:
        srcs = ["--source", f"fa=d3_pool:{fa}:train:4:0", "--source", f"rp=d3_pool:{rp}:replay:4:1"]
    flags = dict(CTRL=[], FA=[], NULLA=["--null"], REVA=["--rev"])[arm]
    cfg = make_cfg(str(tmp_path / "c.json"), "--arm", f"D3{arm}", "--seed", "20260925", "--tile", "128",
                   "--no-rot24", "--no-null", "--no-rev", *flags, "--batch", "8", "--steps", steps,
                   "--threads", "3", "--log-every", "1", "--ckpt-every", "0", *srcs)
    d2_out = str(tmp_path / "d2")
    run([TR, "train", "--config", cfg, "--out", d2_out], threads=3)
    l3 = [json.loads(l)["loss"] for l in open(os.path.join(d3_out, "train_log.jsonl")) if '"loss"' in l]
    l2 = losses(d2_out)
    assert len(l3) == int(steps) and l3 == l2, (l3, l2)
    assert same_weights(weights(d3_out), weights(d2_out))


def test_bf16_training_refused_without_gate(syn, tmp_path):
    cfg = make_cfg(str(tmp_path / "c.json"), "--arm", "P128", "--seed", "1", "--threads", "1", "--batch", "1",
                   "--steps", "1", "--precision", "bf16", "--source", f"syn=pairs:{syn['r400']}")
    r = run([TR, "train", "--config", cfg, "--out", str(tmp_path / "o")], check=False)
    assert r.returncode != 0 and "bf16 training refused" in (r.stdout + r.stderr)
    gate = tmp_path / "gate.json"
    gate.write_text(json.dumps({"pass": False}))
    cfg = make_cfg(str(tmp_path / "c2.json"), "--arm", "P128", "--seed", "1", "--threads", "1", "--batch", "1",
                   "--steps", "1", "--precision", "bf16", "--amx-gate", str(gate), "--source", f"syn=pairs:{syn['r400']}")
    r = run([TR, "train", "--config", cfg, "--out", str(tmp_path / "o2")], check=False)
    assert r.returncode != 0 and "pass: true" in (r.stdout + r.stderr)
    # the bench path (throughput only, no model written) runs bf16
    r = run([TR, "bench", "--config", cfg, "--out", str(tmp_path / "b"), "--steps", "1", "--warmup", "0"])
    b = json.load(open(tmp_path / "b" / "bench.json"))
    assert b["precision"] == "bf16" and not os.path.exists(tmp_path / "b" / "model_final.pth")
