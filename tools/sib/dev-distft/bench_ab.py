# Provenance: Project HERCULES | owner the owner | [id removed]
"""Timing A/B on SYNTHETIC data (numbers only): pinned Trainer (hard target) vs DIST-FT (soft) with the augmentation
label check off and on, same config otherwise (tile 128, rot24, sub-tiles, batch 32, fp32, 4 threads).
Usage: bench_ab.py <registry.json> <out.json> <steps>"""
import copy, json, os, statistics, sys, time
os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = "4"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import distft, d2_train, torch  # noqa: E402
reg, outp, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
PIN = d2_train.Trainer
torch.set_num_interop_threads(1); torch.set_num_interop_threads = lambda k: None
res = {}
for name, cls, target, chk in (("pinned_hard", PIN, "hard", None), ("distft_soft_nocheck", distft.DistFTTrainer, "soft", 0),
                               ("distft_soft_check", distft.DistFTTrainer, "soft", 4000)):
    cp = f"/work/distft/bench_{name}.json"
    distft.make_config(["--arm", "DIST-FT", "--target", target, "--out", cp, "--batch", "32", "--steps", str(n),
                        "--threads", "4", "--subtile", "--source", f"syn=pairs:{reg}"])
    cfg = json.load(open(cp))
    if chk is not None:
        distft.DistFTTrainer.check_aug_samples = chk
    t = cls(copy.deepcopy(cfg), f"/work/distft/bench_{name}")
    w = []
    for i in range(n + 1):
        t0 = time.perf_counter(); t.train_step(i); dt = time.perf_counter() - t0
        if i: w.append(dt)
    t0 = time.perf_counter()
    for _ in range(3): t.make_batch()
    res[name] = dict(s_per_step=w, median=statistics.median(w), make_batch_s=(time.perf_counter() - t0) / 3)
    print(name, json.dumps(res[name]), flush=True)
json.dump(dict(provenance=distft.PROV, data="SYNTHETIC", steps_timed=n, warmup=1, results=res), open(outp, "w"), indent=1)
