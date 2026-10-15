# Provenance: Project HERCULES | owner the owner | [id removed]
"""Manifest for dev-distft's P4-O iteration-2 tiles: the UNCHANGED p4o_tiles.finalize (sha256 checks of every PNG,
e2 validity and eligibility checks), with two adaptations recorded in the manifest:
  1. SPECS.json is read from ckpt-screen-b's branch (git object; it is not on this branch) via a scratch root;
  2. the inference block states the true builder paths and the per-tile precision (PRECISION.json: r0 c5 fp32, the
     rest as ruled by bf16_check.json), since finalize() hard-codes dtype float32.
Usage: p4o_finalize.py <out_dir>"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p4o_tiles as P  # noqa: E402
SPECS_REF = "origin/claude/gifted-bell-gavnl5-sib-ckpt-screen-b:logs/sib/ckpt-screen-b/SPECS.json"
out = os.path.abspath(sys.argv[1])
real = P.REPO
root = "/work/p4o/specroot"
os.makedirs(f"{root}/logs/sib/ckpt-screen-b", exist_ok=True)
blob = subprocess.check_output(["git", "-C", real, "show", SPECS_REF])
open(f"{root}/logs/sib/ckpt-screen-b/SPECS.json", "wb").write(blob)
P.git_json = lambda ref: json.loads(subprocess.check_output(["git", "-C", real, "show", ref]))
P.REPO = root
P.finalize(2, out)
p = os.path.join(out, "manifest.json")
man = json.load(open(p))
prec = json.load(open(os.path.join(out, "PRECISION.json")))
chk = json.load(open(os.path.join(out, "bf16_check.json")))
fn5 = "tiles/20260701183124-w010-027_r0_c5.png"
for t in man["tiles"]:
    t["precision"] = "fp32" if t["file"] == fn5 else prec["precision_after_check"]
man["builder_session"] = "dev-distft (DECL-P4-14-A1; harness batch o5)"
man["inference"].update(
    builder="tools/sib/dev-distft/p4o_tiles.py (byte-identical to tools/sib/ckpt-screen-b/p4o_tiles.py @ ca732aef)",
    wrapper="tools/sib/dev-distft/infer_1667.py (byte-identical to tools/sib/ckpt-screen-b/infer_1667.py @ ca732aef)",
    dtype="per tile (tiles[].precision); float32 for r0 c5; " + prec["precision_after_check"] + " for the rest",
    bf16_runner=("tools/sib/dev-distft/p4o_bf16.py: the unchanged builder with the model under torch.autocast "
                 "(cpu, bfloat16), fp32 logits"),
    bf16_check=dict(rule=chk["rule"], tile="r0 c5", frac_gt2_valid=chk["frac_gt2_valid"], passed=chk["pass"],
                    max_abs_diff=chk["max_abs_diff"]),
    specs_source=SPECS_REF)
man["checkpoint"]["weights_sha256_expected"] = "485ce6e12cca19071c5746d95327d9aa6f2fd04ea1a2acc95c9530d3ee895b71"
assert man["checkpoint"]["weights_sha256"] == man["checkpoint"]["weights_sha256_expected"], man["checkpoint"]
json.dump(man, open(p, "w"), indent=1)
print(p, P.I.sha256(p), man["n_tiles"])
