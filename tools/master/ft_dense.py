#!/usr/bin/env python3
# Provenance: Project HERCULES | [id removed]
"""DECL-FL-7-A1: fine-tune the public dense_native 9 um ink model (Nieuwlaar/ink9um-dense-native step 16000) on the
PHerc0009B training shards at 8.64 um; encoder (shared_encoder + depth_fusion stem) frozen, shared_decoder + task_heads
trainable; AdamW lr 1e-4 wd 1e-2, batch 4, fp32, Dice+BCE on (y > 127). Input adapter = the model's own flat-inference
path (select_layer_indices center crop to 17 layers, centered short-depth zero placement, tifxyz_robust per-crop
normalization), exactly as in the baseline scoring recipe. Evaluation every 250 steps on the held-out shard with
eval_master.py semantics (pixel AUC, pixel AP, tile AUC of 64x64 crops by mean probability vs label fraction > 0.05;
the tile AUC by crop p95 of baseline_eval.py is reported alongside). Never trains on PHerc0343P.
usage: ft_dense.py --train <shards...> --val <shard> --out <dir> --ckpt-out <path.pt> [--steps 2000] [--eval-every 250]"""
import argparse, glob, json, os, sys, time, hashlib, numpy as np, torch, torch.nn.functional as F
from pathlib import Path
from vesuvius.ink_detection.inference import infer as I

def auc(s, l):
    o = np.argsort(s); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1); l = l > 0.5; n1 = l.sum(); n0 = len(l) - n1
    return float((r[l].sum() - n1 * (n1 + 1) / 2) / max(n1 * n0, 1))

def avg_precision(s, l):
    o = np.argsort(-s); l = (l[o] > 0.5); tp = np.cumsum(l); prec = tp / np.arange(1, len(l) + 1); return float((prec * l).sum() / max(l.sum(), 1))

def adapt(stack_DHW, depth_out):
    """The flat-inference input adapter: center-crop the source layers to depth_out (forward order), place them centered
    in a zero depth-out stack (short-depth padding), robust-normalize per crop. Returns float32 (depth_out, H, W)."""
    idx = I.select_layer_indices(stack_DHW.shape[0], layer_start=None, layer_end=None, output_depth=depth_out, direction='forward')
    out = np.zeros((depth_out,) + stack_DHW.shape[1:], np.uint8); s = (depth_out - idx.size) // 2; out[s:s + idx.size] = stack_DHW[idx]
    return I.normalize_flat_patch(out, 'tifxyz_robust').astype(np.float32)

