# Provenance: Project HERCULES | owner the owner | [id removed]
"""bf16 (AMX) CPU variant of the official flat inference CLI, without editing villa code.

The official vesuvius.ink_detection.inference.infer (villa 41701aa, infer.py sha256 979aed8e...0389) autocasts only
on CUDA (run_block_inference uses nullcontext() on CPU). This wrapper runs the unchanged infer.main(argv) inside
torch.autocast('cpu', dtype=torch.bfloat16). Autocast is thread-local; the model forward runs in the main thread,
DataLoader workers only read and normalise (numpy). Probabilities are computed from logits.float() (official
logits_to_probabilities), and blending and uint8 encoding are unchanged. Arguments are exactly the official CLI's.
Usage: python infer_bf16.py IN.zarr CKPT.pth OUT.tif --direction both --batch-size 4 --num-workers 1 --no-compile"""
import sys

import torch
from vesuvius.ink_detection.inference import infer


def main(argv=None):
    with torch.autocast("cpu", dtype=torch.bfloat16):
        return infer.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
