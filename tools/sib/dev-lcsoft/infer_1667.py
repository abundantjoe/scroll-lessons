#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""Minimal wrapper: official scrollprize/PHerc.1667-iteration-N checkpoints on a devloop render.

Numbers only: no image is written for viewing, opened or displayed. Output maps are written as uint8 TIFFs in
the devloop map format (<out>.tif = forward, <out>_reverse.tif = reverse; 2-D, same H x W as the render) and
are summarised by hashes and scalar statistics.

What is official and unchanged
  * the model: modeling_inkdetection.py + configuration_inkdetection.py + config.json + model.safetensors of the
    pinned HF commit (git blob oids and LFS sha256 verified against data/catalogue/checkpoints.json), loaded with
    transformers.AutoModel.from_pretrained(..., trust_remote_code=True) (transformers 4.57.6 = config.json's
    transformers_version; 5.x cannot import the official file);
  * the tiling: the card's "Full-segment inference (tiling)" loop (WINDOW 256, STRIDE 128, skip a tile if any
    fmask pixel is 0, sigmoid, F.interpolate x4 bilinear, sum/count average, uint8 = clip(pred*255) truncated),
    kept statement for statement in card_tiling() below.
What the wrapper adds (each item recorded in the run record)
  * normalisation: clip(0, 200) / 255, i.e. the card's training statement ("clipped raw uint8 layers to [0, 200]
    then applied Normalize(mean=0, std=1)"; albumentations max_pixel_value 255) and villa
    deprecated/ink-detection/train_resnet3d_lib (data_ops.py clip 0..200, config.py A.Normalize(mean=0, std=1)).
    The card's tiling snippet feeds raw 0..255 floats; the weights' bn1 running statistics fix the training scale
    at mean input 0.22-0.30 (logs/sib/ckpt-screen-b/SPECS.json bn1_input_scale), so /255 is used.
  * geometry (--mode):
      spec    resample the render to the model's voxel size (--model-um, default 2.399) in all three axes:
              62 layers at model-um spacing centred on the render surface slice (--surface-slice, default 15),
              linear in depth, bilinear in plane (pixel-centre aligned); after the card's tiling on that grid the
              probability map is area-averaged back to the render grid (cv2.INTER_AREA).
      native  no resampling: the official centre crop of --native-slices render slices (default 16, i.e.
              16 x 9.362 um = 150 um, the physical depth of 62 x 2.399 um) fed at the render voxel size.
  * direction: forward = model depth index increasing with render slice index; reverse = the same layers in
    reverse order (vesuvius.ink_detection.inference.infer select_layer_indices convention).
  * fmask: render-valid (any of the render slices nonzero), nearest-resampled to the model grid in spec mode.
