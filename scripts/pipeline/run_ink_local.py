"""End-to-end villa flat ink inference (used by the ink stage of batch_ink.sh), CPU, N threads, optional bf16 autocast wrapper.
usage: run_ink_local.py <threads> <bf16:0|1> -- <infer.py argv...>"""
import sys, time, os
sys.dont_write_bytecode = True
pass
pass
import torch
threads, bf16 = int(sys.argv[1]), sys.argv[2] == '1'
argv = sys.argv[sys.argv.index('--') + 1:]
torch.set_num_threads(threads)
from vesuvius.ink_detection.inference import infer as I
if bf16:
    orig = I.configure_model
    class AC(torch.nn.Module):
        def __init__(s, m): super().__init__(); s.m = m
        def forward(s, x):
            with torch.autocast('cpu', dtype=torch.bfloat16):
                return s.m(x).float()
    def cfg(args):
        cm = orig(args); return cm.__class__(model=AC(cm.model).eval(), patch_size=cm.patch_size, input_depth=cm.input_depth,
                                             preprocessing=cm.preprocessing, amp_dtype=cm.amp_dtype)
    I.configure_model = cfg
import logging; logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
t0 = time.perf_counter()
rc = I.main(argv)
import resource; print("PEAK_RSS_MB", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss//1024)
print(f"E2E_WALL_S {time.perf_counter() - t0:.2f} threads={torch.get_num_threads()} bf16={bf16}", flush=True)
