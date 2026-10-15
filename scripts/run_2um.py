#!/usr/bin/env python
"""Run the team's 2.4 um ink model (scrollprize/ink_canonical_2um, ResNet-152 3D + 3D decoder) through villa's
optimized_inference entrypoint on a LOCAL surface-volume zarr, both depth orders, CPU (MASTER_PROMPT_v4 section 7).
The weight resolver is wrapped to the local checkpoint. Outputs per order: <out>/<tag>_{forward,reverse}.tif = pred/count
(count > 0) as uint8 p*255, plus the raw pred/count zarrs. Idempotent per order (marker files).
usage: run_2um.py <surface.zarr> <out_dir> --tag w028calib --start 23 --end 85 --um 2.399 [--orders forward reverse]
       [--tile 256 --stride 128 --batch 4]
Layer window: for the team's 109-layer volumes the centred window is 23..85 (villa issue #1813); for our own 64-slice
renders use 1..63.
"""
import argparse, os, sys, json, time
import numpy as np
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

VILLA = os.path.join(os.environ.get("VILLA", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "external", "villa")), "ink-detection", "optimized_inference")
CKPT = DATA + "/models/ink_canonical_2um/r152_3ddec_v2_l5_epoch13.ckpt"

def run_order(a, order):
    marker = os.path.join(a.out, f".complete_{order}")
    if os.path.exists(marker):
        print("skip", order); return
    parts = os.path.join(a.out, f"parts_{order}")
    os.makedirs(parts, exist_ok=True)
    env = dict(MODEL="scrollprize/ink_canonical_2um", MODEL_TYPE="resnet3d-152-3d-decoder", STEP="inference",
               SURFACE_VOLUME_ZARR=a.zarr, START_LAYER=str(a.start), END_LAYER=str(a.end), TILE_SIZE=str(a.tile),
               STRIDE=str(a.stride), BATCH_SIZE=str(a.batch), PREFETCH_FACTOR="1", COMPILE="0",
               PIXEL_RESOLUTION_UM=str(a.um), SEGMENT_ID=a.tag, OUTPUT_PATH=os.path.join(a.out, f"{a.tag}_{order}_raw.png"),
               ZARR_OUTPUT_DIR=parts, PROFILING_LEVEL="none", FORCE_REVERSE="true" if order == "reverse" else "false",
               CUDA_VISIBLE_DEVICES="", NUM_WORKERS=str(a.workers), S3_PATH="local://" + a.zarr, USE_ZARR_COMPRESSION="false")
    os.environ.update(env)
    sys.path.insert(0, VILLA); os.chdir(VILLA)
    import importlib, entrypoint
    importlib.reload(entrypoint)
    entrypoint.download_model_weights = lambda *args, **kw: CKPT
    if hasattr(entrypoint, "upload_prediction_to_s3"):
        entrypoint.upload_prediction_to_s3 = lambda *args, **kw: None
    t0 = time.time()
    try:
        entrypoint.main()
    except SystemExit as e:
        if e.code not in (0, None): raise
    dt = time.time() - t0
    import zarr, tifffile
    pred = zarr.open(os.path.join(parts, "mask_pred_part_000.zarr"), mode="r")[:]
    cnt = zarr.open(os.path.join(parts, "mask_count_part_000.zarr"), mode="r")[:]
    m = np.zeros(pred.shape, np.float32); ok = cnt > 0; m[ok] = pred[ok] / cnt[ok]
    u8 = np.clip(np.rint(m * 255), 0, 255).astype(np.uint8)
    tifffile.imwrite(os.path.join(a.out, f"{a.tag}_{order}.tif"), u8)
    json.dump(dict(order=order, seconds=round(dt), shape=list(u8.shape), mean=float(m[ok].mean()) if ok.any() else None,
                   frac_gt_05=float((m[ok] > 0.5).mean()) if ok.any() else None, start=a.start, end=a.end, tile=a.tile, stride=a.stride,
                   checkpoint=CKPT, zarr=a.zarr), open(os.path.join(a.out, f"{a.tag}_{order}.json"), "w"), indent=1)
    open(marker, "w").write("ok\n"); print(order, "done in %.0f s" % dt)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("zarr"); ap.add_argument("out"); ap.add_argument("--tag", required=True)
    ap.add_argument("--start", type=int, required=True); ap.add_argument("--end", type=int, required=True); ap.add_argument("--um", type=float, required=True)
    ap.add_argument("--orders", nargs="+", default=["forward", "reverse"]); ap.add_argument("--tile", type=int, default=256)
    ap.add_argument("--stride", type=int, default=128); ap.add_argument("--batch", type=int, default=4); ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args(); a.zarr = os.path.abspath(a.zarr); a.out = os.path.abspath(a.out); os.makedirs(a.out, exist_ok=True)
    for order in a.orders:
        run_order(a, order)

if __name__ == "__main__":
    main()
