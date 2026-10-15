# Provenance: Project HERCULES | owner the owner | [id removed]
"""DIST-FT layer tests on SYNTHETIC data only (d2_data.write_synthetic_registry). Numbers only.

Run: /opt/hv-ink/bin/python -m pytest -q -p no:cacheprovider tools/sib/dev-distft/tests/test_distft.py"""
import copy
import json
import os
import sys

import numpy as np
import pytest
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import distft  # noqa: E402
import d2_data  # noqa: E402  (pinned, via distft)
import d2_train  # noqa: E402

PINNED_TRAINER = d2_train.Trainer          # captured before any use_distft_trainer()

# several trainers are built in one test process; torch allows set_num_interop_threads only once per process
torch.set_num_interop_threads(1)
torch.set_num_interop_threads = lambda n: None if n == 1 else (_ for _ in ()).throw(RuntimeError(n))


def cfg_for(tmp, reg, arm="DIST-FT", target="soft", seed=11, steps=3, batch=2, extra=()):
    out = os.path.join(tmp, f"cfg_{arm}_{target}_{seed}_{steps}.json")
    distft.make_config(["--arm", arm, "--target", target, "--seed", str(seed), "--out", out,
                        "--batch", str(batch), "--steps", str(steps), "--threads", "1", "--ckpt-every", "2",
                        "--log-every", "1", "--subtile", "--source", f"syn=pairs:{reg}", *extra])
    return json.load(open(out))


@pytest.fixture(scope="module")
def reg(tmp_path_factory):
    d = str(tmp_path_factory.mktemp("syn"))
    return d2_data.write_synthetic_registry(d, 6, 384, 5, source="synthetic", shard_n=4)


@pytest.fixture(scope="module")
def tmp(tmp_path_factory):
    return str(tmp_path_factory.mktemp("work"))


def test_pinned_hashes():
    assert distft.verify_pinned() == distft.PINNED


def test_soft_source_alignment(reg):
    src = distft.load_soft_source(dict(name="syn", kind="pairs", path=reg))
    pin = d2_data.load_source(dict(name="syn", kind="pairs", path=reg))
    k, s = d2_data.labels_from_target(src.ink, src.sup)
    assert np.array_equal(k, pin.ink) and np.array_equal(s, pin.sup)
    assert src.ink.dtype == np.uint8 and len(np.unique(src.ink)) > 100          # continuous, not binary
    band = (src.ink > 100) & (src.ink < 150) & (src.sup > 0)
    assert band.sum() > 0 and src.meta["distft_target"]["n_band_px_now_supervised"] == int(band.sum())
    assert np.array_equal(src.images, pin.images)


def test_soft_loss_input_equals_official_on_binary():
    from vesuvius.ink_detection.training.train import prepare_loss_inputs
    g = torch.Generator().manual_seed(0)
    lab = (torch.rand(3, 1, 17, 128, 128, generator=g) > 0.7).float()
    sup = (torch.rand(3, 1, 17, 128, 128, generator=g) > 0.2).float()
    b = dict(inklabels=lab, supervision_mask=sup)
    for shape in ((3, 1, 128, 128), (3, 1, 64, 64)):
        p = torch.randn(shape, generator=g)
        o = prepare_loss_inputs(p, b, mode="flat")
        s = distft.soft_prepare_loss_inputs(p, b, mode="flat")
        assert all(torch.equal(x, y) for x, y in zip(o, s))
        pl = [torch.randn(shape, generator=g), torch.randn(3, 1, 32, 32, generator=g)]
        o = prepare_loss_inputs(pl, b, mode="flat"); s = distft.soft_prepare_loss_inputs(pl, b, mode="flat")
        assert torch.equal(o[1], s[1]) and torch.equal(o[2], s[2])
    soft = dict(inklabels=(torch.rand(2, 1, 1, 128, 128, generator=g) * 0.9).expand(2, 1, 17, 128, 128),
                supervision_mask=sup[:2])
    t = distft.soft_prepare_loss_inputs(torch.randn(2, 1, 128, 128), soft, mode="flat")[1]
    assert torch.allclose(t, soft["inklabels"][:, :, 0]) and float(t.max()) < 1.0


