# Provenance: Project HERCULES | owner the owner | [id removed]
"""COST-ONLY bench (task dev-lcsoft), synthetic random input, no training, no data. NOT part of any recipe.

The orchestrator's task text describes LC384-SOFT as 'encoder unfrozen / soft', while first_recipes.md recipe 2 (the
declared protocol) is 'recipe 1 with soft-teacher targets' with the encoder frozen. This bench prices the undeclared
reading so the orchestrator can decide: one LC384 'basedec' step at batch 8 with the base 3-D stem + 2-D encoder
TRAINABLE on the 8 centre tiles (forward + backward) and the 64 neighbour tiles encoded without grad (their level-4/5
skips feed the context block), against the frozen cached-feature step. fp32, --threads threads."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lc_model as LM  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--steps", type=int, default=3)
    ap.add_argument("--out-json", required=True)
    a = ap.parse_args(argv)
    torch.set_num_threads(a.threads)
    torch.manual_seed(0)
    model, _, _ = LM.build("basedec")
    for p in list(model.base_stem.parameters()) + list(model.base_encoder.parameters()):
        p.requires_grad_(True)
    model.train()
    model.base_stem.train(); model.base_encoder.train()
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=1e-5)
    B = 8
    walls, parts = [], []
    for s in range(a.steps + 1):
        xc = torch.randn(B, 1, 17, 128, 128)
        xn = torch.randn(B * 8, 1, 17, 128, 128)
        t0 = time.perf_counter()
        with torch.no_grad():
            skn = [model.base_encoder(model.base_stem(xn[i:i + 8])) for i in range(0, B * 8, 8)]
        t1 = time.perf_counter()
        skc = model.base_encoder(model.base_stem(xc))
        n4 = torch.cat([k[4] for k in skn]).view(B, 8, 320, 8, 8)
        n5 = torch.cat([k[5] for k in skn]).view(B, 8, 320, 4, 4)
        n4 = torch.cat([n4[:, :4], skc[4][:, None], n4[:, 4:]], 1)
        n5 = torch.cat([n5[:, :4], skc[5][:, None], n5[:, 4:]], 1)
        logits = model(skc, n4, n5, torch.ones(B, 9, dtype=torch.bool))
        loss = torch.nn.functional.binary_cross_entropy_with_logits(logits, torch.rand_like(logits))
        loss.backward()
        opt.step(); opt.zero_grad(set_to_none=True)
        t2 = time.perf_counter()
        if s > 0:  # first step is warm-up
            walls.append(t2 - t0); parts.append(dict(neighbour_encode_s=t1 - t0, centre_fwd_bwd_step_s=t2 - t1))
    n_enc = sum(p.numel() for p in list(model.base_stem.parameters()) + list(model.base_encoder.parameters()))
    rep = dict(provenance="Project HERCULES | owner the owner | [id removed]", undeclared_cost_only=True,
               threads=a.threads, batch=B, steps_timed=a.steps, s_per_step=walls, parts=parts,
               median_s_per_step=sorted(walls)[len(walls) // 2], encoder_params=n_enc,
               trainable_params=sum(p.numel() for p in params), hours_per_2000_steps=sorted(walls)[len(walls) // 2] * 2000 / 3600)
    json.dump(rep, open(a.out_json, "w"), indent=1)
    print(json.dumps(rep))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
