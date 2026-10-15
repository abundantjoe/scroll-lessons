#!/usr/bin/env python3
"""Provenance: Project HERCULES | [id removed]
DECL-FL-7 item 3(ii), public-model comparison: run the public ink-8um-v8in model (Hugging Face YoussefMoNader/ink-8um-v8in,
MIT, revision d89166b) on an organizer 8.64 um surface volume and write a full-canvas probability map.

Smallest faithful wrapper. The public repository ships predict.py / ink8um/{modeling,inference}.py, but that code was not
importable here (external-code download refused by the session's permission policy), so the network and the released
full-surface recipe are re-implemented below from the public model card, config.json and ink8um/*.py (read, not executed):
  model   InstanceNorm3d(1, affine) -> trilinear resample to (96, 256, 256) -> ResNet3D-50 (Kinetics-style, conv1 (7,7,7)
          stride (1,2,2), maxpool (1,3,3)/(1,2,2), Bottleneck [3,4,6,3], 1 input channel) -> max over depth at each of the
          4 levels -> 2-D U-Net decoder (conv3x3-BN-ReLU per level, bilinear x2) -> 1x1 logit head -> (B,1,64,64) logits.
          Parameter names match the checkpoint (loaded strict=True from model.safetensors).
  input   24 consecutive layers (the centred 24 of a deeper stack, or --layer-start), uint8 (uint16 >> 8) clipped to
          [0, 200], times 1/255; depth reversed with --reverse (never XY).
  recipe  coverage = max over depth > 0, closed with a 7x7 ellipse; 64 px tiles at stride 21 fully inside coverage;
          sigmoid; tiles weighted by gkern(64, 1)/max (normal-CDF Gaussian, +-1 sigma across the tile) and the weighted
          sum divided by the per-pixel tile COUNT (not the weight sum); clip to [0, 1]. The release used fp16 autocast
          on CUDA; here --precision fp32 (default) or bf16 autocast on CPU (reported with its measured deviation).
usage: v8in_infer.py <sv.zarr dir | shard.npz> <weights.safetensors> <out.tif> [--reverse] [--layer-start N]
          [--stride 21] [--batch 16] [--precision fp32|bf16] [--threads 4] [--png out_q4.png] [--crops-json out.json]
A shard.npz input (tools/master/build_data.py) runs the model on the shard's own (D,64,64) crops only (no stitching) and
writes per-crop probabilities to --crops-json; that is the exact-alignment check, not the released recipe.
"""
import argparse, hashlib, json, math, os, sys, time
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F

# ----------------------------------------------------------------- network (names identical to the public checkpoint)
def conv3x3x3(i, o, s=1): return nn.Conv3d(i, o, 3, stride=s, padding=1, bias=False)
def conv1x1x1(i, o, s=1): return nn.Conv3d(i, o, 1, stride=s, bias=False)

class Bottleneck(nn.Module):
    expansion = 4
    def __init__(self, inp, planes, stride=1, downsample=None):
        super().__init__(); self.conv1 = conv1x1x1(inp, planes); self.bn1 = nn.BatchNorm3d(planes)
        self.conv2 = conv3x3x3(planes, planes, stride); self.bn2 = nn.BatchNorm3d(planes)
        self.conv3 = conv1x1x1(planes, planes * 4); self.bn3 = nn.BatchNorm3d(planes * 4)
        self.relu = nn.ReLU(inplace=True); self.downsample = downsample
    def forward(self, x):
        r = x if self.downsample is None else self.downsample(x)
        o = self.relu(self.bn1(self.conv1(x))); o = self.relu(self.bn2(self.conv2(o))); o = self.bn3(self.conv3(o))
        return self.relu(o + r)

