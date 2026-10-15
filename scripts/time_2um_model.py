#!/usr/bin/env python
"""CONTROL-2UM feasibility on this box: load the team's 2.4 um checkpoint with villa's loader and time a CPU forward
pass on one 62x256x256 tile (batch 1 and 4). Projection: a 5 cm^2 patch at 2.403 um is ~9441^2 px; with tile 256
stride 128 that is ~5400 tiles per depth order. Nothing here touches real data."""
import os, sys, time, json, torch
sys.path.insert(0, os.path.join(os.environ.get("VILLA", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "external", "villa")), "ink-detection", "optimized_inference"))
import model_resnet3d_3d_decoder as M
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA
ck = DATA + "/models/ink_canonical_2um/r152_3ddec_v2_l5_epoch13.ckpt"
t0 = time.time(); w = M.load_model(ck, torch.device("cpu"), num_frames=62); t_load = time.time() - t0
n_par = sum(p.numel() for p in w.model.parameters())
out = {"load_s": round(t_load, 1), "params_M": round(n_par / 1e6, 1), "threads": torch.get_num_threads()}
with torch.no_grad():
    for bs in (1, 4):
        x = torch.rand(bs, 1, 62, 256, 256)
        w.forward(x)  # warm-up
        t0 = time.time(); y = w.forward(x); dt = time.time() - t0
        out[f"bs{bs}_s_per_tile"] = round(dt / bs, 2); out["out_shape"] = list(y.shape)
tiles = (9441 // 128) ** 2
out["tiles_per_order_5cm2"] = tiles
out["hours_per_order_5cm2_at_bs4"] = round(tiles * out["bs4_s_per_tile"] / 3600, 1)
print(json.dumps(out, indent=1))
