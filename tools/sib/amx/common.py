# Provenance: Project HERCULES | owner the owner | [id removed]
"""Shared setup for the AMX benchmarks: official base model + D3 training recipe (tools/d3/d3_train.py), random inputs only.

No scroll data is read. Model, loss and optimizer come from villa 41701aa vesuvius.ink_detection; the checkpoint is
ink_9um hybrid_3d2d seed42 step-075000 (sha256 verified on every load)."""
import copy, hashlib, json, os, resource, subprocess, time
import numpy as np
import torch

CK = "/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth"
CK_SHA = "e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab"
LR, WD, TRAIN_BATCH, INFER_BATCH = 2e-5, 3e-5, 8, 4


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def peak_rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def cur_rss_mb():
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024.0
    return float("nan")


def load(train=False):
    """Returns (model, ink_config, training_config, loss_fn, checkpoint_config). Weights loaded strictly."""
    from vesuvius.ink_detection.config import TrainingConfig, resolve_training_mapping
    from vesuvius.ink_detection.models.model import make_model
    from vesuvius.ink_detection.models.checkpoint import load_checkpoint
    from vesuvius.ink_detection.training.losses import create_loss
    assert sha256(CK) == CK_SHA
    ck = load_checkpoint(CK)
    mapping = copy.deepcopy(ck["config"])
    mapping.update(optimizer="adamw", learning_rate=LR, weight_decay=WD, batch_size=TRAIN_BATCH, num_iterations=2000,
                   seed=20260925, out_dir="/work/amx/unused")
    mapping["fixed_scroll_prior"] = dict(mapping["fixed_scroll_prior"], seed=20260925)
    tc = TrainingConfig.from_mapping(resolve_training_mapping(mapping))
    ink = tc.ink
    model = make_model(ink)
    model.load_state_dict(ck["model"], strict=True)
    cfg = ck["config"]
    del ck
    return model, ink, tc, create_loss(ink), cfg


def rand_batch(n, gen, with_labels=False, supervised_frac=0.95):
    """Random input shaped like the real (post robust_mad) input: N(0,1), (n,1,17,128,128) fp32. Labels random."""
    x = torch.randn(n, 1, 17, 128, 128, generator=gen)
    if not with_labels:
        return x
    ink = (torch.rand(n, 1, 17, 128, 128, generator=gen) < 0.3).float()
    sup = (torch.rand(n, 1, 17, 128, 128, generator=gen) < supervised_frac).float()
    return dict(image=x, inklabels=ink, supervision_mask=sup)


def stats(times):
    t = np.asarray(times, float)
    q1, med, q3 = np.percentile(t, [25, 50, 75])
    return dict(median_s=float(med), q1_s=float(q1), q3_s=float(q3), iqr_s=float(q3 - q1), mean_s=float(t.mean()),
                min_s=float(t.min()), max_s=float(t.max()), n=len(t))


def env_info():
    return dict(torch=torch.__version__, mkldnn=torch.backends.mkldnn.is_available(),
                onednn_cpu_capability=torch.backends.cpu.get_cpu_capability(),
                villa=subprocess.run(["git", "-C", "/work/villa", "rev-parse", "HEAD"], capture_output=True,
                                     text=True).stdout.strip())