@pytest.fixture(scope="module")
def trainers(reg, tmp):
    cfg = cfg_for(tmp, reg, target="hard")
    pin = PINNED_TRAINER(copy.deepcopy(cfg), os.path.join(tmp, "p"))
    mine = distft.DistFTTrainer(copy.deepcopy(cfg), os.path.join(tmp, "m"))
    return pin, mine


class FixedK:
    """Stands in for the rotation generator: always draws angle index k."""

    def __init__(self, k):
        self.k = k

    def integers(self, lo, hi):
        assert (lo, hi) == (0, 24)
        return self.k


def test_rotate_equals_pinned_on_binary(trainers):
    pin, mine = trainers
    rng = np.random.default_rng(3)
    R = pin.R
    for k in range(24):
        img = rng.integers(0, 255, (17, R, R), dtype=np.uint8)
        ink = (rng.random((R, R)) > 0.6).astype(np.uint8); sup = (rng.random((R, R)) > 0.2).astype(np.uint8)
        for t in (pin, mine):
            t.rot_gen = FixedK(k)
        a = pin._rotate(img, ink, sup); b = mine._rotate(img, ink, sup)
        assert a[3] == b[3] == k
        assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1]) and np.array_equal(a[2], b[2])


def test_rotate_soft_keeps_values(trainers):
    _, mine = trainers
    R = mine.R
    rng = np.random.default_rng(4)
    ink = rng.integers(0, 256, (R, R), dtype=np.uint8); sup = np.ones((R, R), np.uint8)
    for k in (1, 5, 7):
        mine.rot_gen = FixedK(k)
        _, a, b, _ = mine._rotate(np.zeros((17, R, R), np.uint8), ink, sup)
        assert set(np.unique(a[b > 0])).issubset(set(np.unique(ink)))
        assert len(np.unique(a[b > 0])) > 50                       # a & b would have left only {0, 1}


def test_hard_target_through_layer_is_bitwise_pinned(reg, tmp):
    """target=hard through DistFTTrainer == the pinned Trainer bitwise (losses and weights, 3 steps, rot24)."""
    cfg = cfg_for(tmp, reg, target="hard", steps=3)
    res = []
    for cls in (PINNED_TRAINER, distft.DistFTTrainer):
        torch.use_deterministic_algorithms(True)
        t = cls(copy.deepcopy(cfg), os.path.join(tmp, "eq"))
        losses = [t.train_step(i)[0] for i in range(3)]
        res.append((losses, {k: v.clone() for k, v in t.model.state_dict().items()}, t.sample_digest))
    assert res[0][0] == res[1][0] and res[0][2] == res[1][2]
    assert all(torch.equal(res[0][1][k], res[1][1][k]) for k in res[0][1])


def test_soft_batch_and_aug_check(reg, tmp):
    cfg = cfg_for(tmp, reg, target="soft", steps=2)
    t = distft.DistFTTrainer(copy.deepcopy(cfg), os.path.join(tmp, "s"))
    for _ in range(4):
        b, _ = t.make_batch()
        v = b["inklabels"][b["supervision_mask"] > 0]
        assert float(v.min()) >= 0.0 and float(v.max()) <= 1.0
        assert len(torch.unique(v)) > 20
        assert torch.all(torch.isin(torch.round(v * 255), torch.arange(256).float()))
    assert t.aug_label_checks["samples"] == 8 and t.aug_label_checks["value_multiset_changed"] == 0
    loss, gn, _, _ = t.train_step(0)
    assert np.isfinite(loss) and np.isfinite(gn)


