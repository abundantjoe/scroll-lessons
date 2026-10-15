# Provenance: Project HERCULES | owner the owner | [id removed]
"""Fast unit tests of the D2 trainer data interface, rotation, shard store and config rules (synthetic only).
Run: /opt/hv-ink/bin/python -m pytest -q tests/sib_trainer_units_test.py"""
import hashlib
import json
import os
import subprocess
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "sib", "trainer"))
import ckpt_shards  # noqa: E402
import d2_data  # noqa: E402

torch = pytest.importorskip("torch")


def test_label_rule_thresholds():
    t = np.array([[0, 100, 101, 149], [150, 151, 255, 120]], np.uint8)
    v = np.array([[1, 1, 1, 1], [1, 0, 1, 1]], np.uint8)
    ink, sup = d2_data.labels_from_target(t, v)
    assert sup.tolist() == [[1, 1, 0, 0], [1, 0, 1, 0]]
    assert ink.tolist() == [[0, 0, 0, 0], [1, 0, 1, 0]]
    with pytest.raises(ValueError):
        d2_data.labels_from_target(t.astype(np.float32))


def test_synthetic_registry_roundtrip_and_tamper(tmp_path):
    p = d2_data.write_synthetic_registry(str(tmp_path / "r"), n=5, size=128, seed=3, shard_n=2)
    s = d2_data.load_pairs_registry(p)
    assert len(s) == 5 and s.images.shape == (5, 21, 128, 128) and s.mesh_xyz.shape[0] == 5
    assert set(np.unique(s.ink)) <= {0, 1} and not np.any(s.ink & (1 - s.sup))
    reg = json.load(open(p))
    with open(tmp_path / "r" / reg["shards"][0]["file"], "ab") as fh:
        fh.write(b"x")
    with pytest.raises(ValueError, match="sha256"):
        d2_data.load_pairs_registry(p)


def test_patch_registry_and_clearance(tmp_path):
    import contam_check
    p = d2_data.write_synthetic_registry(str(tmp_path / "r"), n=3, size=128, seed=3, mesh_stride=16)
    s = d2_data.load_pairs_registry(p)
    summ = d2_data.write_patch_registry(str(tmp_path / "pr.npz"), [s], {s.name: np.array([2, 0, 1])})
    assert summ["fl09_ready"] and summ["sources"][0]["n_drawn"] == 2 and "CORR-RETRACE" in summ["fl09_method"]
    surf = contam_check.registry_surfaces(str(tmp_path / "pr.npz"))
    assert set(surf) == {"SYN0", "SYN1", "SYN2"}
    # synthetic sheets are planes z = 500 + 1000 k: a point 130 vox above sheet 0's interior clears; 50 does not
    top = np.array([[1100.0, 1100.0, 630.0]])
    r = contam_check.clearance(str(tmp_path / "pr.npz"), top)
    assert abs(r["min_distance_vox"] - 130.0) < 1e-6 and r["pass_"]
    assert not contam_check.clearance(str(tmp_path / "pr.npz"), top - [0, 0, 80.0])["pass_"]


def test_point_triangle_distance_exact():
    import contam_check
    rng = np.random.default_rng(0)
    tri = np.array([[0.0, 0, 0], [10, 0, 0], [0, 10, 0]])
    cases = {(2, 2, 3): 3.0, (-3, -4, 0): 5.0, (20, 0, 0): 10.0, (5, 5, 0): 0.0, (6, 6, 0): np.sqrt(2)}
    for pnt, want in cases.items():
        got = contam_check.point_triangle_distance(np.array([pnt], float), tri[None])[0]
        assert abs(got - want) < 1e-9, (pnt, got, want)
    # brute force against dense sampling of the triangle
    tris = rng.normal(size=(50, 3, 3)) * 5
    p = rng.normal(size=(50, 3)) * 8
    uv = np.array([(u / 60, v / 60) for u in range(61) for v in range(61 - u)])
    for k in range(50):
        samp = tris[k, 0] + uv[:, :1] * (tris[k, 1] - tris[k, 0]) + uv[:, 1:] * (tris[k, 2] - tris[k, 0])
        bf = np.linalg.norm(samp - p[k], axis=1).min()
        ex = contam_check.point_triangle_distance(p[k:k + 1], tris[k:k + 1])[0]
        assert ex <= bf + 1e-9 and bf - ex < 0.5


