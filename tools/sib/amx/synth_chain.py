# Provenance: Project HERCULES | owner the owner | [id removed]
"""End-to-end smoke of the bf16 inference chain and the gate on SYNTHETIC data only (no scroll data).

Builds a random uint8 flat surface volume (21 x 640 x 640, depth-first zarr), runs the official CLI in fp32 and the
bf16 wrapper (tools/sib/amx/infer_bf16.py), both orders, batch 4, --no-compile, then runs amx_gate.py with synthetic
labels (a fixed random half-plane mask, so AUCs are ~0.5 by construction and the AUC bars are expected to FAIL; the
purpose is to measure fp32-vs-bf16 map agreement through the full official chain and to exercise the gate CLI)."""
import os, subprocess, sys, json, hashlib
import numpy as np
import zarr

D = "/work/amx/synth"
os.makedirs(D, exist_ok=True)
rng = np.random.default_rng(20260925)
vol = rng.normal(120, 25, (21, 640, 640)).clip(0, 255).astype(np.uint8)
zp = f"{D}/synth.zarr"
if not os.path.exists(zp):
    z = zarr.create_array(zp, shape=vol.shape, chunks=(21, 128, 128), dtype="uint8")
    z[:] = vol
CK = "/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth"
PY = "/opt/hv-ink/bin/python"
HERE = os.path.dirname(os.path.abspath(__file__))
common = ["--direction", "both", "--batch-size", "4", "--num-workers", "1", "--no-compile"]
env = dict(os.environ, OMP_NUM_THREADS="4")
RUNS = (("fp32", [PY, "-m", "vesuvius.ink_detection.inference.infer"]), ("bf16", [PY, f"{HERE}/infer_bf16.py"]),
        ("fp32rep", [PY, "-m", "vesuvius.ink_detection.inference.infer"]))  # fp32rep: determinism of the fp32 chain
for tag, cmd in RUNS:
    out = f"{D}/{tag}.tif"
    if not os.path.exists(out):
        r = subprocess.run(cmd + [zp, CK, out] + common, env=env, capture_output=True, text=True)
        open(f"{D}/{tag}.log", "w").write(r.stdout + r.stderr)
        assert r.returncode == 0, (tag, r.stderr[-2000:])
print(sorted(os.listdir(D)))
import tifffile
m = {t: tifffile.imread(f"{D}/{t}.tif") for t in ("fp32", "bf16")}
m.update({f"{t}_rev": tifffile.imread(f"{D}/{t}_reverse.tif") for t in ("fp32", "bf16")})
for t, a in (("fp32", m["fp32"]), ("bf16", m["bf16"]), ("fp32_reverse", m["fp32_rev"]), ("bf16_reverse", m["bf16_rev"])):
    np.save(f"{D}/{t}.npy", a)  # the gate env (/opt/hv) has no imagecodecs for the official LZW TIFFs (as tools/c3/tif2npy.py)
lab = np.zeros(m["fp32"].shape, np.uint8)
lab[:, : lab.shape[1] // 2] = 255
valid = np.ones(m["fp32"].shape, np.uint8)
np.save(f"{D}/labels.npy", lab); np.save(f"{D}/valid.npy", valid)
genv = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}  # the gate runs in /opt/hv (py3.11)
r = subprocess.run(["/opt/hv/bin/python", f"{HERE}/amx_gate.py", "--fp32-fwd", f"{D}/fp32.npy", "--bf16-fwd", f"{D}/bf16.npy",
                    "--fp32-rev", f"{D}/fp32_reverse.npy", "--bf16-rev", f"{D}/bf16_reverse.npy", "--labels", f"{D}/labels.npy",
                    "--valid", f"{D}/valid.npy", "--out", sys.argv[1]], capture_output=True, text=True, env=genv)
print(r.stdout, r.stderr[-1500:], "gate_rc", r.returncode)
res = json.load(open(sys.argv[1]))
res["synthetic"] = dict(volume_shape=list(vol.shape), volume_sha256=hashlib.sha256(vol.tobytes()).hexdigest(),
                        note="random N(120,25) uint8 volume, half-plane synthetic labels; AUC bars meaningless here",
                        maps_dtype=str(m["fp32"].dtype), maps_shape=list(m["fp32"].shape),
                        fp32_logs_sha256=hashlib.sha256(open(f"{D}/fp32.log", "rb").read()).hexdigest())
sh = {t: hashlib.sha256(open(f"{D}/{t}.tif", "rb").read()).hexdigest() for t in ("fp32", "fp32rep", "bf16", "fp32_reverse", "fp32rep_reverse", "bf16_reverse")}
res["synthetic"]["map_sha256"] = sh
res["synthetic"]["fp32_chain_bitwise_deterministic"] = dict(
    forward=bool(np.array_equal(tifffile.imread(f"{D}/fp32.tif"), tifffile.imread(f"{D}/fp32rep.tif"))),
    reverse=bool(np.array_equal(tifffile.imread(f"{D}/fp32_reverse.tif"), tifffile.imread(f"{D}/fp32rep_reverse.tif"))))
json.dump(res, open(sys.argv[1], "w"), indent=1)
print(json.dumps(res["synthetic"]["fp32_chain_bitwise_deterministic"]))