class ResNet3DEncoder(nn.Module):
    def __init__(self, layers=(3, 4, 6, 3), planes=(64, 128, 256, 512)):
        super().__init__(); self.in_planes = planes[0]
        self.conv1 = nn.Conv3d(1, planes[0], kernel_size=(7, 7, 7), stride=(1, 2, 2), padding=(3, 3, 3), bias=False)
        self.bn1 = nn.BatchNorm3d(planes[0]); self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool3d(kernel_size=(1, 3, 3), stride=(1, 2, 2), padding=(0, 1, 1))
        self.layer1 = self._make(planes[0], layers[0]); self.layer2 = self._make(planes[1], layers[1], 2)
        self.layer3 = self._make(planes[2], layers[2], 2); self.layer4 = self._make(planes[3], layers[3], 2)
        self.out_channels = [p * 4 for p in planes]
    def _make(self, planes, blocks, stride=1):
        ds = None
        if stride != 1 or self.in_planes != planes * 4:
            ds = nn.Sequential(conv1x1x1(self.in_planes, planes * 4, stride), nn.BatchNorm3d(planes * 4))
        L = [Bottleneck(self.in_planes, planes, stride, ds)]; self.in_planes = planes * 4
        L += [Bottleneck(self.in_planes, planes) for _ in range(1, blocks)]; return nn.Sequential(*L)
    def forward(self, x):
        x = self.maxpool(self.relu(self.bn1(self.conv1(x)))); x1 = self.layer1(x); x2 = self.layer2(x1); x3 = self.layer3(x2)
        return [x1, x2, x3, self.layer4(x3)]

class Decoder2D(nn.Module):
    def __init__(self, dims):
        super().__init__()
        self.convs = nn.ModuleList([nn.Sequential(nn.Conv2d(dims[i] + dims[i - 1], dims[i - 1], 3, 1, 1, bias=False),
                                                  nn.BatchNorm2d(dims[i - 1]), nn.ReLU(inplace=True)) for i in range(1, len(dims))])
        self.logit = nn.Conv2d(dims[0], 1, 1, 1, 0)
    def forward(self, fm):
        fm = list(fm)
        for i in range(len(fm) - 1, 0, -1):
            fm[i - 1] = self.convs[i - 1](torch.cat([fm[i - 1], F.interpolate(fm[i], scale_factor=2, mode='bilinear')], 1))
        return self.logit(fm[0])

class InkDetector(nn.Module):
    def __init__(self, cfg):
        super().__init__(); assert cfg.get('encoder_depth', 50) == 50
        self.in_depth = int(cfg.get('in_depth', 24)); self.tile_size = int(cfg.get('tile_size', 64)); self.stride = int(cfg.get('stride', 21))
        self.clip_max = int(cfg.get('clip_max', 200)); self.up_hw = int(cfg.get('input_upsample_hw', 256)); self.up_d = int(cfg.get('input_upsample_depth', 96))
        self.reverse_layers = bool(cfg.get('reverse_layers', False))
        self.normalization = nn.InstanceNorm3d(1, affine=True); self.backbone = ResNet3DEncoder(); self.decoder = Decoder2D(self.backbone.out_channels)
    def forward(self, x):
        if x.ndim == 4: x = x[:, None]
        x = self.normalization(x); tgt = (self.up_d or int(x.shape[2]), self.up_hw, self.up_hw)
        if self.up_hw and tuple(x.shape[-3:]) != tgt: x = F.interpolate(x, size=tgt, mode='trilinear', align_corners=False)
        return self.decoder([torch.max(f, dim=2)[0] for f in self.backbone(x)])

# ----------------------------------------------------------------- recipe
def gkern(n=64, nsig=1.0):
    x = np.linspace(-nsig, nsig, n + 1); cdf = 0.5 * (1.0 + np.vectorize(math.erf)(x / math.sqrt(2.0))); k = np.diff(cdf); k2 = np.outer(k, k); return k2 / k2.sum()

def coverage_mask(stack_dhw):
    import cv2
    cov = (stack_dhw.max(axis=0) > 0).astype(np.uint8) * 255
    return cv2.morphologyEx(cov, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))