def test_same_papyrus_fail_closed_half_cell_retrace():
    """Exact re-trace offset by half a dense cell: the vertex form alone may miss it, the surface form catches it;
    a neighbouring sheet 5 vox away is NOT same."""
    import contam_check
    ys, xs = np.meshgrid(np.arange(0, 201, 20.0), np.arange(0, 201, 20.0), indexing="ij")
    train = np.stack([xs, ys, np.zeros_like(xs)], -1)                 # 20-vox official grid step
    tris = contam_check.grid_triangles(train)
    wy, wx = np.meshgrid(np.arange(2, 198, 2.0), np.arange(2, 198, 2.0), indexing="ij")
    win = np.stack([wx + 2.0, wy + 2.0, np.full_like(wx, 1.5)], -1).reshape(-1, 3)   # half a 4-vox cell + 1.5 vox
    r = contam_check.same_papyrus(tris, win)
    assert r["same_surface"] and r["same"]
    far = win + [0, 0, 5.0]
    assert not contam_check.same_papyrus(tris, far)["same"]


def test_tilegrid_quads_triangulate(tmp_path):
    import contam_check
    _tilegrid_fixture(tmp_path)
    s3 = d2_data.load_source(dict(kind="tilegrid3", path=str(tmp_path), name="p0139"))
    assert s3.mesh_xyz.shape == (1, 9, 2, 2, 3)
    d2_data.write_patch_registry(str(tmp_path / "pr.npz"), [s3], {})
    surf = contam_check.registry_surfaces(str(tmp_path / "pr.npz"))
    assert surf["seg1"].shape == (18, 3, 3)
    assert abs(contam_check.clearance(str(tmp_path / "pr.npz"), np.array([[100.0, 100.0, 150.0]]))["min_distance_vox"]
               - 140.0) < 1e-9


def _tensor_state():
    g = torch.Generator().manual_seed(7)
    return {"w": torch.randn(300, 1000, generator=g), "o": {"exp_avg": torch.randn(50, 50, generator=g)},
            "rng": torch.get_rng_state(), "step": 12}


def test_shards_save_delete_restore_bitwise(tmp_path):
    """Save -> push to a (local bare) remote -> delete everything local -> fetch -> compare tensors bitwise."""
    remote = str(tmp_path / "remote.git")
    subprocess.run(["git", "init", "-q", "--bare", remote], check=True)
    st = _tensor_state()
    bare = str(tmp_path / "local.bare")
    r = ckpt_shards.save_and_push(bare, st, step=12, config_sha256="c" * 64, remote_url=remote,
                                  ref="refs/heads/x-ckpt", max_shard=400_000)
    assert r["pushed"] and r["n_shards"] >= 3 and r["max_shard_bytes"] <= 400_000
    # second save replaces the first: the ref holds a single parentless commit
    st["step"] = 13
    r2 = ckpt_shards.save_and_push(bare, st, step=13, config_sha256="c" * 64, remote_url=remote,
                                   ref="refs/heads/x-ckpt", max_shard=400_000)
    out = subprocess.run(["git", "--git-dir", remote, "rev-list", "--count", "refs/heads/x-ckpt"],
                         capture_output=True, text=True, check=True).stdout.strip()
    assert out == "1" and r2["commit"] != r["commit"]
    import shutil
    shutil.rmtree(bare)
    blob, man = ckpt_shards.fetch_latest(str(tmp_path / "fresh.bare"), remote, "refs/heads/x-ckpt")
    back = ckpt_shards.bytes_to_state(blob)
    assert man["step"] == 13 and back["step"] == 13
    assert torch.equal(back["w"], st["w"]) and torch.equal(back["o"]["exp_avg"], st["o"]["exp_avg"])
    assert torch.equal(back["rng"], st["rng"])
    assert back["w"].numpy().tobytes() == st["w"].numpy().tobytes()


