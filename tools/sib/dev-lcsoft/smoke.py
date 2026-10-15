# Provenance: Project HERCULES | owner the owner | [id removed]
"""Phase-1 SYNTHETIC smoke of LC384-SOFT and its NULL and REV controls (task dev-lcsoft). No real data is read.

Fake pairs0139-format pool: random uint8 image stacks, a random smooth 'inkmap', labels derived from it with the
build_pairs thresholds (>= 150 ink, <= 100 blank, else 255), a render-invalid corner on some tiles, and registry rows
with valid24_frac 1.0 or < 1.0. Then: lc_cache (forward + reverse, fp16 as the recipe default), soft_targets, and
20 training steps each of RECIPE, NULL and REV with --targets soft at 4 threads fp32. Also: soft_targets consistency
checks, NULL derangement, a bitwise resume check (10 + 10 steps vs 20), and per-step / per-encode timing.
Writes one JSON summary (numbers only)."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lc_cache  # noqa: E402
import lc_train  # noqa: E402
import soft_targets  # noqa: E402


def fake_pool(root, n_seg=3, grid=5, seed=7):
    rng = np.random.default_rng(seed)
    os.makedirs(f"{root}/shards", exist_ok=True); os.makedirs(f"{root}/registry", exist_ok=True)
    pos = [(f"S{s}", 128 * r, 128 * c) for s in range(n_seg) for r in range(grid) for c in range(grid)]
    N = len(pos)
    imgs = rng.integers(1, 255, (N, 21, 128, 128), dtype=np.uint8)
    # smooth random ink field in [0, 255]
    base = rng.random((N, 16, 16)).astype(np.float32)
    im = np.kron(base, np.ones((8, 8), np.float32)) * 255.0
    inkmap = np.clip(np.round(im), 0, 255).astype(np.uint8)
    lab = np.full((N, 128, 128), 255, np.uint8)
    lab[inkmap >= 150] = 1; lab[inkmap <= 100] = 0
    v24 = np.ones(N, float)
    for i in range(0, N, 4):  # every 4th tile: render-invalid 16 x 16 corner -> label 255, surface 0
        imgs[i, :, :16, :16] = 0; lab[i, :16, :16] = 255
    for i in range(1, N, 5):  # every 5th tile (offset 1): partial 2.4 um validity
        v24[i] = 0.97
    np.savez_compressed(f"{root}/shards/X_s00.npz", images=imgs, label=lab, inkmap=inkmap, human=np.full_like(lab, 255))
    with open(f"{root}/registry/X.jsonl", "w") as f:
        for i, (s, y, x) in enumerate(pos):
            f.write(json.dumps(dict(tile_id=f"t{i}", segment=s, canvas9_y0=y, canvas9_x0=x, shard="X_s00.npz",
                                    shard_index=i, valid24_frac=v24[i])) + "\n")
    json.dump([f"t{i}" for i in range(N)], open(f"{root}/allow.json", "w"))
    return N


def state_of(out):
    ck = torch.load(f"{out}/lc_final.pt", map_location="cpu", weights_only=False)
    return ck["lc_state"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--out-json", required=True)
    a = ap.parse_args(argv)
    torch.set_num_threads(a.threads)
    R = a.root
    rep = dict(provenance="Project HERCULES | owner the owner | [id removed]", synthetic=True, threads=a.threads,
               steps=a.steps, torch=torch.__version__, torch_threads=torch.get_num_threads())
    rep["n_tiles"] = fake_pool(R)
    for order in ("forward", "reverse"):
        t0 = time.time()
        lc_cache.main(["--shards", f"{R}/shards", "--registry", f"{R}/registry", "--allow", f"{R}/allow.json",
                       "--out", f"{R}/cache_{order}", "--order", order, "--dtype", "fp16", "--threads", str(a.threads)])
        rep[f"cache_{order}_s"] = round(time.time() - t0, 2)
        soft_targets.main(["--cache", f"{R}/cache_{order}", "--shards", f"{R}/shards", "--registry", f"{R}/registry"])
        rep[f"soft_{order}"] = json.load(open(f"{R}/cache_{order}/soft/manifest.json"))["counts"]
    rep["encode_s_per_tile"] = round(rep["cache_forward_s"] / rep["n_tiles"], 4)
    # soft target consistency: identical targets for both orders (labels never reversed)
    rep["soft_targets_equal_across_orders"] = bool(
        np.array_equal(np.load(f"{R}/cache_forward/soft/inkmap.npy"), np.load(f"{R}/cache_reverse/soft/inkmap.npy"))
        and np.array_equal(np.load(f"{R}/cache_forward/soft/sup.npy"), np.load(f"{R}/cache_reverse/soft/sup.npy")))
    # inconsistency is rejected
    try:
        bad = np.full((128, 128), 1, np.uint8); soft_targets.tile_sup(bad, np.zeros_like(bad), np.ones_like(bad), True)
        rep["rejects_threshold_inconsistency"] = False
    except ValueError:
        rep["rejects_threshold_inconsistency"] = True
    p = lc_train.derangement(rep["n_tiles"])
    rep["null_fixed_points"] = int(np.sum(p == np.arange(len(p))))
    arms = dict(RECIPE=f"{R}/cache_forward", NULL=f"{R}/cache_forward", REV=f"{R}/cache_reverse")
    rep["arms"] = {}
    for arm, cache in arms.items():
        out = f"{R}/run_{arm}"
        t0 = time.time()
        rc = lc_train.main(["--cache", cache, "--arm", arm, "--out", out, "--steps", str(a.steps), "--targets", "soft",
                            "--threads", str(a.threads), "--log-every", "5", "--val-every", "10", "--ckpt-every", "10"])
        s = json.load(open(f"{out}/summary.json"))
        log = [json.loads(l) for l in open(f"{out}/train_log.jsonl")]
        rep["arms"][arm] = dict(rc=rc, wall_s=round(time.time() - t0, 1), median_s_per_step=s["median_s_per_step"],
                                loss_first=log[0]["loss"], loss_last=log[-1]["loss"],
                                losses_finite=bool(all(np.isfinite(r["loss"]) for r in log)),
                                val_loss=[r.get("val_loss") for r in log if "val_loss" in r],
                                neighbours_present_frac_last=log[-1]["neighbours_present_frac"],
                                targets=s["targets"], null_fixed_points=s["null_fixed_points"], n_train=s["n_train"],
                                n_val=s["n_val"], final_bytes=s["final_bytes"])
    # arms differ (NULL and REV are not the recipe)
    sr, sn, sv = state_of(f"{R}/run_RECIPE"), state_of(f"{R}/run_NULL"), state_of(f"{R}/run_REV")
    rep["null_differs_from_recipe"] = any(not torch.equal(sr[k], sn[k]) for k in sr)
    rep["rev_differs_from_recipe"] = any(not torch.equal(sr[k], sv[k]) for k in sr)
    # bitwise resume: RECIPE 10 steps, die, resume to 20 == uninterrupted 20
    out = f"{R}/run_RECIPE_resume"
    rc1 = lc_train.main(["--cache", arms["RECIPE"], "--arm", "RECIPE", "--out", out, "--steps", str(a.steps), "--targets",
                         "soft", "--threads", str(a.threads), "--ckpt-every", "10", "--die-after", "10"])
    rc2 = lc_train.main(["--cache", arms["RECIPE"], "--arm", "RECIPE", "--out", out, "--steps", str(a.steps), "--targets",
                         "soft", "--threads", str(a.threads), "--ckpt-every", "10"])
    s2 = state_of(out)
    rep["resume"] = dict(rc_die=rc1, rc_resume=rc2, bitwise_equal=all(torch.equal(sr[k], s2[k]) for k in sr),
                         max_abs_diff=float(max((sr[k].float() - s2[k].float()).abs().max() for k in sr)))
    # hard-target default is still the unchanged path (runs, finite)
    rc = lc_train.main(["--cache", arms["RECIPE"], "--arm", "RECIPE", "--out", f"{R}/run_HARD", "--steps", "5",
                        "--threads", str(a.threads)])
    rep["hard_default"] = dict(rc=rc, targets=json.load(open(f"{R}/run_HARD/summary.json"))["targets"])
    json.dump(rep, open(a.out_json, "w"), indent=1)
    print(json.dumps(rep["arms"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
