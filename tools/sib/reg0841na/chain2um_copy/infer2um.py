# Provenance: Project HERCULES | owner the owner | [id removed]
"""CPU driver for the official ink_canonical_2um chain (villa ink-detection/optimized_inference @ 41701aa).

Uses the official modules unchanged: inference.run_inference (tiling, clip 0..200, /200, reverse = tile[:, :, ::-1]
after the [start, end) layer slice, Hann overlap-add, all-empty-batch skip) and model_resnet3d_3d_decoder.load_model.
The official predict_fn always wraps the forward in torch.autocast(device_type="cpu", enabled=True), i.e. bf16 on CPU.
--precision fp32 nests torch.autocast("cpu", enabled=False) inside the model wrapper, which disables it.

Resumable: the tile list is split into --parts official partitions (CFG.num_parts / CFG.part_id); a finished part leaves
mask_pred/mask_count zarrs plus a done-json and is skipped on restart. The final map is the official reduce formula:
sum(pred) / clip(sum(count), 1e-6), clip 0..1; saved as float32 npz and as the official uint8 (x255, truncation).
Numbers only: nothing is displayed.
"""
import argparse, json, os, sys, time, hashlib, resource
import numpy as np

VILLA_OI = '/work/villa/ink-detection/optimized_inference'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--render', required=True, help='render zarr (group with array 0, shape (Z,H,W))')
    ap.add_argument('--ckpt', required=True)
    ap.add_argument('--out', required=True, help='output directory for this pass')
    ap.add_argument('--direction', choices=['reverse', 'forward'], required=True)
    ap.add_argument('--precision', choices=['bf16', 'fp32'], required=True)
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--layers', type=int, default=62)
    ap.add_argument('--tile', type=int, default=256)
    ap.add_argument('--stride', type=int, default=128)
    ap.add_argument('--batch', type=int, default=1)
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--parts', type=int, default=10)
    ap.add_argument('--only-parts', type=str, default='', help='comma list: run only these parts (benchmarks)')
    a = ap.parse_args()

    import torch
    torch.set_num_threads(a.threads)
    sys.path.insert(0, VILLA_OI)
    import inference as oi
    from inference import CFG
    from model_resnet3d_3d_decoder import load_model
    import zarr

    os.makedirs(a.out, exist_ok=True)
    g = zarr.open(a.render, mode='r')
    arr = g['0'] if hasattr(g, 'keys') and '0' in g else g
    zyx = arr[:]  # (Z, H, W) uint8, small crop held in RAM
    assert zyx.dtype == np.uint8 and zyx.ndim == 3, (zyx.dtype, zyx.shape)
    layers = np.ascontiguousarray(np.transpose(zyx, (1, 2, 0)))  # official (H, W, C) array input
    del zyx

    CFG.in_chans = a.layers
    CFG.tile_size = a.tile
    CFG.size = a.tile
    CFG.stride = a.stride
    CFG.batch_size = a.batch
    CFG.workers = 0  # in-RAM array; worker processes would only compete for the 4 cores
    CFG.num_parts = a.parts
    CFG.use_zarr_compression = False

    t0 = time.time()
    model = load_model(a.ckpt, torch.device('cpu'), num_frames=a.layers)
    t_load = time.time() - t0
    fwd_times = []
    inner = model.model

    class Timed(torch.nn.Module):
        def __init__(self, m, fp32):
            super().__init__(); self.m = m; self.fp32 = fp32
        def forward(self, x):
            t = time.perf_counter()
            if self.fp32:
                with torch.autocast(device_type='cpu', enabled=False):
                    y = self.m(x.float())
            else:
                y = self.m(x)
            fwd_times.append((time.perf_counter() - t, int(x.shape[0])))
            return y
        def get_output_scale_factor(self):
            return self.m.get_output_scale_factor()
    model.model = Timed(inner, a.precision == 'fp32')

    only = {int(p) for p in a.only_parts.split(',') if p != ''}
    parts_log = []
    for p in range(a.parts):
        if only and p not in only:
            continue
        pdir = os.path.join(a.out, f'part{p:03d}')
        done = os.path.join(pdir, 'done.json')
        if os.path.exists(done):
            parts_log.append(json.load(open(done)) | {'resumed': True}); continue
        CFG.part_id = p
        CFG.zarr_output_dir = pdir
        n0 = len(fwd_times); t = time.time()
        res = oi.run_inference(layers, model, torch.device('cpu'), is_reverse_segment=(a.direction == 'reverse'),
                               start_z=a.start, end_z=a.start + a.layers)
        rec = dict(part=p, wall_s=time.time() - t, forward_calls=len(fwd_times) - n0,
                   forward_s=sum(x[0] for x in fwd_times[n0:]), tiles=sum(x[1] for x in fwd_times[n0:]),
                   partition_info=res.get('partition_info'), utc_end=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
        json.dump(rec, open(done, 'w'))
        parts_log.append(rec)
        print(json.dumps(rec), flush=True)

    summary = dict(args=vars(a), torch=torch.__version__, threads=torch.get_num_threads(), model_load_s=t_load,
                   parts=parts_log, peak_rss_gb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6)
    if not only:
        H, W, _ = layers.shape
        pred = np.zeros((H, W), np.float32); cnt = np.zeros((H, W), np.float32)
        for p in range(a.parts):
            pdir = os.path.join(a.out, f'part{p:03d}')
            pred += zarr.open(os.path.join(pdir, f'mask_pred_part_{p:03d}.zarr'), mode='r')[:]
            cnt += zarr.open(os.path.join(pdir, f'mask_count_part_{p:03d}.zarr'), mode='r')[:]
        m = np.clip(pred / np.clip(cnt, 1e-6, None), 0, 1).astype(np.float32)
        u8 = (m * 255).astype(np.uint8)
        np.savez_compressed(os.path.join(a.out, 'map.npz'), map=m, u8=u8, count=cnt)
        tiles = sum(r['tiles'] for r in parts_log)
        fwd = sum(r['forward_s'] for r in parts_log)
        wall = sum(r['wall_s'] for r in parts_log)
        summary |= dict(tiles=tiles, forward_s=fwd, wall_s=wall, s_per_tile_forward=fwd / max(tiles, 1),
                        s_per_tile_wall=wall / max(tiles, 1),
                        map_sha256=hashlib.sha256(u8.tobytes()).hexdigest(), map_shape=[H, W])
    json.dump(summary, open(os.path.join(a.out, 'summary.json' if not only else 'bench.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != 'parts'}), flush=True)


if __name__ == '__main__':
    main()
