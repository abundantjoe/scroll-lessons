# Provenance: Project HERCULES | owner the owner | [id removed]
"""P4-OWN arm trainer (DECL-P4-23 items 4-5). Numbers only. Pattern: tools/d3/d3_train.py (fixed seeds, SeedSequence
streams, resumable checkpoints, jsonl log).

Arms: F1, F2, F3 (train on the patches of 2 of the 3 fold groups; a patch whose pixels touch a tile of another group
is excluded), S1, S2, S3 (all patches; seeds SEED, SEED+1, SEED+2), NULL (= S1 with the label arrays (ink, sup) of
patch i replaced by those of patch perm[i], perm = ONE fixed derangement, numpy default_rng(SEED).permutation redrawn
until no fixed point; D3 NULLA convention). F1-F3, S1 and NULL share SEED.
Schedule: the whole sampling and augmentation schedule is drawn up front from SeedSequence(seed) child streams:
  stream 0: epoch-wise permutations of the ink pool (patches with ink_frac >= 2 %, from the labels the arm sees);
  stream 1: epoch-wise permutations of the rest; each batch = B/2 from each pool (all from one if the other is empty);
  stream 2: per-sample augmentation: flip-y, flip-x, rot90 k in 0..3, gain U(0.9,1.1), offset U(-0.02,0.02);
  torch init: torch.manual_seed(seed).
So a resumed run replays exactly the same batches. Loss at output stride 4: target = mean ink over the 4x4 block,
mask = 4x4 blocks fully covered by (sup & mesh-valid) inside the patch's loss core (margin M = patch 'margin'); masked BCE-with-logits + soft Dice (smooth 1), weight 1:1.
AdamW (lr, wd), linear warm-up then cosine to 0, grad-norm clip 1.0, fp32, CPU.
Checkpoint every --ckpt-min minutes and at the end: <out>/resume_latest.pth (weights, optimizer, scheduler step, torch
RNG); <out>/model_final.pth + summary.json when done (a completed arm exits immediately)."""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

import own_common as C

SEED = 20260927
ARMS = ('F1', 'F2', 'F3', 'S1', 'S2', 'S3', 'NULL')


def derangement(n, seed=SEED):
    rng = np.random.default_rng(seed)
    while True:
        p = rng.permutation(n)
        if n < 2 or not np.any(p == np.arange(n)):
            return p


def fold_groups(tiles):
    """tiles: list of (seg, r, c) certified T tiles. Ordered by (strip, column, row), cut into 3 contiguous groups of
    near-equal tile count (np.array_split). Returns {(seg,r,c): g}."""
    order = sorted(set(map(tuple, tiles)), key=lambda t: (t[0], t[2], t[1]))
    return {t: g for g, part in enumerate(np.array_split(np.arange(len(order)), 3)) for t in (order[i] for i in part)}


def arm_patches(arm, patches, groups):
    """Indices of training patches for the arm."""
    if arm.startswith('F'):
        held = int(arm[1]) - 1
        idx = []
        for i, p in enumerate(patches):
            gs = {groups[(p['seg'], r, c)] for r, c in p['tiles']}
            if held not in gs and len(gs) == 1:
                idx.append(i)
        return np.array(idx, np.int64)
    return np.arange(len(patches), dtype=np.int64)


def schedule(seed, ink_pool, rest_pool, steps, batch):
    ss = np.random.SeedSequence(seed)
    s_ink, s_rest, s_aug = [np.random.default_rng(c) for c in ss.spawn(3)]

    def stream(rng, pool, n):
        out = []
        while len(out) < n:
            out.extend(pool[rng.permutation(len(pool))].tolist())
        return np.array(out[:n], np.int64)

    h = batch // 2
    if len(ink_pool) and len(rest_pool):
        a = stream(s_ink, ink_pool, steps * h).reshape(steps, h)
        b = stream(s_rest, rest_pool, steps * (batch - h)).reshape(steps, batch - h)
        idx = np.concatenate([a, b], 1)
    else:
        pool = ink_pool if len(ink_pool) else rest_pool
        idx = stream(s_ink, pool, steps * batch).reshape(steps, batch)
    aug = dict(fy=s_aug.integers(0, 2, (steps, batch)), fx=s_aug.integers(0, 2, (steps, batch)),
               k=s_aug.integers(0, 4, (steps, batch)), gain=s_aug.uniform(0.9, 1.1, (steps, batch)),
               off=s_aug.uniform(-0.02, 0.02, (steps, batch)))
    return idx, aug


