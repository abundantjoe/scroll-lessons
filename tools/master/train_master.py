# Provenance: Project HERCULES | [id removed]
"""Two-stage training on CPU. Stage A (ssl): DINO-3D on unlabelled stacks (crops of the same npz shards, labels ignored,
plus any extra shards e.g. PHerc0268 chunks). Stage B (sup): Master = EdgeBank -> UNet3D (+ frozen SSL features) with
Dice+BCE, AdamW, bf16 autocast, validation AUC on a held-out shard list. Every epoch logs train loss, val AUC, val AP.
usage: train_master.py ssl --shards a.npz b.npz --out ssl.pt --steps 2000 --bs 8
       train_master.py sup --train a.npz b.npz --val c.npz --ssl ssl.pt --out master.pt --epochs 8 --bs 8"""
import argparse, json, time, random, numpy as np, torch, torch.nn.functional as F, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ssl3d import CNNEncoder3D, DINO3D, augment3d; from master import Master; from unet3d import dice_bce
torch.set_num_threads(max(1, os.cpu_count() or 4))

def load(shards, depth=None):
    xs, ys = [], []
    for s in shards:
        d = np.load(s); x = d['x']; y = d['y']
        if depth and x.shape[1] != depth:
            c = x.shape[1] // 2; x = x[:, max(0, c - depth // 2):max(0, c - depth // 2) + depth]
        xs.append(x); ys.append(y)
    return np.concatenate(xs), np.concatenate(ys)

def auc(scores, labels):
    o = np.argsort(scores); r = np.empty(len(o)); r[o] = np.arange(1, len(o) + 1); pos = labels > 0.5; n1, n0 = pos.sum(), (~pos).sum()
    return float((r[pos].sum() - n1 * (n1 + 1) / 2) / max(n1 * n0, 1))

def avg_precision(scores, labels):
    o = np.argsort(-scores); l = (labels[o] > 0.5); tp = np.cumsum(l); prec = tp / np.arange(1, len(l) + 1); return float((prec * l).sum() / max(l.sum(), 1))

def run_ssl(a):
    X, _ = load(a.shards); X = X[:, :, :64, :64] if X.shape[2] >= 64 else X; n, D = len(X), X.shape[1]; print('ssl crops', X.shape)
    enc = CNNEncoder3D(width=a.width, out_dim=192); dino = DINO3D(enc, out_dim=512); opt = torch.optim.AdamW([p for p in dino.student.parameters() if p.requires_grad], lr=a.lr, weight_decay=0.04); g = random.Random(0)
    t0 = time.time()
    for step in range(a.steps):
        idx = np.random.randint(0, n, a.bs); c = torch.from_numpy(X[idx]).float().unsqueeze(1) / 255.0
        v1, v2 = augment3d(c, g), augment3d(c, g); loc = [augment3d(c[:, :, :, 16:48, 16:48], g)]
        with torch.autocast('cpu', dtype=torch.bfloat16): loss = dino.loss([v1, v2], loc)
        if not torch.isfinite(loss): print(f'ssl step {step} non-finite loss, skipped', flush=True); opt.zero_grad(); continue
        opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(dino.student.parameters(), 3.0)
        for gr in opt.param_groups: gr['lr'] = a.lr * min(1.0, (step + 1) / 100)                 # linear warm-up
        opt.step(); dino.update_teacher()
        if step % 20 == 0: print(f'ssl step {step} loss {float(loss):.3f} {time.time()-t0:.0f}s', flush=True)
    torch.save({'encoder': enc.state_dict(), 'width': a.width, 'out_dim': 192}, a.out); print('saved', a.out)

