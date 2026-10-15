#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""Check the card's claim that model.safetensors is bit-identical to last.ckpt["state_dict"].
Downloads last.ckpt (sha256-verified via fetch.py), loads it with torch.load(weights_only=True) only
(a refusal is recorded, never worked around), compares every tensor, then deletes last.ckpt."""
import json, os, sys, time
import torch
from safetensors.torch import load_file
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch
for it in [int(a) for a in sys.argv[1:]]:
    rec = fetch.fetch(it, "last.ckpt")
    out = {"iteration": it, "check": "last.ckpt vs model.safetensors", "sha256_last_ckpt": rec.get("sha256"),
           "verified_download": rec.get("verified")}
    if rec.get("verified"):
        try:
            ck = torch.load(rec["path"], map_location="cpu", weights_only=True)
            sd = ck["state_dict"]
            st = load_file(f"{fetch.OUT}/PHerc.1667-iteration-{it}/model.safetensors")
            def norm(k):
                return k[len("model."):] if k.startswith("model.") else k
            ckn = {norm(k): v for k, v in sd.items()}
            common = [k for k in st if k in ckn]
            out.update(n_safetensors=len(st), n_ckpt=len(sd), n_common=len(common),
                       only_ckpt=sorted(set(ckn) - set(st))[:10], only_safetensors=sorted(set(st) - set(ckn))[:10],
                       max_abs_diff=max(float((st[k].float() - ckn[k].float()).abs().max()) for k in common),
                       global_step=ck.get("global_step"), epoch=ck.get("epoch"))
        except Exception as e:  # recorded, not worked around
            out["error"] = f"{type(e).__name__}: {str(e)[:300]}"
        os.remove(rec["path"])
        out["deleted"] = True
    out["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(fetch.REPO, "logs/sib/ckpt-screen-b/lastckpt_check.jsonl"), "a") as fh:
        fh.write(json.dumps(out) + "\n")
    print(json.dumps(out), flush=True)