def load_data(d, verify=True):
    man = json.load(open(os.path.join(d, 'build_manifest.json')))
    if verify:
        for f, h in man['files'].items():
            got = C.sha256_file(os.path.join(d, f))
            if got != h:
                raise SystemExit(f'shard {f} sha256 {got} != {h}')
    pj = json.load(open(os.path.join(d, 'patches.json')))
    arrs = {n: [] for n in ('x', 'ink', 'sup', 'valid')}
    for sd in sorted(os.listdir(d)):
        if sd.startswith('shard_'):
            for n in arrs:
                arrs[n].append(np.load(os.path.join(d, sd, f'{n}.npy'), mmap_mode='r'))
    data = {n: np.concatenate(v) if len(v) > 1 else np.asarray(v[0]) for n, v in arrs.items()}
    assert len(data['x']) == len(pj['patches']) == man['n_patches']
    return man, pj['patches'], data


def batch_tensors(torch, data, idx, lab_src, aug, s, li_margin=0):
    xs, ts, ms = [], [], []
    for j, i in enumerate(idx):
        x = C.norm(np.asarray(data['x'][i]))            # (62,P,P)
        li = lab_src[i]
        ink = data['ink'][li].astype(np.float32) / 255.0
        cov = data['sup'][li].astype(bool) & data['valid'][i].astype(bool)
        if aug['fy'][s, j]:
            x, ink, cov = x[:, ::-1], ink[::-1], cov[::-1]
        if aug['fx'][s, j]:
            x, ink, cov = x[:, :, ::-1], ink[:, ::-1], cov[:, ::-1]
        k = int(aug['k'][s, j])
        x, ink, cov = np.rot90(x, k, (1, 2)), np.rot90(ink, k), np.rot90(cov, k)
        x = x * np.float32(aug['gain'][s, j]) + np.float32(aug['off'][s, j])
        P = ink.shape[0]
        q = C.STRIDE_OUT
        cb = cov.reshape(P // q, q, P // q, q)
        m = cb.all((1, 3))
        mg = li_margin // q
        if mg:
            m[:mg], m[-mg:], m[:, :mg], m[:, -mg:] = False, False, False, False
        t = (ink * cov).reshape(P // q, q, P // q, q).sum((1, 3)) / np.maximum(cb.sum((1, 3)), 1)
        xs.append(np.ascontiguousarray(x))
        ts.append(t.astype(np.float32))
        ms.append(m)
    X = torch.from_numpy(np.stack(xs))[:, None]
    return X, torch.from_numpy(np.stack(ts))[:, None], torch.from_numpy(np.stack(ms))[:, None]


def loss_fn(torch, logit, t, m):
    F = torch.nn.functional
    mf = m.float()
    n = mf.sum().clamp_min(1.0)
    bce = (F.binary_cross_entropy_with_logits(logit, t, reduction='none') * mf).sum() / n
    p = torch.sigmoid(logit) * mf
    dice = 1 - (2 * (p * t * mf).sum() + 1) / (p.sum() + (t * mf).sum() + 1)
    return bce + dice, float(bce), float(dice)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arm', required=True, choices=ARMS)
    ap.add_argument('--data', required=True)
    ap.add_argument('--recipe', required=True, help='recipe.json (frozen with RECIPE.md)')
    ap.add_argument('--out', required=True)
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--ckpt-min', type=float, default=15.0)
    ap.add_argument('--steps', type=int, default=0, help='override (tests only)')
    ap.add_argument('--no-verify', action='store_true')
    ap.add_argument('--die-after', type=int, default=0, help='TEST ONLY: checkpoint and exit(99) after this step')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    FINAL, SUMMARY, RESUME = (os.path.join(a.out, n) for n in ('model_final.pth', 'summary.json', 'resume_latest.pth'))
    if os.path.exists(FINAL) and os.path.exists(SUMMARY):
        print(f'arm {a.arm}: complete; nothing to do', flush=True)
        return
    import torch
    torch.set_num_threads(a.threads)
    rc = json.load(open(a.recipe))
    steps = a.steps or rc['steps']
    batch, cfg = rc['batch'], rc['model']
    seed = SEED + {'S2': 1, 'S3': 2}.get(a.arm, 0)
    log = C.jlog(os.path.join(a.out, 'train_log.jsonl'))
    man, patches, data = load_data(a.data, verify=not a.no_verify)
    n = len(patches)
    margin = int(patches[0].get('margin', 0)) if patches else 0
    assert all(int(p.get('margin', 0)) == margin for p in patches)
    if 'fold_groups' in rc:     # frozen in RECIPE: certified T tiles -> group
        groups = {(s, int(r), int(c)): int(g) for s, r, c, g in rc['fold_groups']}
        missing = {(p['seg'], r, c) for p in patches for r, c in p['tiles']} - set(groups)
        assert not missing, f'patch tiles outside the certified fold list: {sorted(missing)[:5]}'
    else:
        groups = fold_groups([(p['seg'], r, c) for p in patches for r, c in p['tiles']])
    lab_src = derangement(n) if a.arm == 'NULL' else np.arange(n)
    idx_arm = arm_patches(a.arm, patches, groups)
    inkf = np.array([patches[lab_src[i]]['ink_frac'] for i in range(n)])
    ink_pool = idx_arm[inkf[idx_arm] >= 0.02]
    rest_pool = idx_arm[inkf[idx_arm] < 0.02]
    sched_idx, aug = schedule(seed, ink_pool, rest_pool, steps, batch)
    sched_sha = C.arr_sha(np.concatenate([sched_idx.ravel().astype(np.float64)] +
                                         [aug[k].ravel().astype(np.float64) for k in sorted(aug)]))
    train_ids = sorted(int(i) for i in idx_arm)
    tm = dict(arm=a.arm, data_manifest_sha256=C.sha256_file(os.path.join(a.data, 'build_manifest.json')),
              train_patch_ids=train_ids, label_source=[int(lab_src[i]) for i in train_ids],
              min_dist_to_X_mm=min(patches[i]['min_dist_mm'] for i in train_ids))
    tm_bytes = json.dumps(tm, sort_keys=True).encode()
    open(os.path.join(a.out, 'train_manifest.json'), 'wb').write(tm_bytes)
    torch.manual_seed(seed)
    model = C.build_model(cfg)
    opt = torch.optim.AdamW(model.parameters(), lr=rc['lr'], weight_decay=rc['wd'])
    warm = rc['warmup']

    def lr_at(s):
        if s < warm:
            return rc['lr'] * (s + 1) / warm
        return rc['lr'] * 0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, steps - warm)))

    s0 = 0
    if os.path.exists(RESUME):
        ck = torch.load(RESUME, weights_only=False)
        model.load_state_dict(ck['model'])
        opt.load_state_dict(ck['opt'])
        torch.set_rng_state(ck['torch_rng'])
        s0 = ck['step']
        assert ck['sched_sha'] == sched_sha
        log(dict(resume_from_step=s0))
    else:
        log(dict(start=True, arm=a.arm, seed=seed, n_patches=n, n_train=len(idx_arm), n_ink_pool=len(ink_pool),
                 n_rest_pool=len(rest_pool), steps=steps, batch=batch, params=C.n_params(model), sched_sha=sched_sha,
                 train_manifest_sha256=C.sha_bytes(tm_bytes), recipe_sha256=C.sha256_file(a.recipe),
                 derangement_fixed_points=int(np.sum(lab_src == np.arange(n))) if a.arm == 'NULL' else None,
                 threads=a.threads))

    def save(step, path):
        tmp = path + '.tmp'
        torch.save(dict(model=model.state_dict(), opt=opt.state_dict(), torch_rng=torch.get_rng_state(), step=step,
                        sched_sha=sched_sha), tmp)
        os.replace(tmp, path)

    model.train()
    t_ck = time.time()
    t_start = time.time()
    acc = []
    for s in range(s0, steps):
        for g in opt.param_groups:
            g['lr'] = lr_at(s)
        X, t, m = batch_tensors(torch, data, sched_idx[s], lab_src, aug, s, margin)
        logit = model(X)
        loss, b, d = loss_fn(torch, logit, t, m)
        opt.zero_grad()
        loss.backward()
        gn = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
        opt.step()
        acc.append((float(loss), b, d, gn))
        if (s + 1) % rc.get('log_every', 25) == 0 or s + 1 == steps:
            A = np.array(acc)
            log(dict(step=s + 1, loss=float(A[:, 0].mean()), bce=float(A[:, 1].mean()), dice=float(A[:, 2].mean()),
                     grad_norm=float(A[:, 3].mean()), lr=lr_at(s),
                     s_per_step=round((time.time() - t_start) / (s + 1 - s0), 3)))
            acc = []
        if a.die_after and s + 1 == a.die_after:
            save(s + 1, RESUME)
            os._exit(99)
        if time.time() - t_ck > a.ckpt_min * 60 and s + 1 < steps:
            save(s + 1, RESUME)
            t_ck = time.time()
            log(dict(checkpoint=s + 1))
    torch.save(dict(model=model.state_dict(), cfg=cfg, arm=a.arm, seed=seed, steps=steps,
                    train_manifest_sha256=C.sha_bytes(tm_bytes), recipe_sha256=C.sha256_file(a.recipe)), FINAL)
    summ = dict(provenance=C.PROV, arm=a.arm, steps=steps, seed=seed, model_final_sha256=C.sha256_file(FINAL),
                train_manifest_sha256=C.sha_bytes(tm_bytes), min_dist_to_X_mm=tm['min_dist_to_X_mm'],
                recipe_sha256=C.sha256_file(a.recipe), data_manifest_sha256=tm['data_manifest_sha256'],
                n_train=len(idx_arm), code_sha256={f: C.sha256_file(os.path.join(C.HERE, f))
                                                  for f in ('train.py', 'own_common.py')}, utc=C.utc())
    json.dump(summ, open(SUMMARY, 'w'), indent=1)
    if os.path.exists(RESUME):
        os.remove(RESUME)
    log(dict(done=True, **summ))


if __name__ == '__main__':
    sys.exit(main())
