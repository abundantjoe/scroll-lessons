# Provenance: Project HERCULES | owner the owner | [id removed]
"""LC384 map producer with the official flat-inference output contract (task devloop-r1). Numbers only.

Mirrors vesuvius.ink_detection.inference.infer.infer_single_zarr (villa 41701aa) and REUSES its components unchanged:
open_volume_root / select_volume_level, _volume_axes, select_layer_indices (centre 17 layers; reversed for the
reverse order), FlatPatchReader (padded read), normalize_flat_patch (tifxyz_robust per patch), build_lowres_block_mask
+ iter_blocks (stride 64 = overlap 0.5, boundary-aligned last position, occupancy skipping), the nonempty skip,
compute_importance_map_2d ('hann' for stride < patch), ChunkAccumulator, logits_to_probabilities (sigmoid in fp32),
write_output_tiff (clip, * 255, truncate to uint8; LZW tiled BigTIFF). Output files: <out>.tif and
<out>_reverse.tif for --direction both, as the official CLI.
The only change is the forward: each block's encoder skips (frozen base) are combined with the level-4/5 skips of
the patches whose origins lie at +-128 px (read with the same reader, normalised the same way; a neighbour is
'missing' when its origin window lies entirely outside the image or its raw patch is all zero). Encoder outputs
are cached per origin and evicted once no later block can use them; with --feature-dtype fp16/bf16 every skip is rounded
through that dtype exactly as in the training cache (lc_cache.py). Batch = --batch-size blocks in official order
(InstanceNorm is per sample, so batching does not change results).
Usage: python lc_infer.py IN.zarr LC_CKPT.pt OUT.tif [--direction both] [--batch-size 4] [--threads 4]
       [--base-identity]  (no checkpoint: a zero-initialised LC384 'basedec', i.e. the base model; for tests)"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lc_model as LM  # noqa: E402
from vesuvius.ink_detection.inference import infer as OI  # noqa: E402
from vesuvius.ink_detection.volume_io import open_volume_root, select_volume_level  # noqa: E402

PATCH, STRIDE, CTX = 128, 64, 128


def cast_skips(skips, feature_dtype):
    if feature_dtype in ("bf16", "fp16"):
        dt = torch.bfloat16 if feature_dtype == "bf16" else torch.float16
        return [s.to(dt).float() for s in skips]
    return skips


class FeatureCache:
    """Encoder skips per patch origin (y0, x0); None marks a missing patch."""

    def __init__(self, model, reader, preprocessing, height, width, feature_dtype):
        self.model, self.reader, self.pre = model, reader, preprocessing
        self.h, self.w, self.fd = height, width, feature_dtype
        self.store = {}
        self.encodes = 0

    def _read(self, y0, x0):
        if y0 + PATCH <= 0 or x0 + PATCH <= 0 or y0 >= self.h or x0 >= self.w:
            return None
        p = self.reader.read(y0, x0, PATCH, PATCH)
        if not p.any():
            return None
        zyx = OI.normalize_flat_patch(np.moveaxis(p, -1, 0), self.pre)
        return torch.from_numpy(zyx).unsqueeze(0)

    def ensure(self, keys):
        todo = [k for k in dict.fromkeys(keys) if k not in self.store]
        xs, ks = [], []
        for k in todo:
            x = self._read(*k)
            if x is None:
                self.store[k] = None
            else:
                xs.append(x); ks.append(k)
        for i in range(0, len(xs), 8):
            sk = cast_skips(self.model.encode(torch.stack(xs[i:i + 8])), self.fd)
            self.encodes += len(xs[i:i + 8])
            for j, k in enumerate(ks[i:i + 8]):
                self.store[k] = [s[j] for s in sk]

    def evict_above(self, y_min):
        for k in [k for k in self.store if k[0] < y_min]:
            del self.store[k]


def run_order(model, input_zarr, out_tif, direction, batch_size, feature_dtype, log):
    root = open_volume_root(input_zarr)
    volume = select_volume_level(root, "0", source=str(input_zarr))
    depth_first, depth, height, width, chunk_h, chunk_w = OI._volume_axes(volume)
    layer_indices = OI.select_layer_indices(depth, layer_start=None, layer_end=None, output_depth=17, direction=direction)
    preprocessing = "tifxyz_robust"
    tile_shape = (PATCH, PATCH)
    reader = OI.FlatPatchReader(input_path=input_zarr, resolution="0", depth_axis_first=depth_first, height=height,
                                width=width, layer_indices=layer_indices, output_depth=17, preprocessing=preprocessing)
    occupancy, occ_scale, _ = OI.build_lowres_block_mask(root, height=height, width=width, user_mask=None)
    blocks = OI.iter_blocks((height, width), PATCH, STRIDE, occupancy, occ_scale)
    weight_map = OI.compute_importance_map_2d(patch_size=(PATCH, PATCH), mode="hann").numpy()
    fc = FeatureCache(model, reader, preprocessing, height, width, feature_dtype)
    tmp = Path(tempfile.mkdtemp(prefix="lc_infer_", dir=os.environ.get("LC_TMP", None)))
    t0 = time.time()
    try:
        chunks = (min(tile_shape[0], height), min(tile_shape[1], width))
        ps = OI.open_temp_zarr_array(tmp / "p.zarr", shape=(height, width), chunks=chunks)
        ws = OI.open_temp_zarr_array(tmp / "w.zarr", shape=(height, width), chunks=chunks)
        acc = OI.ChunkAccumulator(shape=(height, width), chunk_shape=chunks, prob_sum_store=ps, weight_sum_store=ws,
                                  contribution_counts=OI.compute_chunk_contribution_counts(blocks, chunk_shape=chunks))
        n_missing = 0
        with torch.inference_mode():
            for i in range(0, len(blocks), batch_size):
                bb = blocks[i:i + batch_size]
                keys = [(b.y0 + dy * CTX, b.x0 + dx * CTX) for b in bb for dy, dx in LM.OFFSETS]
                fc.ensure(keys)
                live = [b for b in bb if fc.store[(b.y0, b.x0)] is not None]  # official: skip raw-empty patches
                if live:
                    cen = [torch.stack([fc.store[(b.y0, b.x0)][l] for b in live]) for l in range(6)]
                    n4, n5, pres = [], [], []
                    for b in live:
                        row4, row5, rowp = [], [], []
                        for dy, dx in LM.OFFSETS:
                            f = fc.store[(b.y0 + dy * CTX, b.x0 + dx * CTX)]
                            rowp.append(f is not None)
                            row4.append(f[4] if f is not None else torch.zeros_like(cen[4][0]))
                            row5.append(f[5] if f is not None else torch.zeros_like(cen[5][0]))
                        n4.append(torch.stack(row4)); n5.append(torch.stack(row5)); pres.append(rowp)
                        n_missing += 9 - sum(rowp)
                    logits = model(cen, torch.stack(n4), torch.stack(n5), torch.tensor(pres))
                    probs = OI.logits_to_probabilities(logits, image_hw=(PATCH, PATCH)).cpu().numpy()[:, 0]
                    for p, b in zip(probs, live):
                        acc.add_tile(y0=b.y0, x0=b.x0, tile=p[:b.valid_h, :b.valid_w], tile_weights=weight_map[:b.valid_h, :b.valid_w])
                nxt = blocks[i + batch_size].y0 if i + batch_size < len(blocks) else height
                fc.evict_above(nxt - CTX)
        acc.flush_remaining()
        OI.write_output_tiff(ps, ws, Path(out_tif), tile_shape)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    rec = dict(direction=direction, out=str(out_tif), blocks=len(blocks), encodes=fc.encodes,
               encodes_per_block=fc.encodes / max(1, len(blocks)), missing_neighbour_slots=n_missing,
               layer_indices=[int(v) for v in layer_indices], seconds=round(time.time() - t0, 1))
    log.append(rec)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("input_zarr")
    ap.add_argument("ckpt")
    ap.add_argument("output_tiff")
    ap.add_argument("--direction", default="both", choices=("forward", "reverse", "both"))
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--threads", type=int, default=int(os.environ.get("OMP_NUM_THREADS", "4")))
    ap.add_argument("--feature-dtype", choices=("fp32", "fp16", "bf16"), default=None, help="default: from the checkpoint")
    ap.add_argument("--base-identity", action="store_true")
    ap.add_argument("--record", help="write a JSON record here")
    a = ap.parse_args(argv)
    torch.set_num_threads(a.threads)
    if a.base_identity:
        model, _, _ = LM.build("basedec")
        model.eval()
        meta = dict(variant="basedec", identity=True)
        fd = a.feature_dtype or "fp32"
    else:
        model, ck, _, _ = LM.load_ckpt(a.ckpt)
        meta = dict(variant=ck["variant"], meta=ck.get("meta"))
        fd = a.feature_dtype or ck.get("meta", {}).get("feature_dtype", "fp32")
    out = Path(a.output_tiff)
    runs = ("forward", "reverse") if a.direction == "both" else (a.direction,)
    log = []
    for d in runs:
        path = out if (d == "forward" or a.direction != "both") else out.with_name(out.stem + "_reverse" + out.suffix)
        run_order(model, a.input_zarr, path, d, a.batch_size, fd, log)
    if a.record:
        json.dump(dict(model=meta, feature_dtype=fd, threads=a.threads, runs=log), open(a.record, "w"), indent=1)
    print(json.dumps(log))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
