# Provenance: Project HERCULES | owner the owner | [id removed]
"""Ruling on ASK 1: "full 384 mode only if the unchanged base architecture runs it fully convolutionally with strict
weight loading". Numbers only, synthetic input. Builds the model from the base checkpoint's own embedded config
(patch_size 17 x 128 x 128, unchanged), loads the weights with strict=True, then runs 17 x T x T inputs for
T = 128, 384, 512 through (a) the model directly (full) and (b) the official stitched forward, in eval mode and in
train mode with backward. Also records the parameter-shape mismatch when the model is instead built from
patch_size 384 (the reason official infer cannot build a 384 model). Writes logs/sib/trainer/full_conv_check.json."""
import copy, hashlib, json, os, sys
import torch
from vesuvius.ink_detection.config import TrainingConfig, resolve_training_mapping
from vesuvius.ink_detection.models.model import make_model
from vesuvius.ink_detection.training.stitching import run_model_forward

CK = "/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "logs", "sib", "trainer", "full_conv_check.json")
torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "4")))
torch.manual_seed(0)
h = hashlib.sha256(open(CK, "rb").read()).hexdigest()
assert h.startswith("e635558a"), h
ck = torch.load(CK, map_location="cpu", weights_only=False)


def build(ps):
    m = copy.deepcopy(ck["config"]); m["patch_size"] = list(ps); m["crop_size"] = list(ps)
    tc = TrainingConfig.from_mapping(resolve_training_mapping(m))
    return tc, make_model(tc.ink)


tc, model = build(ck["config"]["patch_size"])
strict = str(model.load_state_dict(ck["model"], strict=True))
res = dict(provenance="Provenance: Project HERCULES | owner the owner | [id removed]", base_sha256=h,
           config_patch_size=ck["config"]["patch_size"], strict_load=strict, data="SYNTHETIC N(0,1) input", tiles={})
for T in (128, 384, 512):
    r = {}
    x = torch.randn(1, 1, 17, T, T)
    model.eval()
    with torch.no_grad():
        yf = model(x)["ink"]
        ys = run_model_forward(model, x, tuple(tc.model_crop_size), stitched=True, use_gradient_checkpointing=False)
    r["full_eval_out_shape"] = list(yf.shape); r["stitched_eval_out_shape"] = list(ys.shape)
    r["full_finite"] = bool(torch.isfinite(yf).all())
    r["full_vs_stitched_max_abs_diff"] = float((yf - ys).abs().max())
    # full-mode interior agrees with a 128 forward of the same pixels? (context changes the output: expected != 0)
    model.train()
    x.requires_grad_(False)
    y = model(x)["ink"]
    y.float().mean().backward()
    g = [p.grad for p in model.parameters() if p.grad is not None]
    r["train_backward_ok"] = bool(len(g) > 0 and all(torch.isfinite(t).all() for t in g))
    model.zero_grad(set_to_none=True)
    res["tiles"][str(T)] = r
_, m384 = build([17, 384, 384])
s1 = {k: tuple(v.shape) for k, v in model.state_dict().items()}
s3 = {k: tuple(v.shape) for k, v in m384.state_dict().items()}
res["built_from_384_same_param_shapes"] = s1 == s3
res["built_from_384_n_params_differ"] = sum(1 for k in set(s1) | set(s3) if s1.get(k) != s3.get(k))
try:
    m384.load_state_dict(ck["model"], strict=True); res["built_from_384_strict_load"] = "ok"
except Exception as e:
    res["built_from_384_strict_load"] = "fails: " + type(e).__name__
res["verdict"] = ("the unchanged base architecture (built from its own 128 config, strict load) runs 384 and 512 tiles "
                  "fully convolutionally: " + str(all(res["tiles"][t]["full_eval_out_shape"][-2:] == [int(t)] * 2 and
                                                       res["tiles"][t]["train_backward_ok"] for t in res["tiles"])))
json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps(res, indent=1))