def test_null_seed_fixed_and_rev(reg, tmp):
    perms = []
    for seed in (11, 12):
        t = distft.DistFTTrainer(cfg_for(tmp, reg, arm="DIST-FT-NULL", seed=seed), os.path.join(tmp, "n"))
        assert t.checks["null_fixed_points"] == 0
        perms.append(t.meta["derangement"]["perm_sha256"])
    assert perms[0] == perms[1]
    n = 6
    drng = np.random.default_rng(distft.NULL_SEED)
    while True:
        p = drng.permutation(n)
        if not np.any(p == np.arange(n)):
            break
    import hashlib
    assert perms[0] == hashlib.sha256(p.astype(np.int64).tobytes()).hexdigest()
    base = distft.load_soft_source(dict(name="syn", kind="pairs", path=reg))
    assert np.array_equal(t.sources[0].ink, base.ink[p]) and np.array_equal(t.sources[0].sup, base.sup[p])
    r = distft.DistFTTrainer(cfg_for(tmp, reg, arm="DIST-FT-REV"), os.path.join(tmp, "r"))
    assert r.checks["rev_syn_exact_depth_reverse"] is True
    assert np.array_equal(r.sources[0].images, base.images[:, ::-1])
    assert np.array_equal(r.sources[0].ink, base.ink)
    # paired sampling: recipe, NULL and REV draw the same (patch, z, rotation) sequence
    ds = []
    for arm in ("DIST-FT", "DIST-FT-NULL", "DIST-FT-REV"):
        t = distft.DistFTTrainer(cfg_for(tmp, reg, arm=arm, seed=11), os.path.join(tmp, "d"))
        for _ in range(3):
            t.make_batch()
        ds.append(t.sample_digest)
    assert ds[0] == ds[1] == ds[2]


def test_null_seed_refused(tmp, reg):
    with pytest.raises(SystemExit):
        distft.make_config(["--arm", "DIST-FT-NULL", "--null-seed", "1", "--out", os.path.join(tmp, "x.json"),
                            "--source", f"syn=pairs:{reg}"])
    with pytest.raises(SystemExit):
        distft.make_config(["--arm", "DIST-FT", "--remote-ref", "refs/heads/x", "--out",
                            os.path.join(tmp, "x.json"), "--source", f"syn=pairs:{reg}"])


def test_resume_bitwise(reg, tmp):
    distft.use_distft_trainer()
    try:
        cfg = cfg_for(tmp, reg, arm="DIST-FT", steps=4)
        a = d2_train.run_train(copy.deepcopy(cfg), os.path.join(tmp, "full"))
        import subprocess
        out = os.path.join(tmp, "killed")
        cp = os.path.join(tmp, "cfg_resume.json")
        json.dump(cfg, open(cp, "w"))
        r = subprocess.run([sys.executable, distft.__file__, "train", "--config", cp, "--out", out,
                            "--die-after", "3"], capture_output=True, text=True)
        assert r.returncode == 99, r.stderr[-2000:]
        assert os.path.exists(os.path.join(out, "resume_latest.pth"))
        b = d2_train.run_train(copy.deepcopy(cfg), out)
        assert a["losses"] == b["losses"] and len(b["resumptions"]) == 1 and b["resumptions"][0]["from_step"] == 2
        wa = torch.load(os.path.join(tmp, "full", "model_final.pth"), weights_only=False)["model"]
        wb = torch.load(os.path.join(out, "model_final.pth"), weights_only=False)["model"]
        assert all(torch.equal(wa[k], wb[k]) for k in wa)
        assert a["checks"]["distft_aug_label_value_multiset"]["value_multiset_changed"] == 0
    finally:
        d2_train.Trainer = PINNED_TRAINER


def _rule_labels(t, v):
    lab = np.full(t.shape, 255, np.uint8)
    lab[(t >= 150) & v] = 1
    lab[(t <= 100) & v] = 0
    return lab


