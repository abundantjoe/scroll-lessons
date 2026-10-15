# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-DEVLOOP-SCREEN wrapper (task ckpt-screen-c): run an official scrollprize ink checkpoint on a devloop render
through the OFFICIAL villa inference code (ink-detection/optimized_inference at the pinned villa SHA), unchanged, and
write the devloop map format: <out>.tif (forward depth order) and <out>_reverse.tif, uint8, 2-D, same canvas as the
render. Numbers only: no image is displayed or opened for viewing; the run record holds hashes and summary numbers.

What the wrapper does (and nothing else):
  1. reads the render (31, H, W) uint8 zarr written by vc_render_tifxyz (surface = index 15, devloop N_SLICES = 31);
  2. selects the checkpoint's documented slice window around the surface in two depth orders (see SPECS below):
       forward  = render indices s + o for o in offsets (increasing render index),
       reverse  = render indices s - o for the same offsets (the mirrored window, surface at the same stack position);
  3. builds the model with the official code (villa model_timesformer.load_model for the Lightning .ckpt; the HF repo's
     own model class + strict safetensors load for HF repos, whose .safetensors the villa torch.load path cannot read);
  4. calls villa inference.run_inference (clip 0..200, /200, 64 px tiles stride 16 unless the spec says otherwise,
     sigmoid, bilinear to tile, Hann overlap-add) and villa processing.reduce_partitions (divide, clip 0..1, *255,
     astype uint8), unchanged;
  5. precision: 'fp32' disables torch.autocast (the only runtime deviation; the villa code autocasts, which on CPU is
     bfloat16); 'official' leaves it as written.
Usage:
  python screen_infer.py --ckpt NAME --weights PATH --render render.zarr --out OUT.tif [--threads 4] [--precision fp32]
         [--orders forward reverse] [--batch-size 32] [--window primary|alt]
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import fcntl
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import types

import numpy as np

PROV = 'Provenance: Project HERCULES | owner the owner | [id removed]'
VILLA = os.environ.get('CKSCR_VILLA', '/work/villa')
VILLA_SHA = '41701aa0eaa1aa765523db3f9f972b5830abf549'
OI = os.path.join(VILLA, 'ink-detection', 'optimized_inference')
CARDS = os.environ.get('CKSCR_CARDS', '/work/ckscr/cards')
N_SLICES = 31
SURFACE = 15
LOCK = '/tmp/ckscr_infer.lock'
PARTITION_CACHE = '/tmp/partition_cache'   # fixed path used by villa processing.reduce_partitions (never overwritten)

# Input specs. offsets = slice offsets from the surface in vc_render_tifxyz --flip-normals index order (the devloop
# render and the organizer production render use the same binary and flag). 'primary' is the organizer-documented
# production spec where one exists, else the checkpoint's own card/training code; 'alt' is the other documented window.
#   PROD27: official bucket metadata.json (sha256 8119d1c2...) production run of timesformer_scroll5_july_retreat on
#     PHerc0172: vc_render_tifxyz num-slices 33, flip-normals true -> ink-detection start-layer 3, end-layer 30,
#     tile 64, stride 16, force-reverse false = 27 slices centred on the surface, offsets -13..+13, forward order.
#     The registry entry of timesformer_GP_scroll1 (20230702185753) lists the same defaults (27 layers, 64, 16).
#   TRAIN26: villa deprecated/ink-detection/train_timesformer_og.py read_image_mask(start_idx=17, end_idx=43) on
#     65-layer 2023 surface volumes (surface = layer 32) -> offsets -15..+10 (legacy layer order; its mapping to the
#     flip-normals order is not documented, hence both depth orders).
#   RESNET18: card config num_layers=18, window_size=256; centring per villa deprecated inference_resnet3d.py
#     (start = mid - n // 2) -> offsets -9..+8; stride 64 is a wrapper choice (not documented).
PROD27 = list(range(-13, 14))
TRAIN26 = list(range(-15, 11))
RESNET18 = list(range(-9, 9))
_TF_HF = dict(config_py='timesformer_config', model_py='timesformer_model', config_cls='TimesformerScrollprizeConfig',
              model_cls='TimesformerScrollprizeModel', scale=16)
SPECS = {
    'timesformer_scroll5_july_retreat': dict(kind='pl_timesformer', tile=64, stride=16,
                                             windows=dict(primary=PROD27, alt=TRAIN26)),
    'timesformer_GP_scroll1': dict(kind='hf', tile=64, stride=16, windows=dict(primary=PROD27, alt=TRAIN26), **_TF_HF),
    'timesformer_large_scroll1_01122024': dict(kind='hf', tile=64, stride=16, windows=dict(primary=TRAIN26, alt=PROD27),
                                               **_TF_HF),
    'resnet50_7.9um_scroll1_frags': dict(kind='hf', tile=256, stride=64, windows=dict(primary=RESNET18),
                                         config_py='configuration_resnet3d', model_py='modeling_resnet3d',
                                         config_cls='Resnet3DScrollprizeConfig', model_cls='Resnet3DScrollprizeModel',
                                         scale=4),
}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def arr_sha(a):
    a = np.ascontiguousarray(a)
    return hashlib.sha256(a.tobytes() + str(a.dtype).encode() + str(a.shape).encode()).hexdigest()


