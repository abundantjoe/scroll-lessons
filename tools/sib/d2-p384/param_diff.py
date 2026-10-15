# Provenance: Project HERCULES | owner the owner | [id removed]
"""Independent measurement for the F384 question (numbers only, synthetic N(0,1) input, no real data).
Build A: the model from the base checkpoint's own embedded config (patch 17 x 128 x 128), weights loaded strict=True.
Build B: the same config with patch_size = crop_size = 17 x 384 x 384.
Records: every state_dict key whose presence or shape differs (with shapes and element counts), total parameter
counts, strict-load outcome of B, and build A's forward on a 17 x 384 x 384 input (output shape, finite, backward ok).
Writes logs/sib/d2-p384/param_diff.json."""
import copy
import hashlib
import json
import os
import sys

import torch
from vesuvius.ink_detection.config import TrainingConfig, resolve_training_mapping
from vesuvius.ink_detection.models.model import make_model

CK = "/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth"
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
OUT = os.path.join(REPO, "logs", "sib", "d2-p384", "param_diff.json")
torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "1")))
torch.manual_seed(0)
h = hashlib.sha256(open(CK, "rb").read()).hexdigest()
if h != "e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab":
    sys.exit(f"base sha256 mismatch {h}")
ck = torch.load(CK, map_location="cpu", weights_only=False)


def build(ps):
    m = copy.deepcopy(ck["config"])
    m["patch_size"] = list(ps)
    m["crop_size"] = list(ps)
    tc = TrainingConfig.from_mapping(resolve_training_mapping(m))
    return tc, make_model(tc.ink)


_, A = build(ck["config"]["patch_size"])
strictA = str(A.load_state_dict(ck["model"], strict=True))
_, B = build([17, 384, 384])
sa = {k: tuple(v.shape) for k, v in A.state_dict().items()}
sb = {k: tuple(v.shape) for k, v in B.state_dict().items()}
pa = {n for n, _ in A.named_parameters()}
diff = []
for k in sorted(set(sa) | set(sb)):
    if sa.get(k) != sb.get(k):
        na = int(torch.Size(sa[k]).numel()) if k in sa else None
        nb = int(torch.Size(sb[k]).numel()) if k in sb else None
        diff.append(dict(key=k, shape_128=sa.get(k), shape_384=sb.get(k), numel_128=na, numel_384=nb,
                         is_parameter=k in pa))
try:
    B.load_state_dict(ck["model"], strict=True)
    strictB = "ok"
except Exception as e:
    strictB = f"fails: {type(e).__name__} ({len(str(e))} chars)"
# group differing keys by module prefix (first two dotted components) for a readable summary
groups = {}
for d in diff:
    g = ".".join(d["key"].split(".")[:2])
    groups.setdefault(g, 0)
    groups[g] += 1
x = torch.randn(1, 1, 17, 384, 384)
A.eval()
with torch.no_grad():
    y = A(x)["ink"]
A.train()
yt = A(x)["ink"]
yt.float().mean().backward()
gok = all(torch.isfinite(p.grad).all() for p in A.parameters() if p.grad is not None)
res = dict(
    provenance="Provenance: Project HERCULES | owner the owner | [id removed]",
    base_sha256=h, data="SYNTHETIC N(0,1) input", config_patch_size=ck["config"]["patch_size"],
    model_type=ck["config"].get("model_type"),
    build_128=dict(state_keys=len(sa), n_params=sum(p.numel() for p in A.parameters()), strict_load=strictA),
    build_384=dict(state_keys=len(sb), n_params=sum(p.numel() for p in B.parameters()), strict_load_of_base=strictB),
    n_keys_differ=len(diff), n_param_tensors_differ=sum(d["is_parameter"] for d in diff),
    numel_differ_128=sum(d["numel_128"] or 0 for d in diff), numel_differ_384=sum(d["numel_384"] or 0 for d in diff),
    keys_only_in_128=sum(d["shape_384"] is None for d in diff), keys_only_in_384=sum(d["shape_128"] is None for d in diff),
    differ_by_module=groups, differing=diff,
    build_128_forward_384=dict(out_shape=list(y.shape), finite=bool(torch.isfinite(y).all()),
                               train_backward_finite=bool(gok)),
)
json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "differing"}, indent=1))
print(json.dumps(diff[:6], indent=1))
