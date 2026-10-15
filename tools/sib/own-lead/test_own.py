# Provenance: Project HERCULES | owner the owner | [id removed]
"""Unit tests of the P4-OWN tools on synthetic data only (no network, no real CT or labels).
Run: OWN_WORK=<tmp> python test_own.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import own_common as C  # noqa: E402
import auc as A  # noqa: E402
import build_patches as BP  # noqa: E402
import train as TR  # noqa: E402

PY = sys.executable
TMP = tempfile.mkdtemp(prefix='own_test_')
SMALL = dict(w=(4, 8, 8), head=8, dil=(1, 2), res3=(False, False, True, True))


def test_auc():
    rng = np.random.default_rng(1)
    for _ in range(20):
        n = int(rng.integers(50, 400))
        s = rng.integers(0, 12, n).astype(np.uint8)          # many ties
        y = rng.random(n) < 0.3
        m = rng.random(n) < 0.8
        sp, sn = s[m & y].astype(float), s[m & ~y].astype(float)
        brute = ((sp[:, None] > sn[None]).sum() + 0.5 * (sp[:, None] == sn[None]).sum()) / (len(sp) * len(sn))
        got = A.auc(s, y.astype(np.uint8), m)
        assert abs(got - brute) < 1e-12, (got, brute)
    assert A.auc(np.array([1, 2], np.uint8), np.array([0, 0]), np.array([True, True])) is None
    print('auc ok')


def test_derangement_folds_sched():
    for n in (2, 3, 10, 1000):
        p = TR.derangement(n)
        assert sorted(p) == list(range(n)) and not np.any(p == np.arange(n))
        assert np.array_equal(p, TR.derangement(n))
    tiles = [('20260701183124-w010-027', r, c) for r in range(8) for c in range(9)] + \
            [('20260701183125-w028-037', r, c) for r in range(2) for c in range(3)]
    g = TR.fold_groups(tiles)
    sizes = np.bincount(list(g.values()))
    assert sizes.max() - sizes.min() <= 1 and len(sizes) == 3
    order = sorted(tiles, key=lambda t: (t[0], t[2], t[1]))
    gs = [g[t] for t in order]
    assert gs == sorted(gs), 'groups must be contiguous in (strip, column, row) order'
    pats = [dict(seg=tiles[0][0], tiles=[[0, 0]]), dict(seg=tiles[0][0], tiles=[[0, 0], [0, 8]])]
    # patch 1 straddles c0 (group 0) and c8 (group 2): excluded from every F arm
    for arm in ('F1', 'F2', 'F3'):
        assert 1 not in TR.arm_patches(arm, pats, g)
    assert 0 not in TR.arm_patches('F1', pats, g) and 0 in TR.arm_patches('F2', pats, g)
    i1, a1 = TR.schedule(5, np.arange(10), np.arange(10, 30), 7, 4)
    i2, a2 = TR.schedule(5, np.arange(10), np.arange(10, 30), 7, 4)
    assert np.array_equal(i1, i2) and all(np.array_equal(a1[k], a2[k]) for k in a1)
    assert (i1[:, :2] < 10).all() and (i1[:, 2:] >= 10).all()
    print('derangement/folds/schedule ok')


class FakeReader:
    """Synthetic CT: value = f(seg, y, x, z) deterministic; stands in for C.read_region."""

    def __call__(self, seg, y0, y1, x0, x1):
        yy, xx = np.meshgrid(np.arange(y0, y1), np.arange(x0, x1), indexing='ij')
        base = ((yy * 7 + xx * 13) % 97).astype(np.uint8)
        img = np.repeat(base[..., None], C.NZ, 2) + np.arange(C.NZ, dtype=np.uint8)[None, None]
        return img, dict(chunks_read=1, chunks_missing=0, chunk_records_sha256='x')


def setup_small_world():
    """Shrink the canvas: T_TILE 256, a w010-027 canvas of 9 x 12 tiles; all-valid mesh."""
    C.T_TILE = 256
    C.TILE_PX = {}
    C.SEGS = {'20260701183124-w010-027': (9 * 256, 12 * 256), '20260701183125-w028-037': (2 * 256, 2 * 256)}
    C.read_region = FakeReader()
    C.load_valid = lambda seg: np.ones((C.SEGS[seg][0] // 20 + 1, C.SEGS[seg][1] // 20 + 1), bool)
    C.canvas_mask = lambda seg, valid, y0, y1, x0, x1: np.ones((y1 - y0, x1 - x0), bool)


def make_excl(d, x_label=False):
    os.makedirs(f'{d}/shards', exist_ok=True)
    T = C.T_TILE
    rng = np.random.default_rng(3)
    cells, shards = [], []
    # certify w010-027 c0-c7 r0-r7 (c8 not certified: too close to X) and w028-037 all
    for r in range(8):
        for c in range(8):
            cells.append(dict(seg='20260701183124-w010-027', y0=r * T, x0=c * T, h=T, w=T, min_dist_mm=1.3 + 0.01 * c))
    for r in range(2):
        for c in range(2):
            cells.append(dict(seg='20260701183125-w028-037', y0=r * T, x0=c * T, h=T, w=T, min_dist_mm=5.0))
    regs = [('20260701183124-w010-027', 0, 0, 8 * T, 8 * T), ('20260701183125-w028-037', 0, 0, 2 * T, 2 * T)]
    if x_label:
        regs.append(('20260701183124-w010-027', 0, 9 * T, T, T))
    for i, (seg, y0, x0, h, w) in enumerate(regs):
        ink = (rng.random((h, w)) < 0.05).astype(np.uint8)
        sup = np.ones((h, w), bool)
        sup[:, : w // 10] = False
        f = f'{d}/shards/s{i}.npz'
        np.savez_compressed(f, ink=ink, sup=sup)
        shards.append(dict(file=f'shards/s{i}.npz', seg=seg, y0=y0, x0=x0, h=h, w=w, scale=1,
                           sha256=C.sha256_file(f)))
    json.dump(dict(cells=cells), open(f'{d}/cert.json', 'w'))
    json.dump(dict(shards=shards), open(f'{d}/shards.json', 'w'))


def test_build_patches():
    setup_small_world()
    d = f'{TMP}/excl_bad'
    make_excl(d, x_label=True)
    try:
        BP.load_excl(d)
        raise AssertionError('X-overlapping label shard accepted')
    except SystemExit as e:
        assert 'overlaps X' in str(e)
    d = f'{TMP}/excl'
    make_excl(d)
    ex = BP.load_excl(d)
    valid = {s: C.load_valid(s) for s in C.SEGS}
    keep, nq = BP.select(ex, valid, 128)
    assert nq == len(keep)
    kc, _ = BP.select(ex, valid, 160, 128)          # input 160, core 128, margin 16
    assert all(p['margin'] == 16 and p['y0'] >= 0 for p in kc)
    # no core in tile row 0/col 0 border lost except where the window leaves the canvas; c7 cores whose window
    # reaches c8 (uncertified) must be dropped
    assert not any(p['seg'] == C.X_SEG and any(c == 8 for _, c in p['tiles']) for p in kc)
    kcap, nq2 = BP.select(ex, valid, 128, None, 50)
    assert len(kcap) == 50 and nq2 == nq and kcap == BP.select(ex, valid, 128, None, 50)[0]
    assert keep and all(not C.in_x_zone(p['seg'], r, c) for p in keep for r, c in p['tiles'])
    assert all(p['min_dist_mm'] >= 1.2 for p in keep)
    # c8 of w010-027 not certified -> no patch may touch it
    assert not any(p['seg'] == C.X_SEG and any(c == 8 for _, c in p['tiles']) for p in keep)
    # w010-027: 8 x 8 tiles x 4 patches, minus the 8 x 2 patches at x0 = 0 of the two c0 patch rows per tile row
    # (sup coverage 0 %; x0 = 128 has 41 % and stays). w028-037: all 16.
    assert len(keep) == 8 * 8 * 4 - 8 * 2 + 16, len(keep)
    f = BP.feasibility(ex, valid)
    assert f['n_labelled_cells'] > 0 and 0 < f['n_ink_cells_ge2pct'] <= f['n_labelled_cells']
    out1, out2 = f'{TMP}/p1', f'{TMP}/p2'
    for o in (out1, out2):
        files = BP.write_shards(ex, valid, [dict(p) for p in keep], 128, o, threads=2)
    f1 = json.load(open(f'{out1}/shard_000/done.json'))
    f2 = json.load(open(f'{out2}/shard_000/done.json'))
    assert f1 == f2, 'shards are not byte-deterministic'
    # full manifest as main() writes it (for the train test)
    json.dump(dict(patch=128, n=len(keep), patches=keep), open(f'{out1}/patches.json', 'w'))
    json.dump(dict(n_patches=len(keep), files=files), open(f'{out1}/build_manifest.json', 'w'))
    print('build_patches ok', len(keep), f)
    return out1


def test_excl_format_a():
    """p4-excl t_cert.py format + x4 label tiles (LABEL_INTERFACE.md)."""
    setup_small_world()
    T = C.T_TILE
    d = f'{TMP}/excl_a'
    os.makedirs(f'{d}/labels', exist_ok=True)
    n4 = -(-T // 4)
    masks, tiles, files = {}, {}, []
    rng = np.random.default_rng(5)
    for r in range(8):
        for c in range(9):
            m = np.ones((n4, n4), bool)
            if c == 8:
                m[:, n4 // 2:] = False          # half of c8 too close to X
            masks[f'w010-027_r{r}_c{c}'] = m
            tiles[f'w010-027_r{r}_c{c}'] = dict(strip='w010-027', r=r, c=c, min_dist_to_X_mm=1.0 if c == 8 else 2.0)
            ink = (rng.random((n4, n4)) < 0.05).astype(np.uint8) * 16
            sup = np.full((n4, n4), 16, np.uint8)
            f = f'labels/w010-027_r{r}_c{c}.npz'
            np.savez_compressed(f'{d}/{f}', ink=ink, sup=sup, n_sub=16)
            files.append(dict(file=f, strip='w010-027', r=r, c=c, sha256=C.sha256_file(f'{d}/{f}')))
    np.savez_compressed(f'{d}/T_mask_w010-027.npz', **masks)
    tc = dict(strips={'w010-027': dict(T_px=T, mask_file='T_mask_w010-027.npz',
                                       mask_file_sha256=C.sha256_file(f'{d}/T_mask_w010-027.npz'))}, tiles=tiles)
    json.dump(tc, open(f'{d}/T_cert.json', 'w'))
    json.dump(dict(grid='x4 of tile', files=files), open(f'{d}/labels_w010-027.json', 'w'))
    ex = BP.load_excl(d)
    valid = {s: C.load_valid(s) for s in C.SEGS}
    keep, nq = BP.select(ex, valid, 128)
    x8 = 8 * T
    # c8: only cores whose whole window lies in its certified left half
    assert all(p['x0'] + 128 <= x8 + (n4 // 2) * 4 for p in keep if p['seg'] == C.X_SEG)
    assert any(p['x0'] >= x8 for p in keep)
    assert all(abs(p['ink_frac'] - 0.05) < 0.03 for p in keep)
    f_slow, f_fast = BP.feasibility(ex, valid), BP.feasibility_fast(ex, valid)
    assert (f_slow['n_labelled_cells'], f_slow['n_ink_cells_ge2pct']) == (f_fast['n_labelled_cells'],
                                                                          f_fast['n_ink_cells_ge2pct']), (f_slow, f_fast)
    ink, sup = ex.labels(C.X_SEG, 0, 8, 0, 8)
    assert ink.dtype == np.float32 and sup.all()
    # an X label file is refused
    files.append(dict(file=files[0]['file'], strip='w010-027', r=0, c=9, sha256=files[0]['sha256']))
    json.dump(dict(grid='x4 of tile', files=files), open(f'{d}/labels_w010-027.json', 'w'))
    try:
        BP.load_excl(d)
        raise AssertionError('X label file accepted')
    except SystemExit as e:
        assert 'X tile' in str(e)
    print('excl format a ok', len(keep))


def test_train_resume_infer(data):
    rc = dict(model=SMALL, steps=6, batch=4, lr=1e-3, wd=1e-4, warmup=2, log_every=1)
    rp = f'{TMP}/recipe.json'
    json.dump(rc, open(rp, 'w'))
    env = dict(os.environ, OWN_WORK=f'{TMP}/work')
    base = [PY, f'{HERE}/train.py', '--data', data, '--recipe', rp, '--threads', '2']
    # train.py imports the real own_common: the data dir is synthetic but self-contained, so this works unchanged
    subprocess.run(base + ['--arm', 'S1', '--out', f'{TMP}/a'], check=True, env=env, capture_output=True)
    r = subprocess.run(base + ['--arm', 'S1', '--out', f'{TMP}/b', '--die-after', '3'], env=env, capture_output=True)
    assert r.returncode == 99, r.stderr[-500:]
    subprocess.run(base + ['--arm', 'S1', '--out', f'{TMP}/b'], check=True, env=env, capture_output=True)
    import torch
    wa = torch.load(f'{TMP}/a/model_final.pth', weights_only=False)['model']
    wb = torch.load(f'{TMP}/b/model_final.pth', weights_only=False)['model']
    diff = max(float((wa[k].float() - wb[k].float()).abs().max()) for k in wa)
    assert diff < 1e-5, f'resume not equivalent: {diff}'
    sa = json.load(open(f'{TMP}/a/summary.json'))
    sb = json.load(open(f'{TMP}/b/summary.json'))
    assert sa['train_manifest_sha256'] == sb['train_manifest_sha256']
    for arm in ('NULL', 'F1'):
        subprocess.run(base + ['--arm', arm, '--out', f'{TMP}/{arm}', '--steps', '2'], check=True, env=env,
                       capture_output=True)
    tn = json.load(open(f'{TMP}/NULL/train_manifest.json'))
    assert all(i != j for i, j in zip(tn['train_patch_ids'], tn['label_source']))
    tf = json.load(open(f'{TMP}/F1/train_manifest.json'))
    assert len(tf['train_patch_ids']) < len(tn['train_patch_ids'])
    # ShardCat == np.concatenate item by item (the lazy loader gives identical arrays)
    parts = [np.arange(i * 10, i * 10 + n * 3).reshape(n, 3) for i, n in enumerate((4, 1, 5))]
    cat = TR.ShardCat(parts)
    ref = np.concatenate(parts)
    assert len(cat) == len(ref) and all(np.array_equal(cat[i], ref[i]) for i in range(len(ref)))
    print('train/resume ok; max weight diff after resume', diff)


def test_window_equivalence():
    """Windowed inference with HALO equals whole-region prediction (exact receptive field coverage)."""
    import torch
    import infer as IN
    torch.manual_seed(0)
    cfg = dict(w=(8, 16, 32), head=32, dil=(1, 2, 4, 8), res3=(False, False, True, True))  # config A
    m = C.build_model(cfg).eval()
    for mod in m.modules():   # non-trivial BN statistics
        if isinstance(mod, (torch.nn.BatchNorm2d, torch.nn.BatchNorm3d)):
            mod.running_mean.uniform_(-0.1, 0.1)
            mod.running_var.uniform_(0.5, 1.5)
    rng = np.random.default_rng(0)
    S = 640
    img = rng.integers(0, 256, (S, S, C.NZ)).astype(np.uint8)
    x = torch.from_numpy(C.norm(img)).permute(2, 0, 1)[None, None]
    with torch.no_grad():
        full = torch.sigmoid(m(x))
    H = IN.HALO
    y0 = 320 - 64
    sub = img[y0 - H:y0 + 128 + H, y0 - H:y0 + 128 + H]
    with torch.no_grad():
        w = torch.sigmoid(m(torch.from_numpy(C.norm(sub)).permute(2, 0, 1)[None, None]))
    a = full[0, 0, y0 // 4:(y0 + 128) // 4, y0 // 4:(y0 + 128) // 4]
    b = w[0, 0, H // 4:(H + 128) // 4, H // 4:(H + 128) // 4]
    d = float((a - b).abs().max())
    assert d < 1e-5, f'window/halo mismatch {d}'
    print('window equivalence ok', d)


def test_display():
    rng = np.random.default_rng(0)
    p = rng.random((C.T_TILE, C.T_TILE)).astype(np.float32)
    m = rng.random((C.T_TILE, C.T_TILE)) < 0.7
    b, u8, disp = C.display_png(C.to_u8(p), m)
    assert (u8[~m] == 0).all() and disp.shape == (C.OUT_SIDE, C.OUT_SIDE) and b[:8] == b'\x89PNG\r\n\x1a\n'
    assert C.to_u8(np.array([1.0, 0.999, -1, 2]))[1] == 254
    print('display ok')


if __name__ == '__main__':
    try:
        test_auc()
        test_derangement_folds_sched()
        test_display()
        test_window_equivalence()
        test_excl_format_a()
        data = test_build_patches()
        test_train_resume_infer(data)
        print('ALL OK')
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