def order_indices(offsets, order, surface=SURFACE, n=N_SLICES):
    idx = [surface + o for o in offsets] if order == 'forward' else [surface - o for o in offsets]
    assert all(0 <= i < n for i in idx), (order, idx)
    return idx


def load_render(path):
    if path.endswith('.npy'):
        a = np.load(path, mmap_mode='r')
    else:
        import zarr
        z = zarr.open(path, mode='r')
        a = z['0'] if hasattr(z, 'keys') and '0' in z else z
    a = np.asarray(a[:])
    assert a.ndim == 3 and a.shape[0] == N_SLICES, a.shape
    assert a.dtype == np.uint8, f'render dtype {a.dtype}: the official code clips uint8 at 200; refusing to convert'
    return a


class _TorchNoAutocast:
    """The torch module as seen by villa inference.py, with torch.autocast replaced by a no-op context."""

    def __init__(self, torch_mod):
        self._t = torch_mod

    def __getattr__(self, k):
        return getattr(self._t, k)

    @staticmethod
    def autocast(*args, **kw):
        return contextlib.nullcontext()


class HFModelWrapper:
    """InferenceModel protocol (villa inference.py) around an HF repo model class."""

    def __init__(self, model, scale):
        self.model, self.scale = model, scale

    def forward(self, x):
        return self.model(x)

    def get_output_scale_factor(self):
        return self.scale

    def eval(self):
        self.model.eval()

    def to(self, device):
        self.model.to(device)


def build_model(name, weights, device, n_frames):
    import torch
    spec = SPECS[name]
    info = dict(weights=weights, weights_sha256=sha256(weights))
    if spec['kind'] == 'pl_timesformer':
        import model_timesformer as MT  # villa, unchanged
        ck = torch.load(weights, map_location='cpu', weights_only=False)
        ref = MT.RegressionPLModel(pred_shape=(1, 1), num_frames=n_frames).state_dict()
        sd = ck['state_dict']
        info.update(hyper_parameters={k: str(v) for k, v in ck.get('hyper_parameters', {}).items()},
                    epoch=ck.get('epoch'), global_step=ck.get('global_step'),
                    missing_keys=sorted(set(ref) - set(sd)), unexpected_keys=sorted(set(sd) - set(ref)),
                    shape_mismatch=sorted(k for k in set(ref) & set(sd) if ref[k].shape != sd[k].shape),
                    loader='villa model_timesformer.load_model')
        del ck, sd
        model = MT.load_model(weights, device, num_frames=n_frames)
    else:
        from safetensors.torch import load_file
        card = os.path.join(CARDS, name)
        pkg = 'hfrepo_' + hashlib.sha1(name.encode()).hexdigest()[:10]
        if pkg not in sys.modules:
            m = types.ModuleType(pkg)
            m.__path__ = [card]
            sys.modules[pkg] = m
        cfg_mod = importlib.import_module(f'{pkg}.{spec["config_py"]}')
        mdl_mod = importlib.import_module(f'{pkg}.{spec["model_py"]}')
        cj = json.load(open(os.path.join(card, 'config.json')))
        cfg = getattr(cfg_mod, spec['config_cls'])(**{k: v for k, v in cj.items() if k not in (
            'architectures', 'auto_map', 'torch_dtype', 'transformers_version', 'model_type')})
        net = getattr(mdl_mod, spec['model_cls'])(cfg)
        sd = load_file(weights)
        ref = net.state_dict()
        info.update(code_sha256={f: sha256(os.path.join(card, f)) for f in sorted(os.listdir(card))
                                 if f.endswith(('.py', '.json', '.md'))},
                    missing_keys=sorted(set(ref) - set(sd)), unexpected_keys=sorted(set(sd) - set(ref)),
                    shape_mismatch=sorted(k for k in set(ref) & set(sd) if ref[k].shape != sd[k].shape),
                    loader='HF repo model class + safetensors strict load')
        net.load_state_dict(sd, strict=True)
        del sd
        net.to(device).eval()
        model = HFModelWrapper(net, spec['scale'])
    info['n_params'] = int(sum(p.numel() for p in (model.model.parameters())))
    return model, info