def run_sup(a):
    Xt, Yt = load(a.train, a.depth); Xv, Yv = load(a.val, a.depth); print('train', Xt.shape, 'val', Xv.shape, 'label means', Yt.mean() / 255, Yv.mean() / 255)
    enc = None
    if a.ssl:
        ck = torch.load(a.ssl); enc = CNNEncoder3D(width=ck['width'], out_dim=ck['out_dim']); enc.load_state_dict(ck['encoder']); enc.eval()
    m = Master(ssl_encoder=enc, base=a.base, ssl_dim=(ck['width'] * 8 if a.ssl else 192))
    if a.init: m.load_state_dict(torch.load(a.init, map_location='cpu')['model']); print('init from', a.init)
    opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=a.lr, weight_decay=1e-2)
    n = len(Xt); steps = max(1, n // a.bs); steps = min(steps, a.max_steps) if a.max_steps else steps; best = -1; g = random.Random(1); hist = []
    for ep in range(a.epochs):
        m.train(); perm = np.random.permutation(n); tl = 0; t0 = time.time(); skipped = 0
        for s in range(steps):
            idx = perm[s * a.bs:(s + 1) * a.bs]; x = torch.from_numpy(Xt[idx]).float().unsqueeze(1) / 255.0; y = torch.from_numpy(Yt[idx]).float().unsqueeze(1) / 255.0
            if g.random() < 0.5: x, y = x.flip(-1), y.flip(-1)
            if g.random() < 0.5: x, y = x.flip(-2), y.flip(-2)
            k = int(g.random() * 4); x, y = torch.rot90(x, k, (-2, -1)), torch.rot90(y, k, (-2, -1))
            sh = int(g.random() * 5) - 2                                   # random depth shift of the stack: the misalignment robustness we want
            if sh: x = torch.roll(x, sh, dims=2)
            if a.bf16:
                with torch.autocast('cpu', dtype=torch.bfloat16): logit = m(x)
            else: logit = m(x)                                                  # fp32 by default: bf16 autocast produced non-finite gradients with finite losses (diag2, 2026-10-09)
            loss = dice_bce(logit.float(), (y > 0.5).float())
            if not torch.isfinite(loss): skipped += 1; opt.zero_grad(); continue
            opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(m.parameters(), 5.0); opt.step(); tl += float(loss.detach())
        m.eval(); sc, lb = [], []
        with torch.no_grad():
            for i in range(0, len(Xv), a.bs):
                x = torch.from_numpy(Xv[i:i + a.bs]).float().unsqueeze(1) / 255.0
                p = torch.sigmoid(m(x).float())
                sc.append(p.numpy().ravel()); lb.append(Yv[i:i + a.bs].ravel() / 255.0)
        sc, lb = np.concatenate(sc), np.concatenate(lb); finite = bool(np.isfinite(sc).all())
        if not finite: print('NON-FINITE validation scores: the weights diverged; aborting', flush=True); hist.append({'epoch': ep, 'train_loss': tl / max(steps - skipped, 1), 'skipped': skipped, 'diverged': True}); break
        A, P = auc(sc, lb), avg_precision(sc, lb); hist.append({'epoch': ep, 'train_loss': tl / max(steps - skipped, 1), 'skipped_steps': skipped, 'val_auc': A, 'val_ap': P, 'secs': time.time() - t0})
        print(json.dumps(hist[-1]), flush=True)
        if A > best: best = A; torch.save({'model': m.state_dict(), 'base': a.base, 'ssl': a.ssl, 'hist': hist, 'n_train': int(n)}, a.out)
    json.dump(hist, open(a.out + '.hist.json', 'w')); print('best val AUC', best, 'saved', a.out)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd')
    s1 = sub.add_parser('ssl'); s1.add_argument('--shards', nargs='+', required=True); s1.add_argument('--out', required=True); s1.add_argument('--steps', type=int, default=2000); s1.add_argument('--bs', type=int, default=8); s1.add_argument('--width', type=int, default=16); s1.add_argument('--lr', type=float, default=1e-4)
    s2 = sub.add_parser('sup'); s2.add_argument('--train', nargs='+', required=True); s2.add_argument('--val', nargs='+', required=True); s2.add_argument('--ssl', default=None); s2.add_argument('--out', required=True); s2.add_argument('--epochs', type=int, default=8); s2.add_argument('--bs', type=int, default=8); s2.add_argument('--base', type=int, default=16); s2.add_argument('--lr', type=float, default=3e-4); s2.add_argument('--init', default=None); s2.add_argument('--depth', type=int, default=16); s2.add_argument('--max_steps', type=int, default=0); s2.add_argument('--bf16', action='store_true', help='bf16 autocast in training (unstable on CPU: non-finite gradients); off by default')
    a = ap.parse_args(); run_ssl(a) if a.cmd == 'ssl' else run_sup(a)