def test_soft_loader_stagec(tmp_path):
    """Synthetic stage-C layout (pairs0814 stage_c.py schema as read by the pinned load_stagec)."""
    rng = np.random.default_rng(8)
    root = str(tmp_path / "stagec"); os.makedirs(root)
    shards, allp = [], []
    for s in range(2):
        n = 3
        ref9 = rng.integers(0, 256, (n, 384, 384), dtype=np.uint8)
        valid = rng.random((n, 384, 384)) > 0.1
        pid = np.array([f"p{s}_{i}" for i in range(n)]); allp += list(pid)
        f = f"shard_{s}.npz"
        np.savez(os.path.join(root, f), images=rng.integers(0, 255, (n, 21, 384, 384), dtype=np.uint8), ref9=ref9,
                 labels=_rule_labels(ref9, valid), valid=valid, xyz=rng.random((n, 17, 17, 3)).astype(np.float32),
                 patch_id=pid, segment=np.array(["SEG"] * n))
        shards.append(dict(shard=f, n=n, bytes=os.path.getsize(os.path.join(root, f)),
                           sha256=d2_data.sha256_file(os.path.join(root, f)), patch_ids=list(pid)))
    json.dump(dict(shards=shards), open(os.path.join(root, "shards.json"), "w"))
    allow = str(tmp_path / "allow.json"); json.dump([p for p in allp if p != "p0_1"], open(allow, "w"))
    for aid in (None, allow):
        spec = dict(name="c", kind="stagec", path=root, **({"allow_ids": aid} if aid else {}))
        src = distft.load_soft_source(spec)
        keep = [i for i, p in enumerate(allp) if aid is None or p != "p0_1"]
        ref = np.concatenate([np.load(os.path.join(root, f"shard_{s}.npz"))["ref9"] for s in range(2)])[keep]
        val = np.concatenate([np.load(os.path.join(root, f"shard_{s}.npz"))["valid"] for s in range(2)])[keep]
        assert src.patch_id == [allp[i] for i in keep]
        assert np.array_equal(src.ink, ref) and np.array_equal(src.sup, val.astype(np.uint8))


def test_soft_loader_tilegrid3(tmp_path):
    """Synthetic pairs0139 tile-grid layout; 3 x 3 mosaics must place the soft map exactly like the pinned labels."""
    rng = np.random.default_rng(9)
    root = str(tmp_path / "tg"); os.makedirs(os.path.join(root, "registry")); os.makedirs(os.path.join(root, "shards"))
    T, rows, imgs, labs, imaps, tids = 128, [], [], [], [], []
    full = rng.integers(0, 256, (4 * T, 4 * T), dtype=np.uint8)            # one canvas; 4 x 4 tiles kept
    fvalid = rng.random((4 * T, 4 * T)) > 0.05
    for a in range(4):
        for b in range(4):
            im = full[a * T:(a + 1) * T, b * T:(b + 1) * T]
            v = fvalid[a * T:(a + 1) * T, b * T:(b + 1) * T]
            imap = np.where(v, im, 0).astype(np.uint8)                      # invalid -> inkmap 0 (nan_to_num)
            tid = f"t{a}{b}"
            imgs.append(rng.integers(0, 255, (21, T, T), dtype=np.uint8)); labs.append(_rule_labels(imap, v))
            imaps.append(imap); tids.append(tid)
            rows.append(dict(tile_id=tid, segment="S", canvas9_y0=a * T, canvas9_x0=b * T, size=T,
                             xyz_centre=[0, 0, 0], xyz_corners=[[0, 0, 0]] * 4, shard="s0.npz",
                             shard_index=len(tids) - 1))
    sp = os.path.join(root, "shards", "s0.npz")
    np.savez(sp, images=np.stack(imgs), label=np.stack(labs), inkmap=np.stack(imaps), human=np.stack(labs),
             tile_id=np.array(tids))
    for r in rows:
        r["shard_sha256"] = d2_data.sha256_file(sp)
    with open(os.path.join(root, "registry", "S.jsonl"), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    src = distft.load_soft_source(dict(name="g", kind="tilegrid3", path=root))
    assert len(src) == 1 and src.ink.shape == (1, 3 * T, 3 * T)            # one complete grid-aligned 3 x 3 block
    exp = np.where(fvalid, full, 0)[:3 * T, :3 * T]
    band = (exp > 100) & (exp < 150)
    assert np.array_equal(src.ink[0], exp)
    assert np.array_equal(src.sup[0].astype(bool), fvalid[:3 * T, :3 * T] | band)   # A7 rule, documented
    src1 = distft.load_soft_source(dict(name="g", kind="tilegrid", path=root))
    assert len(src1) == 16 and np.array_equal(src1.ink[5], imaps[5])
