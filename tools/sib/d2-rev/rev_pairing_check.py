# Provenance: Project HERCULES | owner the owner | [id removed]
"""d2-rev: verify on SYNTHETIC data that the REV arm is exactly "P384 with every input stack reversed in depth" and is
paired with P384 (same patch, z jitter, rotation and augmentation sequence). Numbers and hashes only; no image written.

Runs the pinned trainer (d2_train.py, unchanged) in-process for three configs that differ only as stated:
  A = P384 on registry R;  B = REV on R;  C = P384 on R with every stored 21-slice stack depth-reversed here (by this
  script, independently of the trainer's REV code).
Per micro-batch it records sha256 of the model input x, of the ink labels and of the supervision mask, and after every
batch draw the sha256 of the python / numpy / torch global RNG states and of the sampling + rotation generators.
PASS requires, at every step:
  (1) x(B) == x(C) bitwise                  (REV = P384 on depth-reversed stacks, same window/jitter/rotation/aug);
  (2) labels and masks equal in A, B, C     (labels unchanged; geometric draws identical);
  (3) every RNG state equal in A, B, C      (augmentation draw sequence identical, pixel values do not steer draws);
  (4) sample_digest equal in A, B, C        (trainer's own (patch, z offset, rotation) chain);
  (5) x(B) != x(A)                          (the reversal is actually applied);
  (6) loss(B) == loss(C) and grad norm(B) == grad norm(C) bitwise (deterministic, same threads);
  (7) trainer check rev_*_exact_depth_reverse is True in B.
Usage: python rev_pairing_check.py --registry R/registry.json --out DIR --steps 2 [--batch 32 --micro-batch 4]"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"


def h(b) -> str:
    return hashlib.sha256(b).hexdigest()


def th(t) -> str:
    return h(t.detach().contiguous().cpu().numpy().tobytes())


def rng_hash(tr) -> dict:
    import pickle
    st = tr.rng_state()
    return dict(python=h(pickle.dumps(st["python"])), numpy=h(pickle.dumps(st["numpy"])),
                torch=th(st["torch"]), gens=h(json.dumps(st["gens"], sort_keys=True).encode()),
                rot=h(json.dumps(st["rot"], sort_keys=True).encode()))


def run(name, cfg, sources, out, steps):
    import d2_train
    tr = d2_train.Trainer(cfg, os.path.join(out, name), sources=sources)
    rec = dict(steps=[])
    cur = {}
    orig_mb, orig_fwd = tr.make_batch, tr.forward

    def make_batch():
        batch, srcs = orig_mb()
        cur["batch"] = dict(ink=th(batch["inklabels"]), sup=th(batch["supervision_mask"]),
                            image_aug=th(batch["image"]), srcs=srcs, rng=rng_hash(tr), digest=tr.sample_digest)
        cur["x"] = []
        return batch, srcs

    def forward(x):
        cur["x"].append(th(x))
        return orig_fwd(x)

    tr.make_batch, tr.forward = make_batch, forward
    for step in range(steps):
        t0 = time.perf_counter()
        loss, gn, srcs, supf = tr.train_step(step)
        rec["steps"].append(dict(step=step + 1, loss=loss, grad_norm=gn, supervised_frac=supf, x=cur["x"],
                                 s=time.perf_counter() - t0, **cur["batch"]))
        print(json.dumps(dict(run=name, step=step + 1, loss=loss, gn=gn, s=rec["steps"][-1]["s"])), flush=True)
    rec["checks"] = tr.checks
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--steps", type=int, default=2)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--micro-batch", type=int, default=4)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--forward", default="full")
    ap.add_argument("--single", default=None)
    ap.add_argument("--arm", default=None)
    ap.add_argument("--rev-here", type=int, default=0)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.single:
        import numpy as np
        import d2_data
        cfg = json.load(open(os.path.join(a.out, f"cfg_{a.arm}.json")))
        srcs = [d2_data.load_source(s) for s in cfg["sources"]]
        if a.rev_here:
            for s in srcs:
                s.images = np.ascontiguousarray(s.images[:, ::-1])  # independent reversal, not the trainer's code
        rec = run(a.single, cfg, srcs, a.out, cfg["steps"])
        json.dump(rec, open(os.path.join(a.out, f"rec_{a.single}.json"), "w"))
        return
    import numpy as np
    import d2_data
    import d2_train
    cfgs = {}
    for arm in ("P384", "REV"):
        p = os.path.join(a.out, f"cfg_{arm}.json")
        d2_train.main(["make-config", "--arm", arm, "--seed", "1", "--batch", str(a.batch), "--micro-batch",
                       str(a.micro_batch), "--steps", str(a.steps), "--rot24", "--subtile", "--threads", str(a.threads),
                       "--z-jitter", "2", "--z-centre-offset", "0", "--lr", "2e-5", "--weight-decay", "3e-5",
                       "--forward", a.forward, "--precision", "fp32", "--source", f"syn=pairs:{a.registry}",
                       "--log-every", "1", "--ckpt-every", "0", "--out", p])
        cfgs[arm] = json.load(open(p))
    spec = cfgs["P384"]["sources"]
    # one arm per process: torch allows set_num_interop_threads only once per process
    recs = {}
    for name, arm, rev_here in (("A_P384", "P384", 0), ("B_REV", "REV", 0), ("C_P384_on_reversed", "P384", 1)):
        rp = os.path.join(a.out, f"rec_{name}.json")
        if not os.path.exists(rp):
            r = subprocess.run([sys.executable, os.path.abspath(__file__), "--single", name, "--arm", arm,
                                "--rev-here", str(rev_here), "--registry", a.registry, "--out", a.out,
                                "--steps", str(a.steps)], env=dict(os.environ))
            if r.returncode != 0:
                sys.exit(f"{name}: rc {r.returncode}")
        recs[name] = json.load(open(rp))
    A, B, C = recs["A_P384"], recs["B_REV"], recs["C_P384_on_reversed"]

    per = []
    for sa, sb, sc in zip(A["steps"], B["steps"], C["steps"]):
        per.append(dict(
            step=sa["step"],
            x_B_eq_C=sb["x"] == sc["x"],
            x_B_ne_A_all_micro=all(xb != xa for xa, xb in zip(sa["x"], sb["x"])),
            labels_equal_ABC=sa["ink"] == sb["ink"] == sc["ink"] and sa["sup"] == sb["sup"] == sc["sup"],
            rng_equal_ABC=sa["rng"] == sb["rng"] == sc["rng"],
            srcs_equal_ABC=sa["srcs"] == sb["srcs"] == sc["srcs"],
            digest_equal_ABC=sa["digest"] == sb["digest"] == sc["digest"],
            loss_B_eq_C=sb["loss"] == sc["loss"], gn_B_eq_C=sb["grad_norm"] == sc["grad_norm"],
            loss=dict(A=sa["loss"], B=sb["loss"], C=sc["loss"]), n_micro=len(sb["x"]),
            rotations=[r[3] for r in sb["srcs"]], z_offsets=[r[2] for r in sb["srcs"]]))
    keys = ["x_B_eq_C", "x_B_ne_A_all_micro", "labels_equal_ABC", "rng_equal_ABC", "srcs_equal_ABC",
            "digest_equal_ABC", "loss_B_eq_C", "gn_B_eq_C"]
    rev_checks = {k: v for k, v in B["checks"].items() if k.startswith("rev_")}
    ok = all(all(p[k] for k in keys) for p in per) and bool(rev_checks) and all(rev_checks.values())
    res = dict(provenance=PROV, id="d2rev_pairing_check", data="SYNTHETIC", registry=a.registry,
               registry_sha256=h(open(a.registry, "rb").read()),
               script_sha256=h(open(os.path.abspath(__file__), "rb").read()),
               d2_train_sha256=h(open(os.path.join(HERE, "d2_train.py"), "rb").read()),
               d2_data_sha256=h(open(os.path.join(HERE, "d2_data.py"), "rb").read()),
               config_sha256=dict(P384=d2_train.config_sha256(cfgs["P384"]), REV=d2_train.config_sha256(cfgs["REV"])),
               config_diff={k: (cfgs["P384"][k], cfgs["REV"][k]) for k in cfgs["P384"]
                            if cfgs["P384"][k] != cfgs["REV"][k]},
               batch=a.batch, micro_batch=a.micro_batch, forward=a.forward, threads=a.threads, steps=a.steps,
               per_step=per, rev_trainer_checks=rev_checks, pass_=ok)
    json.dump(res, open(os.path.join(a.out, "pairing_check.json"), "w"), indent=1)
    print(json.dumps(dict(pass_=ok, per_step=[{k: p[k] for k in keys} for p in per])), flush=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