def run_order(layers_hwc, model, device, spec, workdir):
    import inference as INF  # villa, unchanged
    import processing as PR  # villa, unchanged
    INF.CFG.in_chans = layers_hwc.shape[2]
    INF.CFG.tile_size = spec['tile']
    INF.CFG.size = spec['tile']
    INF.CFG.stride = spec['stride']
    INF.CFG.workers = 0
    INF.CFG.num_parts, INF.CFG.part_id = 1, 0
    INF.CFG.zarr_output_dir = workdir
    INF.CFG.use_zarr_compression = False
    res = INF.run_inference(layers_hwc, model, device, fragment_mask=None, is_reverse_segment=False)
    shutil.rmtree(PARTITION_CACHE, ignore_errors=True)  # the villa cache is never overwritten: clear it every run
    gen, (H, W) = PR.reduce_partitions(workdir, 1, layers_hwc.shape[:2], 1024)
    out = np.zeros((H, W), np.uint8)
    for y in range(0, H, 1024):
        for x in range(0, W, 1024):
            t = next(gen)
            out[y:y + t.shape[0], x:x + t.shape[1]] = t
    shutil.rmtree(PARTITION_CACHE, ignore_errors=True)
    return out, dict(partition_batches=int(res.get('partition_batches', 0)),
                     partition_tiles=int(res.get('partition_tiles', 0)))


def map_stats(m, valid):
    v = m[valid] if valid is not None and valid.any() else m.ravel()
    return dict(mean=round(float(v.mean()), 4), std=round(float(v.std()), 4),
                frac_ge128=round(float((v >= 128).mean()), 6), frac_eq0=round(float((v == 0).mean()), 6),
                frac_eq255=round(float((v == 255).mean()), 6), n=int(v.size))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ckpt', required=True, choices=sorted(SPECS))
    ap.add_argument('--weights', required=True)
    ap.add_argument('--render', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--precision', choices=['fp32', 'official'], default='fp32')
    ap.add_argument('--orders', nargs='+', default=['forward', 'reverse'], choices=['forward', 'reverse'])
    ap.add_argument('--batch-size', type=int, default=32)
    ap.add_argument('--window', choices=['primary', 'alt'], default='primary')
    a = ap.parse_args()

    for k in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
        os.environ[k] = str(a.threads)
    villa_head = subprocess.run(['git', '-C', VILLA, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    assert villa_head == VILLA_SHA, f'villa at {villa_head}, expected {VILLA_SHA}'
    dirty = subprocess.run(['git', '-C', VILLA, 'status', '--porcelain', '--', 'ink-detection/optimized_inference'],
                           capture_output=True, text=True).stdout.strip()
    assert not dirty, 'villa optimized_inference has local modifications'
    sys.path.insert(0, OI)
    import torch
    torch.set_num_threads(a.threads)
    import inference as INF
    if a.precision == 'fp32':
        INF.torch = _TorchNoAutocast(torch)  # autocast off inside villa inference.py only; nothing else changes
    INF.CFG.batch_size = a.batch_size

    lockf = open(LOCK, 'w')
    fcntl.flock(lockf, fcntl.LOCK_EX)
    spec = SPECS[a.ckpt]
    offsets = spec['windows'][a.window]
    device = torch.device('cpu')
    rec = dict(provenance=PROV, utc_start=utc(), ckpt=a.ckpt, spec={k: v for k, v in spec.items() if k != 'windows'},
               window=a.window, offsets=offsets, precision=a.precision, threads=a.threads, batch_size=a.batch_size,
               torch=torch.__version__, villa_sha=villa_head, wrapper_sha256=sha256(os.path.abspath(__file__)),
               render=a.render, surface_index=SURFACE)
    t0 = time.time()
    model, rec['model'] = build_model(a.ckpt, a.weights, device, len(offsets))
    rec['model_load_s'] = round(time.time() - t0, 2)
    render = load_render(a.render)
    rec['render_shape'] = list(render.shape)
    valid = np.any(render != 0, axis=0)
    rec['render_valid_frac'] = round(float(valid.mean()), 6)
    base = a.out[:-4] if a.out.endswith('.tif') else a.out
    import tifffile
    rec['orders'] = {}
    for order in a.orders:
        idx = order_indices(offsets, order)
        layers = np.ascontiguousarray(np.transpose(render[idx], (1, 2, 0)))  # (H, W, C) as villa LayersSource expects
        wd = tempfile.mkdtemp(prefix=f'ckscr_{order}_', dir=os.environ.get('CKSCR_TMP', '/tmp'))
        t1 = time.time()
        m, info = run_order(layers, model, device, spec, wd)
        secs = time.time() - t1
        shutil.rmtree(wd, ignore_errors=True)
        path = f'{base}.tif' if order == 'forward' else f'{base}_reverse.tif'
        tifffile.imwrite(path, m)
        rec['orders'][order] = dict(indices=idx, seconds=round(secs, 2), path=path, sha256=sha256(path),
                                    array_sha256=arr_sha(m), shape=list(m.shape), dtype=str(m.dtype),
                                    stats_valid=map_stats(m, valid), **info)
    rec['utc_end'] = utc()
    rec['seconds_total'] = round(time.time() - t0, 2)
    with open(f'{base}.run.json', 'w') as f:
        t = json.dumps(rec, indent=1, default=str) + '\n'
        assert t.isascii()
        f.write(t)
    print(json.dumps({k: rec[k] for k in ('ckpt', 'precision', 'seconds_total')}))
    for o, r in rec['orders'].items():
        print(o, r['seconds'], r['sha256'], json.dumps(r['stats_valid']))


if __name__ == '__main__':
    main()
