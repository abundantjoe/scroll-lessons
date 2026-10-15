# Provenance: Project HERCULES | owner the owner | [id removed]
"""Unit tests for tools/sib/devloop-r1 (LC384) on SYNTHETIC data only (random volumes, fake pair shards).
Needs the official base checkpoint and the hv-ink environment; skipped otherwise.
Run: PYTHONPATH=/work/amx/pylib /opt/hv-ink/bin/python -m pytest -q tests/sib_devloop_r1_test_lc.py"""
import json
import os
import sys

import numpy as np
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("vesuvius")
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "sib", "devloop-r1")
sys.path.insert(0, D)
import lc_model as LM  # noqa: E402

if not os.path.exists(LM.BASE_CK):
    pytest.skip("base checkpoint not present", allow_module_level=True)
torch.set_num_threads(4)


@pytest.fixture(scope="module")
def base():
    m, _, ink = LM.load_base()
    return m, ink


@pytest.fixture(scope="module")
def pool(tmp_path_factory):
    """Fake pairs0139 output: segment A has a 3 x 4 grid of kept tiles (stride 128) plus one isolated tile,
    segment B one tile at the same canvas position as A's first tile (must not become its neighbour)."""
    root = tmp_path_factory.mktemp("pool")
    (root / "shards").mkdir(); (root / "registry").mkdir()
    rng = np.random.default_rng(1)
    pos = [("A", 128 * r, 128 * c) for r in range(3) for c in range(4)] + [("A", 2048, 2048), ("B", 0, 0)]
    imgs = rng.integers(40, 200, (len(pos), 21, 128, 128), dtype=np.uint8)
    lab = rng.choice(np.array([0, 1, 255], np.uint8), (len(pos), 128, 128), p=[0.6, 0.3, 0.1])
    np.savez_compressed(root / "shards" / "X_s00.npz", images=imgs, label=lab, inkmap=lab, human=lab)
    rows = [dict(tile_id=f"t{i}", segment=s, canvas9_y0=y, canvas9_x0=x, shard="X_s00.npz", shard_index=i) for i, (s, y, x) in enumerate(pos)]
    rows.append(dict(tile_id="notkept", segment="A", canvas9_y0=384, canvas9_x0=0, shard=None))
    with open(root / "registry" / "X.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    allow = [r["tile_id"] for r in rows]
    json.dump(allow, open(root / "allow.json", "w"))
    import lc_cache
    for order in ("forward", "reverse"):
        lc_cache.main(["--shards", str(root / "shards"), "--registry", str(root / "registry"), "--allow", str(root / "allow.json"),
                       "--out", str(root / f"cache_{order}"), "--order", order, "--dtype", "fp32"])
    return root, imgs, lab, pos


def test_mosaic_places_tiles_row_major():
    t = torch.arange(9).float().view(1, 9, 1, 1, 1).expand(1, 9, 1, 2, 2)
    m = LM.mosaic(t.contiguous())
    assert m.shape == (1, 1, 6, 6)
    assert m[0, 0, ::2, ::2].flatten().tolist() == list(range(9))


def test_missing_token_fill():
    n = torch.ones(2, 9, 3, 2, 2)
    pres = torch.ones(2, 9, dtype=torch.bool); pres[1, 0] = False
    out = LM.LetterContext.fill(n, pres, torch.tensor([5.0, 6.0, 7.0]))
    assert torch.all(out[0] == 1) and torch.all(out[1, 1:] == 1)
    assert out[1, 0, :, 0, 0].tolist() == [5.0, 6.0, 7.0]


@pytest.mark.parametrize("variant", ["basedec", "light"])
def test_identity_at_init(base, variant):
    m, _ = base
    lc = LM.LC384(m, variant).eval()
    x = torch.randn(3, 1, 17, 128, 128)
    with torch.no_grad():
        ref = m(x)["ink"]
        sk = lc.encode(x)
        n4 = torch.randn(3, 9, 320, 8, 8); n5 = torch.randn(3, 9, 320, 4, 4)
        pres = torch.rand(3, 9) > 0.3
        out = lc(sk, n4, n5, pres)
    assert float((out - ref).abs().max()) == 0.0


def test_frozen_parts_have_no_grad_and_trainable_state(base):
    m, _ = base
    for variant, prefixes in (("basedec", ("context.", "decoder.", "head.")), ("light", ("context.", "light."))):
        lc = LM.LC384(m, variant)
        tr = {n for n, p in lc.named_parameters() if p.requires_grad}
        assert tr and all(n.startswith(prefixes) for n in tr)
        assert set(lc.trainable_state()) >= tr


def test_cache_neighbours_and_labels(pool):
    root, imgs, lab, pos = pool
    rows = json.load(open(root / "cache_forward" / "tiles.json"))
    assert len(rows) == len(pos)  # the not-kept row is never cached
    key = {(r["segment"], r["y0"], r["x0"]): i for i, r in enumerate(rows)}
    i = key[("A", 128, 128)]  # interior of the 3 x 4 grid: all 9 present
    assert all(v >= 0 for v in rows[i]["nbr"])
    j = key[("A", 0, 0)]      # corner: 4 present (itself, right, below, below-right)
    assert sum(v >= 0 for v in rows[j]["nbr"]) == 4
    assert rows[key[("B", 0, 0)]]["nbr"].count(-1) == 8  # segment B never borrows segment A's tiles
    assert rows[key[("A", 2048, 2048)]]["nbr"].count(-1) == 8
    labs = np.load(root / "cache_forward" / "labels.npy")
    for r_i, r in enumerate(rows):
        t = int(r["tile_id"][1:])
        assert np.array_equal(labs[r_i], lab[t])


@pytest.mark.parametrize("order", ["forward", "reverse"])
def test_cache_features_equal_direct_encode(pool, base, order):
    root, imgs, lab, pos = pool
    import lc_cache
    m, _ = base
    lc = LM.LC384(m).eval()
    C = lc_cache.Cache(str(root / f"cache_{order}"))
    ids = [0, 5]
    t = [int(C.rows[i]["tile_id"][1:]) for i in ids]
    x = torch.stack([torch.from_numpy(lc_cache.normalise(lc_cache.window(imgs[k], order))).unsqueeze(0) for k in t])
    with torch.no_grad():
        sk = lc.encode(x)
    cen, n4, n5, pres = C.batch(ids)
    for l in range(6):
        assert float((cen[l] - sk[l]).abs().max()) == 0.0
    # the window is stack index 2..18 (render slices 7..23); reverse is its exact depth reversal
    w = lc_cache.window(imgs[t[0]], order)
    assert np.array_equal(w, imgs[t[0]][2:19] if order == "forward" else imgs[t[0]][2:19][::-1])


def test_derangement_and_split():
    import lc_train
    p = lc_train.derangement(500)
    assert not np.any(p == np.arange(500)) and sorted(p.tolist()) == list(range(500))
    assert np.array_equal(p, lc_train.derangement(500))
    tr, va = lc_train.split(200)
    assert len(va) == 10 and not set(tr) & set(va) and len(tr) + len(va) == 200


def test_train_smoke_and_ckpt_roundtrip(pool, tmp_path):
    root, *_ = pool
    import lc_train
    out = tmp_path / "run"
    lc_train.main(["--cache", str(root / "cache_forward"), "--arm", "RECIPE", "--out", str(out), "--steps", "6",
                   "--log-every", "2", "--val-every", "2", "--ckpt-every", "3"])
    s = json.load(open(out / "summary.json"))
    assert s["steps"] == 6 and np.isfinite(s["loss_mean_last200"])
    assert s["final_bytes"] < 90e6
    m, ck, _, _ = LM.load_ckpt(str(out / "lc_final.pt"))
    assert ck["variant"] == "basedec" and ck["meta"]["arm"] == "RECIPE"
    with pytest.raises(AssertionError):  # REV must use a reverse-order cache
        lc_train.main(["--cache", str(root / "cache_forward"), "--arm", "REV", "--out", str(tmp_path / "rev"), "--steps", "1"])
    lc_train.main(["--cache", str(root / "cache_forward"), "--arm", "NULL", "--out", str(tmp_path / "null"), "--steps", "2"])
    assert json.load(open(tmp_path / "null" / "summary.json"))["null_fixed_points"] == 0


def test_train_resume_is_bitwise(pool, tmp_path):
    root, *_ = pool
    import lc_train
    base_args = ["--cache", str(root / "cache_forward"), "--arm", "RECIPE", "--steps", "6", "--ckpt-every", "3", "--log-every", "1"]
    lc_train.main(base_args + ["--out", str(tmp_path / "straight")])
    assert lc_train.main(base_args + ["--out", str(tmp_path / "cut"), "--die-after", "3"]) == 99
    assert (tmp_path / "cut" / "resume.pt").exists() and not (tmp_path / "cut" / "lc_final.pt").exists()
    lc_train.main(base_args + ["--out", str(tmp_path / "cut")])
    assert not (tmp_path / "cut" / "resume.pt").exists()
    assert '"event": "resume"' in (tmp_path / "cut" / "train_log.jsonl").read_text()
    a = torch.load(tmp_path / "straight" / "lc_final.pt", weights_only=False)["lc_state"]
    b = torch.load(tmp_path / "cut" / "lc_final.pt", weights_only=False)["lc_state"]
    assert a.keys() == b.keys() and all(torch.equal(a[k], b[k]) for k in a)