def tile_positions(mask, S=64, stride=21):
    inside = mask > 0; H, W = inside.shape; ig = np.pad(inside.astype(np.int64).cumsum(0).cumsum(1), ((1, 0), (1, 0))); pts = []
    for y in range(0, H - S + 1, stride):
        for x in range(0, W - S + 1, stride):
            if ig[y + S, x + S] - ig[y, x + S] - ig[y + S, x] + ig[y, x] == S * S: pts.append((x, y))
    return pts

def to_u8(a, clip_max):
    if a.dtype == np.uint16: a = (a >> 8).astype(np.uint8)
    elif a.dtype != np.uint8: raise ValueError(f'unsupported layer dtype {a.dtype}')
    return np.clip(a, 0, clip_max).astype(np.uint8, copy=False)

def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
    return h.hexdigest()

def load_model(weights, cfg):
    from safetensors.torch import load_file
    m = InkDetector(cfg); sd = load_file(weights); miss = m.load_state_dict(sd, strict=True); m.eval(); return m

def run_batch(model, tiles_u8, precision):
    x = torch.from_numpy(np.ascontiguousarray(tiles_u8)).float().mul_(np.float32(1.0 / 255.0))
    with torch.inference_mode(), torch.autocast('cpu', dtype=torch.bfloat16, enabled=(precision == 'bf16')):
        lg = model(x)
    return torch.sigmoid(lg.float())[:, 0].numpy()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('inp'); ap.add_argument('weights'); ap.add_argument('out')
    ap.add_argument('--config', default=None); ap.add_argument('--reverse', action='store_true'); ap.add_argument('--layer-start', type=int, default=None)
    ap.add_argument('--stride', type=int, default=None); ap.add_argument('--batch', type=int, default=16); ap.add_argument('--precision', default='fp32', choices=['fp32', 'bf16'])
    ap.add_argument('--threads', type=int, default=4); ap.add_argument('--png', default=None); ap.add_argument('--crops-json', default=None); ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--ckpt', default=None, help='checkpoint (.npz: numerator/count/index in full-surface mode, probabilities/index in shard mode), written every --ckpt-every batches and resumed if present')
    ap.add_argument('--ckpt-every', type=int, default=25)
    a = ap.parse_args(); torch.set_num_threads(a.threads); import tifffile, cv2
    cfg = json.load(open(a.config)) if a.config else json.load(open(os.path.join(os.path.dirname(a.weights), 'config.json')))
    model = load_model(a.weights, cfg); S, D = model.tile_size, model.in_depth; stride = a.stride or model.stride; t0 = time.time()
    rec = {'weights': a.weights, 'weights_sha256': sha256(a.weights), 'config': cfg, 'reverse': a.reverse, 'precision': a.precision, 'stride': stride,
           'tile': S, 'in_depth': D, 'torch': torch.__version__, 'threads': a.threads, 'n_params': int(sum(p.numel() for p in model.parameters()))}
    if a.inp.endswith('.npz'):   # exact-alignment check on shard crops
        d = np.load(a.inp, allow_pickle=True); X = d['x']; pos = d['pos']; n = len(X) if not a.limit else min(a.limit, len(X))
        ls = a.layer_start if a.layer_start is not None else max(0, (X.shape[1] - D) // 2); assert ls + D <= X.shape[1]
        P = np.zeros((n, S, S), np.float32); start = 0
        if a.ckpt and os.path.exists(a.ckpt):
            c = np.load(a.ckpt); assert c['reverse'] == a.reverse and c['n'] == n, 'checkpoint from a different run'; P, start = c['P'], int(c['i']); print(f'resumed at crop {start}', flush=True)
        for k, i in enumerate(range(start, n, a.batch)):
            t = to_u8(X[i:i + a.batch, ls:ls + D], model.clip_max)
            if a.reverse: t = np.ascontiguousarray(t[:, ::-1])
            P[i:i + a.batch] = run_batch(model, t, a.precision); print(f'{min(i + a.batch, n)}/{n} {time.time() - t0:.0f}s', flush=True)
            if a.ckpt and (k + 1) % a.ckpt_every == 0:
                np.savez(a.ckpt + '.tmp.npz', P=P, i=min(i + a.batch, n), n=n, reverse=a.reverse); os.replace(a.ckpt + '.tmp.npz', a.ckpt)
        np.save(a.out, P)
        rec.update({'mode': 'shard_crops', 'shard': a.inp, 'layer_start': ls, 'n_crops': int(n), 'seconds': time.time() - t0, 'pos': pos[:n].tolist()})
        json.dump(rec, open(a.crops_json or a.out + '.json', 'w')); print('wrote', a.out); return
    import zarr
    z = zarr.open(a.inp, mode='r'); z = z['0'] if hasattr(z, 'keys') and '0' in z else z
    Dz, H, W = z.shape; ls = a.layer_start if a.layer_start is not None else max(0, (Dz - D) // 2); assert ls + D <= Dz, f'need {D} layers from {ls}, have {Dz}'
    stack = to_u8(np.asarray(z[ls:ls + D]), model.clip_max)                          # (24, H, W) uint8
    if a.reverse: stack = np.ascontiguousarray(stack[::-1])
    pts = tile_positions(coverage_mask(stack), S, stride)
    if a.limit: pts = pts[:a.limit]
    blend = gkern(S, 1); blend = (blend / blend.max()).astype(np.float32)
    num = np.zeros((H, W), np.float32); cnt = np.zeros((H, W), np.float32); start = 0
    if a.ckpt and os.path.exists(a.ckpt):
        c = np.load(a.ckpt); assert c['stride'] == stride and c['reverse'] == a.reverse and c['n'] == len(pts), 'checkpoint from a different run'
        num, cnt, start = c['num'], c['cnt'], int(c['i']); print(f'resumed at tile {start}', flush=True)
    print(f'stack {stack.shape} layers {ls}..{ls + D - 1} of {Dz}, tiles {len(pts)} at stride {stride}', flush=True)
    for k, i in enumerate(range(start, len(pts), a.batch)):
        b = pts[i:i + a.batch]; t = np.stack([stack[:, y:y + S, x:x + S] for x, y in b]); p = run_batch(model, t, a.precision)
        for pr, (x, y) in zip(p, b): num[y:y + S, x:x + S] += pr * blend; cnt[y:y + S, x:x + S] += 1.0
        if k % 20 == 0: print(f'{min(i + a.batch, len(pts))}/{len(pts)} {time.time() - t0:.0f}s', flush=True)
        if a.ckpt and (k + 1) % a.ckpt_every == 0:
            np.savez(a.ckpt + '.tmp.npz', num=num, cnt=cnt, i=i + len(b), n=len(pts), stride=stride, reverse=a.reverse); os.replace(a.ckpt + '.tmp.npz', a.ckpt)
    pred = np.clip(np.nan_to_num(np.divide(num, cnt, out=np.zeros_like(num), where=cnt != 0)), 0, 1).astype(np.float32)
    tifffile.imwrite(a.out, pred)
    if a.png: cv2.imwrite(a.png, cv2.resize((pred * 255).astype(np.uint8), None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA))
    rec.update({'mode': 'full_surface', 'input': a.inp, 'sv_shape': [int(Dz), int(H), int(W)], 'layer_start': ls, 'layers_used': [ls, ls + D - 1], 'n_tiles': len(pts),
                'covered_frac': float((cnt > 0).mean()), 'seconds': time.time() - t0, 'out': a.out, 'out_sha256': sha256(a.out)})
    json.dump(rec, open(a.out + '.json', 'w'), indent=1); print(json.dumps({k: v for k, v in rec.items() if k != 'config'}))

if __name__ == '__main__': main()