def test_shard_cap_and_tamper(tmp_path):
    with pytest.raises(ValueError):
        ckpt_shards.split_bytes(b"x", 96_000_000)
    bare = str(tmp_path / "b.bare")
    commit, man = ckpt_shards.build_commit(bare, b"abc" * 1000, step=1, config_sha256="0" * 64, max_shard=1000)
    blob, _ = ckpt_shards.read_commit(bare, commit)
    assert blob == b"abc" * 1000 and len(man["shards"]) == 3
    assert ckpt_shards.fetch_latest(str(tmp_path / "c.bare"), bare, "refs/heads/none") is None


def test_rotation_exact_multiples_and_margin():
    import d2_train
    tr = d2_train.Trainer.__new__(d2_train.Trainer)
    tr.np, tr.torch, tr.T = np, torch, 128
    rng = np.random.default_rng(0)
    R = d2_train.rot_crop_size(128)
    assert R >= 128 * 2 ** 0.5 and (R - 128) % 2 == 0
    img = rng.integers(0, 255, (17, R, R)).astype(np.uint8)
    ink = rng.integers(0, 2, (R, R)).astype(np.uint8)
    sup = np.ones((R, R), np.uint8)
    seen = set()
    tr.rot_gen = np.random.default_rng(0)
    for _ in range(200):
        im, a, b, k = tr._rotate(img, ink, sup)
        seen.add(k)
        assert im.shape == (17, 128, 128) and a.shape == b.shape == (128, 128)
        assert set(np.unique(a)) <= {0, 1} and set(np.unique(b)) <= {0, 1}
        if k % 6 == 0:
            c0 = (R - 128) // 2
            ref = np.rot90(img, k // 6, axes=(1, 2))[:, c0:c0 + 128, c0:c0 + 128]
            assert np.array_equal(im, ref.astype(np.float32))
        else:
            assert b.all(), "full margin: no pixel may fall outside the stored patch"
    assert seen == set(range(24))
    # constant image stays constant under any rotation; small patch (no margin) -> corners ignored
    tr.rot_gen = np.random.default_rng(1)
    while True:
        im, a, b, k = tr._rotate(np.full((17, 128, 128), 77, np.uint8), ink[:128, :128], sup[:128, :128])
        if k % 6:
            break
    assert np.allclose(im, 77.0, atol=1e-3) and 0 < b.mean() < 1 and b[0, 0] == 0 and b[64, 64] == 1


def test_config_rules(tmp_path):
    import d2_train
    base = ["make-config", "--seed", "1", "--source", f"s=pairs:{tmp_path}/r.json", "--out", str(tmp_path / "c.json")]
    assert d2_train.main(base + ["--arm", "NULL"]) == 0
    c = json.load(open(tmp_path / "c.json"))
    assert (c["tile"], c["rot24"], c["null"], c["rev"], c["batch"], c["steps"]) == (384, True, True, False, 32, 12000)
    assert c["base_checkpoint"]["sha256"].startswith("e635558a")
    for arm, t in (("P128", 128), ("P384", 384), ("REV", 384)):
        d2_train.main(base + ["--arm", arm])
        assert json.load(open(tmp_path / "c.json"))["tile"] == t
    with pytest.raises(ValueError):
        d2_train.main(base + ["--arm", "P128", "--z-centre-offset", "1"])      # 1 + jitter 2 > 2
    d2_train.main(base + ["--arm", "P128", "--z-centre-offset", "1", "--z-jitter", "1"])
    with pytest.raises(ValueError):
        d2_train.main(base + ["--arm", "P128", "--micro-batch", "5"])
    d2_train.main(base + ["--arm", "CUSTOM", "--tile", "512"])
    c = json.load(open(tmp_path / "c.json"))
    assert (c["tile"], c["rot24"], c["null"], c["rev"]) == (512, False, False, False)
    d2_train.main(base + ["--arm", "CUSTOM", "--tile", "128", "--rot24"])
    assert json.load(open(tmp_path / "c.json"))["rot24"] is True
    c = json.load(open(tmp_path / "c.json"))
    assert d2_train.config_sha256(c) == hashlib.sha256(d2_train.canonical_json(c)).hexdigest()


def test_stagec_adapter(tmp_path):
    """Synthetic fixture in the pairs-session stage-C layout: loads, recomputes labels, refuses tampering."""
    rng = np.random.default_rng(5)
    os.makedirs(tmp_path / "shards")
    ref9 = rng.integers(0, 256, (3, 384, 384)).astype(np.uint8)
    valid = rng.random((3, 384, 384)) > 0.1
    ink, sup = d2_data.labels_from_target(ref9, valid.astype(np.uint8))
    labels = np.where(sup == 1, ink, 255).astype(np.uint8)
    f = tmp_path / "shards" / "p_000.npz"
    np.savez_compressed(f, images=rng.integers(0, 256, (3, 21, 384, 384)).astype(np.uint8), ref9=ref9,
                        labels=labels, valid=valid, xyz=rng.random((3, 17, 17, 3)).astype(np.float32),
                        patch_id=np.array(["a", "b", "c"]), segment=np.array(["s1", "s1", "s2"]))
    man = dict(shards=[dict(shard="shards/p_000.npz", n=3, bytes=os.path.getsize(f),
                            sha256=d2_data.sha256_file(str(f)), patch_ids=["a", "b", "c"])])
    json.dump(man, open(tmp_path / "shards.json", "w"))
    s = d2_data.load_source(dict(kind="stagec", path=str(tmp_path), name="p0814"))
    assert len(s) == 3 and s.size == 384 and np.array_equal(s.ink, ink) and s.mesh_xyz.shape == (3, 17, 17, 3)
    json.dump(["a", "c"], open(tmp_path / "allow.json", "w"))
    s2 = d2_data.load_source(dict(kind="stagec", path=str(tmp_path), name="p0814", allow_ids=str(tmp_path / "allow.json")))
    assert s2.patch_id == ["a", "c"] and s2.meta["allow_ids_sha256"]
    bad = labels.copy(); bad[0, 0, 0] = 1 - bad[0, 0, 0] if bad[0, 0, 0] < 2 else 0
    np.savez_compressed(f, images=np.zeros((3, 21, 384, 384), np.uint8), ref9=ref9, labels=bad, valid=valid,
                        xyz=np.zeros((3, 17, 17, 3), np.float32), patch_id=np.array(["a", "b", "c"]),
                        segment=np.array(["s1", "s1", "s2"]))
    man["shards"][0]["sha256"] = d2_data.sha256_file(str(f))
    json.dump(man, open(tmp_path / "shards.json", "w"))
    with pytest.raises(ValueError, match="differ"):
        d2_data.load_source(dict(kind="stagec", path=str(tmp_path), name="p0814"))


def test_subtile_crop_padding():
    import d2_train
    tr = d2_train.Trainer.__new__(d2_train.Trainer)
    tr.np, tr.R = np, 6
    src = d2_data.Source(name="s", role="train", images=np.zeros((1, 21, 8, 8), np.uint8),
                         ink=np.ones((1, 8, 8), np.uint8), sup=np.ones((1, 8, 8), np.uint8), registry_sha256="x")
    w = np.arange(17 * 64, dtype=np.uint8).reshape(17, 8, 8)
    im, ink, sup = tr._crop(src, 0, w, 1, 1)                       # inside: plain slice
    assert np.array_equal(im, w[:, 1:7, 1:7]) and sup.all()
    im, ink, sup = tr._crop(src, 0, w, -2, 4)                      # top/right outside -> padded, ignored
    assert im.shape == (17, 6, 6) and sup[:2].sum() == 0 and sup[:, 4:].sum() == 0 and sup[2:, :4].all()
    assert np.array_equal(im[:, 0, :4], w[:, 0, 4:8]) and np.array_equal(im[:, 2:, :4], w[:, 0:4, 4:8])
    assert ink[:2].sum() == 0


def _tilegrid_fixture(root, bad=False):
    rng = np.random.default_rng(9)
    os.makedirs(root / "shards"); os.makedirs(root / "registry")
    pos = [(y, x) for y in (0, 128, 256) for x in (0, 128, 256)] + [(384, 0)]      # one complete 3x3 block + 1 extra
    n = len(pos)
    imgs = rng.integers(0, 256, (n, 21, 128, 128)).astype(np.uint8)
    imap = rng.integers(0, 256, (n, 128, 128)).astype(np.uint8)
    lab = np.where(imap >= 150, 1, np.where(imap <= 100, 0, 255)).astype(np.uint8)
    lab[:, :4] = 255                                                                 # invalid rows
    if bad:
        lab[0][imap[0] > 200] = 0
    ids = np.array([f"seg1_{y}_{x}" for y, x in pos])
    np.savez_compressed(root / "shards" / "seg1_s00.npz", images=imgs, label=lab, inkmap=imap,
                        human=np.full_like(lab, 255), tile_id=ids)
    h = d2_data.sha256_file(str(root / "shards" / "seg1_s00.npz"))
    with open(root / "registry" / "seg1.jsonl", "w") as f:
        for i, (y, x) in enumerate(pos):
            f.write(json.dumps(dict(tile_id=str(ids[i]), segment="seg1", canvas9_y0=y, canvas9_x0=x, size=128,
                                    xyz_centre=[x + 64.0, y + 64.0, 10.0],
                                    xyz_corners=[[x, y, 10.0], [x + 128.0, y, 10.0], [x, y + 128.0, 10.0],
                                                 [x + 128.0, y + 128.0, 10.0]],
                                    shard="seg1_s00.npz", shard_index=i, shard_sha256=h)) + "\n")
        f.write(json.dumps(dict(tile_id="seg1_rejected", segment="seg1", canvas9_y0=512, canvas9_x0=0, size=128)) + "\n")
    return imgs, lab


def test_tilegrid_adapter_and_mosaic(tmp_path):
    imgs, lab = _tilegrid_fixture(tmp_path)
    s1 = d2_data.load_source(dict(kind="tilegrid", path=str(tmp_path), name="p0139"))
    assert len(s1) == 10 and s1.size == 128 and np.array_equal(s1.sup[0], (lab[0] != 255).astype(np.uint8))
    s3 = d2_data.load_source(dict(kind="tilegrid3", path=str(tmp_path), name="p0139"))
    assert len(s3) == 1 and s3.size == 384 and s3.canvas_yx.tolist() == [[0, 0]]
    assert np.array_equal(s3.images[0][:, 128:256, 256:384], imgs[5])              # tile (128, 256)
    assert np.array_equal(s3.ink[0][256:, :128], (lab[6] == 1).astype(np.uint8))    # tile (256, 0)
    assert s3.mesh_xyz.shape == (1, 9, 2, 2, 3)


def test_tilegrid_label_rule_mismatch_refused(tmp_path):
    _tilegrid_fixture(tmp_path, bad=True)
    with pytest.raises(ValueError, match="disagree"):
        d2_data.load_source(dict(kind="tilegrid", path=str(tmp_path), name="p0139"))


def test_network_remote_weights_refused(tmp_path):
    """DECL-OFFLOAD-1 ruling: the trainer never pushes weights/optimiser state to a network git remote."""
    import d2_train
    cfgp = str(tmp_path / "c.json")
    d2_train.main(["make-config", "--arm", "P128", "--seed", "1", "--source", f"s=pairs:{tmp_path}/r.json",
                   "--remote-ref", "refs/heads/x-ckpt", "--out", cfgp])
    cfg = json.load(open(cfgp))
    for url in ("https://github.com/abc/def", "git@github.com:abc/def.git", None, str(tmp_path / "missing")):
        with pytest.raises(SystemExit, match="refused"):
            d2_train.run_train(cfg, str(tmp_path / "o"), remote_url=url)


def _blockpairs_fixture(root):
    rng = np.random.default_rng(4)
    os.makedirs(root / "registry"); os.makedirs(root / "blockpairs" / "segA")
    ref9 = rng.integers(0, 256, (2, 384, 384)).astype(np.uint8)
    valid = rng.random((2, 384, 384)) > 0.05
    ink, sup = d2_data.labels_from_target(ref9, valid.astype(np.uint8))
    f = root / "blockpairs" / "segA" / "0_0.npz"
    np.savez_compressed(f, images=rng.integers(0, 256, (2, 21, 384, 384)).astype(np.uint8), ref9=ref9,
                        labels=np.where(sup == 1, ink, 255).astype(np.uint8), valid=valid,
                        xyz=rng.random((2, 17, 17, 3)).astype(np.float32), patch_id=np.array(["A_0_0", "A_0_384"]))
    h = d2_data.sha256_file(str(f))
    with open(root / "registry" / "segA.jsonl", "w") as fh:
        for i, pid in enumerate(["A_0_0", "A_0_384"]):
            fh.write(json.dumps(dict(patch_id=pid, segment="segA", y0=0, x0=384 * i, size=384, status="GATED",
                                     passed=True, staged="blockpairs/segA/0_0.npz", staged_sha256=h,
                                     n_ink=int(ink[i].sum()), n_blank=int((sup[i] & (1 - ink[i])).sum()),
                                     n_ignore=int((1 - sup[i]).sum()))) + "\n")
        fh.write(json.dumps(dict(patch_id="A_384_0", segment="segA", y0=384, x0=0, size=384, status="GATED",
                                 passed=False)) + "\n")
    return ink


def test_blockpairs_adapter(tmp_path):
    ink = _blockpairs_fixture(tmp_path)
    s = d2_data.load_source(dict(kind="blockpairs", path=str(tmp_path), name="p0814"))
    assert len(s) == 2 and s.patch_id == ["A_0_0", "A_0_384"] and np.array_equal(s.ink, ink)
    assert s.canvas_yx.tolist() == [[0, 0], [0, 384]] and s.mesh_xyz.shape == (2, 17, 17, 3)


def test_pair_freeze_record(tmp_path):
    import pair_freeze
    _tilegrid_fixture(tmp_path / "t")
    _blockpairs_fixture(tmp_path / "b")
    json.dump(["seg1_128_128"], open(tmp_path / "hold.json", "w"))      # breaks the only 3x3 block
    json.dump(["A_0_384"], open(tmp_path / "hold2.json", "w"))
    req = dict(d2_date=None, decl="DECL-D2-A1",
               sources=[dict(name="p0139", kind="tilegrid3", branch="b1", commit="c1", path=str(tmp_path / "t")),
                        dict(name="p0814", kind="blockpairs", branch="b2", commit="c2", path=str(tmp_path / "b"))],
               holdouts=[dict(reason="test", file=str(tmp_path / "hold2.json"))])
    json.dump(req, open(tmp_path / "req.json", "w"))
    assert pair_freeze.main(["--request", str(tmp_path / "req.json"), "--out", str(tmp_path / "f"), "--verify"]) == 0
    r = json.load(open(tmp_path / "f" / "pair_freeze.json"))
    c0, c1 = r["sources"][0]["counts"], r["sources"][1]["counts"]
    assert (c0["kept"], c0["in_block"], c0["out_of_block"], c0["blocks"]) == (10, 9, 1, 1)
    assert (c1["passed"], c1["held_out"], c1["after_holdouts"]) == (2, 1, 1)
    assert r["sources"][1]["verified_load"]["n_patches"] == 1 and r["sources"][0]["verified_load"]["n_patches"] == 1
    req["holdouts"].append(dict(reason="test2", file=str(tmp_path / "hold.json")))
    json.dump(req, open(tmp_path / "req.json", "w"))
    pair_freeze.main(["--request", str(tmp_path / "req.json"), "--out", str(tmp_path / "g")])
    r2 = json.load(open(tmp_path / "g" / "pair_freeze.json"))
    assert r2["sources"][0]["counts"]["in_block"] == 0 and r2["record_sha256"] != r["record_sha256"]


def test_stagec_blockfile_layout_with_data_root(tmp_path):
    """pairs0814 ede21e3 stage C: shards.json lists staged block files by repo-relative path (two branches), the npz
    has no segment key, segment/canvas come from pair_registry.json; only listed patch ids are used."""
    import pair_freeze
    rng = np.random.default_rng(6)
    tree = tmp_path / "tree"
    for rel in ("logs/sib/pairs0814/blockpairs/s1", "data/sib/pairs0814b/blockpairs/s2"):
        os.makedirs(tree / rel)
    entries, preg = [], []
    for rel, sid, br in (("logs/sib/pairs0814/blockpairs/s1/0_0.npz", "s1", "b1"),
                         ("data/sib/pairs0814b/blockpairs/s2/0_0.npz", "s2", "b2@c")):
        ref9 = rng.integers(0, 256, (2, 384, 384)).astype(np.uint8)
        valid = np.ones((2, 384, 384), bool)
        ink, sup = d2_data.labels_from_target(ref9, valid.astype(np.uint8))
        ids = [f"{sid}_0_0", f"{sid}_0_384"]
        np.savez_compressed(tree / rel, images=rng.integers(0, 256, (2, 21, 384, 384)).astype(np.uint8), ref9=ref9,
                            labels=np.where(sup == 1, ink, 255).astype(np.uint8), valid=valid,
                            xyz=rng.random((2, 17, 17, 3)).astype(np.float32), patch_id=np.array(ids))
        entries.append(dict(shard=rel, branch=br, n=1, bytes=os.path.getsize(tree / rel),
                            sha256=d2_data.sha256_file(str(tree / rel)), patch_ids=[ids[0]]))   # only the first listed
        preg.append(dict(patch_id=ids[0], segment=f"SEG-{sid}", y0=0, x0=0, size=384))
    root = tree / "logs/sib/pairs0814"
    json.dump(dict(shards=entries), open(root / "shards.json", "w"))
    json.dump(dict(patches=preg), open(root / "pair_registry.json", "w"))
    s = d2_data.load_source(dict(kind="stagec", path=str(root), name="p0814", data_root=str(tree)))
    assert s.patch_id == ["s1_0_0", "s2_0_0"] and s.segment == ["SEG-s1", "SEG-s2"] and s.size == 384
    req = dict(d2_date="2026-10-20", decl="T", holdouts=[],
               sources=[dict(name="p0814u", kind="stagec", path=str(root), data_root=str(tree))])
    json.dump(req, open(tmp_path / "req.json", "w"))
    pair_freeze.main(["--request", str(tmp_path / "req.json"), "--out", str(tmp_path / "f"), "--verify"])
    r = json.load(open(tmp_path / "f" / "pair_freeze.json"))["sources"][0]
    assert r["counts"]["passed"] == 2 and r["verified_load"]["n_patches"] == 2
    assert "pair_registry.json" in r["registry_files_sha256"]


def test_holdouts_from_registry(tmp_path):
    import holdouts_from_registry as h
    rows = [dict(patch_id="a", segment="20260226000000-x", base_same_papyrus_46527=False, base_min_dist_vox=">=256",
                 duplicate_group=0),
            dict(patch_id="b", segment="s1", base_same_papyrus_46527=True, base_min_dist_vox=0.5, duplicate_group=1),
            dict(patch_id="c", segment="s1", base_same_papyrus_46527=False, base_min_dist_vox=100.0, duplicate_group=1),
            dict(patch_id="d", segment="s2", base_same_papyrus_46527=False, base_min_dist_vox=">=256", duplicate_group=2)]
    assert h.apply("base_same", rows) == ["a", "b"]
    assert h.apply("base_within:128", rows) == ["a", "b", "c"]
    assert h.apply("dedupe_groups", rows) == ["c"]
