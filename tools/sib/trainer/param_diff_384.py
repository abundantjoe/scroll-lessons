# Provenance: Project HERCULES | owner the owner | [id removed]
"""Q1 evidence (numbers only): parameter-level diff between the official model built from the base checkpoint's own
config (patch 17 x 128 x 128; strict load of the base weights) and the model built from the same config with
patch_size / crop_size 17 x 384 x 384. Lists keys only in one build, shape mismatches, parameter counts, and the
network's reported pooling configuration. Writes logs/sib/trainer/param_diff_384.json."""
import copy, collections, io, json, os, contextlib, torch
from vesuvius.ink_detection.config import TrainingConfig, resolve_training_mapping
from vesuvius.ink_detection.models.model import make_model

CK = "/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "logs", "sib", "trainer", "param_diff_384.json")
ck = torch.load(CK, map_location="cpu", weights_only=False)


def build(ps):
    m = copy.deepcopy(ck["config"]); m["patch_size"] = list(ps); m["crop_size"] = list(ps)
    tc = TrainingConfig.from_mapping(resolve_training_mapping(m))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        model = make_model(tc.ink)
    log = [l.strip() for l in buf.getvalue().splitlines() if "pool" in l.lower() or "stage" in l.lower()
           or "patch size" in l.lower() or "features_per_stage" in l.lower()]
    return model, log


m1, log1 = build([17, 128, 128])
strict = str(m1.load_state_dict(ck["model"], strict=True))
m3, log3 = build([17, 384, 384])
s1 = {k: tuple(v.shape) for k, v in m1.state_dict().items()}
s3 = {k: tuple(v.shape) for k, v in m3.state_dict().items()}
only1 = sorted(set(s1) - set(s3)); only3 = sorted(set(s3) - set(s1))
shape = sorted(k for k in set(s1) & set(s3) if s1[k] != s3[k])


def group(keys):
    c = collections.Counter(".".join(k.split(".")[:4]) for k in keys)
    return dict(sorted(c.items()))


n1 = sum(v.numel() for v in m1.parameters()); n3 = sum(v.numel() for v in m3.parameters())
res = dict(provenance="Provenance: Project HERCULES | owner the owner | [id removed]",
           base_sha256_prefix="e635558a", strict_load_base_build=strict,
           n_state_tensors=dict(base128=len(s1), build384=len(s3)),
           n_params=dict(base128=n1, build384=n3, diff=n3 - n1),
           keys_only_in_base128=len(only1), keys_only_in_build384=len(only3), same_key_shape_mismatch=len(shape),
           total_differing_tensors=len(only1) + len(only3) + len(shape),
           only_in_base128_by_module=group(only1), only_in_build384_by_module=group(only3),
           shape_mismatch_examples=[dict(key=k, base128=s1[k], build384=s3[k]) for k in shape[:20]],
           only_in_build384_examples=[dict(key=k, shape=s3[k]) for k in only3[:20]],
           network_log_base128=log1[:12], network_log_build384=log3[:12])
try:
    m3.load_state_dict(ck["model"], strict=True); res["strict_load_into_build384"] = "ok"
except RuntimeError as e:
    res["strict_load_into_build384"] = "fails (RuntimeError)"
json.dump(res, open(OUT, "w"), indent=1, default=list)
print(json.dumps({k: v for k, v in res.items() if not k.endswith("examples") and not k.startswith("network_log")}, default=list, indent=1))