def evaluate(tm, X, Y, depth_out, bs=16):
    tm.eval(); sc, lb, tm_, tl, tp95 = [], [], [], [], []
    with torch.no_grad():
        for i in range(0, len(X), bs):
            x = torch.from_numpy(np.stack([adapt(s, depth_out) for s in X[i:i + bs]])).unsqueeze(1)
            p = torch.sigmoid(tm(x).float()).numpy()[:, 0]; y = Y[i:i + bs] / 255.0
            sc.append(p.ravel()); lb.append(y.ravel()); tm_.append(p.reshape(len(p), -1).mean(1)); tp95.append(np.percentile(p.reshape(len(p), -1), 95, axis=1)); tl.append((y.reshape(len(y), -1) > 0.5).mean(1) > 0.05)
    sc, lb, ts, tp, tl = map(np.concatenate, (sc, lb, tm_, tp95, tl)); tm.train()
    return {'n_crops': int(len(X)), 'pixel_auc': round(auc(sc, lb), 4), 'pixel_ap': round(avg_precision(sc, lb), 4), 'tile_auc': round(auc(ts, tl.astype(float)), 4), 'tile_auc_p95': round(auc(tp, tl.astype(float)), 4), 'label_frac': round(float((lb > 0.5).mean()), 4), 'bars': {'auc': 0.9, 'ap': 0.5, 'tile_auc': 0.85}}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--train', nargs='+', required=True); ap.add_argument('--val', required=True); ap.add_argument('--out', required=True); ap.add_argument('--ckpt-out', required=True)
    ap.add_argument('--base', default='/work/ckpt/dense_native/dense_native_016000.pth'); ap.add_argument('--steps', type=int, default=2000); ap.add_argument('--eval-every', type=int, default=250)
    ap.add_argument('--bs', type=int, default=4); ap.add_argument('--lr', type=float, default=1e-4); ap.add_argument('--wd', type=float, default=1e-2); ap.add_argument('--seed', type=int, default=0); ap.add_argument('--max-hours', type=float, default=6.0)
    a = ap.parse_args(); O = Path(a.out); O.mkdir(parents=True, exist_ok=True); torch.manual_seed(a.seed); rng = np.random.default_rng(a.seed); torch.set_num_threads(max(1, os.cpu_count() or 4))
    log = open(O / 'train.log', 'a'); P = lambda *s: (print(*s, flush=True), print(*s, file=log, flush=True))
    assert not any('PHerc0343P' in t for t in a.train), 'held-out scroll in the training list'
    Xs, Ys, names = [], [], []
    for t in a.train:
        d = np.load(t); Xs.append(d['x']); Ys.append(d['y']); names.append(os.path.basename(t)); P('train shard', t, d['x'].shape, 'label mean', round(float(d['y'].mean() / 255), 4))
    X = np.concatenate(Xs); Y = np.concatenate(Ys); dv = np.load(a.val); XV, YV = dv['x'], dv['y']; P('train', X.shape, 'val', XV.shape, a.val)
    c = I.configure_model(argparse.Namespace(checkpoint=Path(a.base), amp_dtype='default')); tm = c.model; base = tm.model; D = c.input_depth
    payload = torch.load(a.base, map_location='cpu', weights_only=False); cfg = payload['config']
    for n, p in base.named_parameters(): p.requires_grad = n.startswith('network.shared_decoder') or n.startswith('network.task_heads')
    tr = [p for p in base.parameters() if p.requires_grad]
    P('base', a.base, 'sha256', hashlib.sha256(open(a.base, 'rb').read()).hexdigest(), 'input depth', D, 'patch', c.patch_size, 'prep', c.preprocessing)
    P('trainable params', sum(p.numel() for p in tr), 'frozen', sum(p.numel() for p in base.parameters() if not p.requires_grad), 'state_dict numel', sum(v.numel() for v in base.state_dict().values()))
    opt = torch.optim.AdamW(tr, lr=a.lr, weight_decay=a.wd); tm.train(); best = {'pixel_auc': -1}; hist = []
    def do_eval(step):
        r = evaluate(tm, XV, YV, D); r.update(step=step, shard=a.val); json.dump(r, open(O / f'eval_{step}.json', 'w'), indent=1); hist.append(r); P('EVAL', json.dumps(r)); return r
    r0 = do_eval(0); best = r0; torch.save({'model': base.state_dict(), 'config': cfg, 'step': 0, 'base': a.base, 'metrics': r0, 'train_shards': names}, a.ckpt_out)  # step 0 = base weights is a candidate: the kept checkpoint is never worse than the base on held-out AUC
    t_run = time.time(); times = []
    for step in range(1, a.steps + 1):
        t0 = time.time(); sel = rng.integers(0, len(X), a.bs)
        x = torch.from_numpy(np.stack([adapt(X[i], D) for i in sel])).unsqueeze(1); y = torch.from_numpy((Y[sel] > 127).astype(np.float32)).unsqueeze(1)
        logit = tm(x); bce = F.binary_cross_entropy_with_logits(logit, y); p = torch.sigmoid(logit); dice = 1 - (2 * (p * y).sum() + 1) / (p.sum() + y.sum() + 1); loss = bce + dice
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step(); times.append(time.time() - t0)
        if step % 10 == 0: P(f'step {step} loss {loss.item():.4f} bce {bce.item():.4f} dice {dice.item():.4f} step_s {np.mean(times[-10:]):.3f}')
        if step == 20:
            proj = float(np.mean(times)) * a.steps / 3600; tj = {'measured_steps': 20, 'mean_step_s': round(float(np.mean(times)), 4), 'projected_hours_for_steps': round(proj, 3), 'steps': a.steps, 'limit_hours': a.max_hours, 'abandon': proj > a.max_hours, 'threads': torch.get_num_threads(), 'bs': a.bs}
            json.dump(tj, open(O / 'timing.json', 'w'), indent=1); P('TIMING', json.dumps(tj))
            if proj > a.max_hours: P('ABANDONED: projected time exceeds the limit'); open(O / 'ABANDONED', 'w').write(json.dumps(tj)); break
        if step % a.eval_every == 0 or step == a.steps:
            r = do_eval(step)
            if r['pixel_auc'] > best['pixel_auc']:
                best = r; torch.save({'model': base.state_dict(), 'config': cfg, 'step': step, 'base': a.base, 'metrics': r, 'train_shards': names}, a.ckpt_out); P('BEST saved', a.ckpt_out, 'step', step, 'auc', r['pixel_auc'])
    json.dump({'best': best, 'history': hist, 'train_shards': names, 'n_train_crops': int(len(X)), 'wall_s': round(time.time() - t_run, 1)}, open(O / 'history.json', 'w'), indent=1); P('FINISHED best', json.dumps(best))

if __name__ == '__main__': main()