Usage
  infer_1667.py --iteration N --render render.zarr --out OUT.tif [--direction both|forward|reverse]
                [--mode spec|native] [--threads 4] [--record rec.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CARDS = os.environ.get('CKB_CARDS_DIR', '/work/cards')  # verbatim HF card/code copies (not committed)
CKPT_DIR = os.environ.get('CKB_CKPT_DIR', '/work/ckpt')
HF_DIR = os.environ.get('CKB_HF_DIR', '/work/hf')
PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
WINDOW, STRIDE, D_MODEL = 256, 128, 62
CLIP_MAX, DIVISOR = 200.0, 255.0


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def arr_sha(a):
    a = np.ascontiguousarray(a)
    return hashlib.sha256(a.tobytes() + str(a.dtype).encode() + str(a.shape).encode()).hexdigest()


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def catalogue_entry(it):
    cat = json.load(open(os.path.join(REPO, 'data/catalogue/checkpoints.json')))
    for m in cat['all_scrollprize_hf_models']:
        if m['repo'] == f'scrollprize/PHerc.1667-iteration-{it}':
            return m
    raise KeyError(it)


def git_blob_oid(p):
    b = open(p, 'rb').read()
    return hashlib.sha1(b'blob %d\0' % len(b) + b).hexdigest()


def load_model(it):
    """Assemble the pinned HF snapshot (verified) in HF_DIR/itN and load it with AutoModel, unchanged."""
    import torch  # noqa: F401
    from transformers import AutoModel
    m = catalogue_entry(it)
    files = {f['path']: f for f in m['files']}
    d = os.path.join(HF_DIR, f'it{it}')
    os.makedirs(d, exist_ok=True)
    checks = {}
    for name in ('config.json', 'configuration_inkdetection.py', 'modeling_inkdetection.py'):
        src = os.path.join(CARDS, f'it{it}_{name}')
        ok = git_blob_oid(src) == files[name]['git_oid']
        checks[name] = dict(git_oid_ok=ok, sha256=sha256(src))
        if not ok:
            raise SystemExit(f'{name}: git blob oid mismatch against the catalogue')
        shutil.copyfile(src, os.path.join(d, name))
    wsrc = os.path.join(CKPT_DIR, f'PHerc.1667-iteration-{it}', 'model.safetensors')
    wsha = sha256(wsrc)
    if wsha != files['model.safetensors']['lfs_sha256']:
        raise SystemExit('model.safetensors: sha256 mismatch against the catalogue')
    checks['model.safetensors'] = dict(sha256=wsha, lfs_sha256_ok=True)
    dst = os.path.join(d, 'model.safetensors')
    if os.path.lexists(dst):
        os.remove(dst)
    os.symlink(wsrc, dst)
    model = AutoModel.from_pretrained(d, trust_remote_code=True).eval()
    return model, dict(repo=m['repo'], commit=m['commit_sha'], files=checks)


# ------------------------------------------------------------------------------------------------------------
# the card's tiling loop (statement for statement; the only change is that the per-tile (256,256,62) uint8
# slice `image[y:y+WINDOW, x:x+WINDOW]` is produced by `tile_fn` so that the spec-mode grid need not be held in
# memory, and that `.float()` is followed by the training normalisation `norm_fn`)
# ------------------------------------------------------------------------------------------------------------

def card_tiling(model, H, W, fmask, tile_fn, norm_fn, progress=None):
    import torch
    import torch.nn.functional as F
    mask_pred = np.zeros((H, W), dtype=np.float32)
    mask_count = np.zeros((H, W), dtype=np.float32)
    n = 0
    with torch.no_grad():
        for y in range(0, H - WINDOW + 1, STRIDE):
            for x in range(0, W - WINDOW + 1, STRIDE):
                if np.any(fmask[y:y + WINDOW, x:x + WINDOW] == 0):
                    continue
                tile = tile_fn(y, x)                                # (256,256,62)
                t = torch.from_numpy(tile).permute(2, 0, 1)         # (62,256,256)
                t = norm_fn(t.unsqueeze(0).unsqueeze(0).float())    # (1,1,62,256,256)
                logits = model(t).logits                            # (1,1,64,64)
                prob = torch.sigmoid(logits)
                prob = F.interpolate(prob, scale_factor=4,
                                     mode="bilinear").squeeze().cpu().numpy()
                mask_pred[y:y + WINDOW, x:x + WINDOW] += prob
                mask_count[y:y + WINDOW, x:x + WINDOW] += 1.0
                n += 1
                if progress:
                    progress(n)
    pred = np.divide(mask_pred, mask_count,
                     out=np.zeros_like(mask_pred),
                     where=mask_count != 0)
    return pred, mask_count


def train_norm(t):
    """clip(0, 200) then Normalize(mean=0, std=1, max_pixel_value=255) == /255."""
    return t.clamp_(0.0, CLIP_MAX).div_(DIVISOR)


def to_u8(pred):
    return np.clip(pred * 255, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------------------------------------------------
# geometry
# ------------------------------------------------------------------------------------------------------------

def centre_crop_indices(depth, out_depth):
    """Official centre crop (vesuvius center_crop_layer_indices / villa _compute_selected_layer_indices)."""
    idx = list(range(depth))
    if len(idx) > out_depth:
        s = (len(idx) - out_depth) // 2
        idx = idx[s:s + out_depth]
    if len(idx) != out_depth:
        raise ValueError(f'need >= {out_depth} slices, got {depth}')
    return np.asarray(idx)


def spec_depth_positions(surface, model_um, render_um, n=D_MODEL):
    """Render-slice coordinates of n layers at model_um spacing centred on the render surface slice."""
    k = np.arange(n, dtype=np.float64)
    return surface + (k - (n - 1) / 2.0) * (model_um / render_um)


class SpecGrid:
    """Render (Z,H,W) uint8 at render_um -> virtual (Hm,Wm,62) float32 grid at model_um, built per tile."""

    def __init__(self, render, surface, model_um, render_um, direction):
        import cv2
        self.cv2 = cv2
        self.r = render
        Z, H, W = render.shape
        self.f = render_um / model_um
        self.Hm, self.Wm = int(round(H * self.f)), int(round(W * self.f))
        zpos = spec_depth_positions(surface, model_um, render_um)
        if zpos.min() < 0 or zpos.max() > Z - 1:
            raise ValueError(f'spec depth range {zpos.min():.2f}..{zpos.max():.2f} outside render 0..{Z - 1}')
        self.z0 = np.floor(zpos).astype(int).clip(0, Z - 2)
        self.wz = (zpos - self.z0).astype(np.float32)
        if direction == 'reverse':
            self.z0, self.wz = self.z0[::-1].copy(), self.wz[::-1].copy()
        self.zpos = zpos

    def coords(self, n0, n, size):
        # model pixel centre i -> render coordinate (i + 0.5) / f - 0.5 (cv2.resize INTER_LINEAR alignment)
        return (np.arange(n0, n0 + n, dtype=np.float64) + 0.5) / self.f - 0.5

    def tile(self, y, x):
        cv2 = self.cv2
        Z, H, W = self.r.shape
        ry = self.coords(y, WINDOW, H)
        rx = self.coords(x, WINDOW, W)
        ya, yb = max(0, int(np.floor(ry.min())) - 1), min(H, int(np.ceil(ry.max())) + 2)
        xa, xb = max(0, int(np.floor(rx.min())) - 1), min(W, int(np.ceil(rx.max())) + 2)
        crop = self.r[:, ya:yb, xa:xb].astype(np.float32)
        lay = crop[self.z0] * (1.0 - self.wz[:, None, None]) + crop[self.z0 + 1] * self.wz[:, None, None]
        mx = np.broadcast_to((rx - xa).astype(np.float32)[None, :], (WINDOW, WINDOW))
        my = np.broadcast_to((ry - ya).astype(np.float32)[:, None], (WINDOW, WINDOW))
        mx, my = np.ascontiguousarray(mx), np.ascontiguousarray(my)
        out = np.empty((WINDOW, WINDOW, D_MODEL), np.float32)
        for k in range(D_MODEL):
            out[:, :, k] = cv2.remap(lay[k], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        return out

    def fmask(self, valid):
        return self.cv2.resize(valid.astype(np.uint8), (self.Wm, self.Hm), interpolation=self.cv2.INTER_NEAREST)

    def back(self, pred_m, H, W):
        return self.cv2.resize(pred_m, (W, H), interpolation=self.cv2.INTER_AREA)


def pad256(n):
    return n + (256 - n % 256)  # the card pads to multiples of 256 (villa data_ops: always adds a pad)


def run_direction(model, render, valid, mode, direction, a, log):
    Z, H, W = render.shape
    t0 = time.time()
    if mode == 'native':
        idx = centre_crop_indices(Z, a.native_slices)
        if direction == 'reverse':
            idx = idx[::-1]
        Hp, Wp = pad256(H), pad256(W)
        image = np.zeros((Hp, Wp, len(idx)), np.uint8)
        image[:H, :W] = np.transpose(render[idx], (1, 2, 0))
        fm = np.zeros((Hp, Wp), np.uint8)
        fm[:H, :W] = valid
        pred, cnt = card_tiling(model, Hp, Wp, fm, lambda y, x: image[y:y + WINDOW, x:x + WINDOW], train_norm)
        pred, cnt = pred[:H, :W], cnt[:H, :W]
        geo = dict(layers_render_slices=[int(i) for i in idx], model_grid_hw=[Hp, Wp])
    else:
        g = SpecGrid(render, a.surface_slice, a.model_um, a.render_um, direction)
        Hp, Wp = pad256(g.Hm), pad256(g.Wm)
        fm = np.zeros((Hp, Wp), np.uint8)
        fm[:g.Hm, :g.Wm] = g.fmask(valid)
        pred_m, cnt_m = card_tiling(model, Hp, Wp, fm, g.tile, train_norm)
        pred = g.back(pred_m[:g.Hm, :g.Wm], H, W)
        cnt = g.back(cnt_m[:g.Hm, :g.Wm], H, W)
        geo = dict(zoom=g.f, model_grid_hw=[g.Hm, g.Wm], padded_hw=[Hp, Wp],
                   layer_render_z_first_last=[float(g.zpos[0]), float(g.zpos[-1])],
                   depth_extent_um=float(D_MODEL * a.model_um))
    n_tiles = int(sum(1 for y in range(0, Hp - WINDOW + 1, STRIDE) for x in range(0, Wp - WINDOW + 1, STRIDE)
                      if not np.any(fm[y:y + WINDOW, x:x + WINDOW] == 0)))
    u8 = to_u8(pred)
    sec = time.time() - t0
    rec = dict(direction=direction, seconds=round(sec, 1), tiles=n_tiles,
               seconds_per_tile=round(sec / max(1, n_tiles), 3), covered_frac=float((cnt > 0).mean()),
               covered_frac_of_valid=float((cnt[valid > 0] > 0).mean()) if valid.any() else None,
               map_mean=float(u8.mean()), map_std=float(u8.std()), map_sha256=arr_sha(u8), **geo)
    log(rec)
    return u8, rec


def load_render(path):
    import zarr
    z = zarr.open(path, mode='r')
    a = z['0'] if hasattr(z, 'keys') and '0' in z else z
    return np.asarray(a[:])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--iteration', type=int, required=True, choices=range(6))
    ap.add_argument('--render', required=True, help='render.zarr (Z,H,W) uint8, or .npy for smoke tests')
    ap.add_argument('--out', required=True, help='forward map path (.tif); reverse is <stem>_reverse.tif')
    ap.add_argument('--direction', default='both', choices=['both', 'forward', 'reverse'])
    ap.add_argument('--mode', default='spec', choices=['spec', 'native'])
    ap.add_argument('--model-um', type=float, default=2.399)
    ap.add_argument('--render-um', type=float, default=9.362)
    ap.add_argument('--surface-slice', type=int, default=15)
    ap.add_argument('--native-slices', type=int, default=16)
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--record', default=None)
    a = ap.parse_args(argv)
    import tifffile
    import torch
    torch.set_num_threads(a.threads)
    torch.manual_seed(0)
    rec = dict(provenance=PROV, start_utc=utc(), args=vars(a), wrapper_sha256=sha256(os.path.abspath(__file__)),
               torch=torch.__version__, threads=torch.get_num_threads(), dtype='float32',
               normalisation=f'clip(0,{CLIP_MAX:g})/{DIVISOR:g}', window=WINDOW, stride=STRIDE)
    import transformers
    rec['transformers'] = transformers.__version__
    model, rec['checkpoint'] = load_model(a.iteration)
    render = np.load(a.render) if a.render.endswith('.npy') else load_render(a.render)
    if render.dtype != np.uint8 or render.ndim != 3:
        raise SystemExit(f'render must be (Z,H,W) uint8, got {render.dtype} {render.shape}')
    valid = (render != 0).any(0).astype(np.uint8)
    rec['render'] = dict(shape=list(render.shape), sha256=arr_sha(render), valid_frac=float(valid.mean()),
                         normalised_mean_valid=float(np.clip(render[:, valid > 0], 0, CLIP_MAX).mean() / DIVISOR)
                         if valid.any() else None)
    dirs = ('forward', 'reverse') if a.direction == 'both' else (a.direction,)
    stem, ext = os.path.splitext(a.out)
    rec['outputs'] = {}
    for d in dirs:
        u8, r = run_direction(model, render, valid, a.mode, d, a, lambda r: print(json.dumps(r), flush=True))
        p = a.out if d == 'forward' else f'{stem}_reverse{ext}'
        os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
        tifffile.imwrite(p, u8, compression='lzw')
        r['path'] = p
        r['file_sha256'] = sha256(p)
        rec['outputs'][d] = r
    rec['end_utc'] = utc()
    if a.record:
        with open(a.record, 'w') as f:
            json.dump(rec, f, indent=1)
    print(json.dumps(dict(done=True, outputs={k: v['map_sha256'] for k, v in rec['outputs'].items()})))
    return rec


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
