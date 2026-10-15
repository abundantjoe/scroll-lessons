# Provenance: Project HERCULES | owner the owner | [id removed]
"""AMX-TRAIN arm P16 (proposal DECL-AMX-1 II.2): run tools/d3/d3_train.py UNCHANGED inside
torch.autocast('cpu', dtype=torch.bfloat16). Arguments are passed through verbatim (e.g. --arm CTRL --out DIR).

d3_train.py already computes the loss on .float() logits; CPU autocast lowers only conv/matmul-class ops, so the loss,
grad clipping and AdamW (fp32 master weights, no grad scaler) stay fp32. Autocast is thread-local; the training step
runs in the main thread. The wrapper records the sha256 of the trainer it ran. NOT RUN until declared."""
import hashlib, os, runpy, sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
TRAINER = os.path.abspath(os.path.join(HERE, "..", "..", "d3", "d3_train.py"))

if __name__ == "__main__":
    print("d3_train_bf16: trainer sha256", hashlib.sha256(open(TRAINER, "rb").read()).hexdigest(), flush=True)
    sys.argv = [TRAINER] + sys.argv[1:]
    with torch.autocast("cpu", dtype=torch.bfloat16):
        runpy.run_path(TRAINER, run_name="__main__")
