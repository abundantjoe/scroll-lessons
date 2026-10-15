# Provenance: Project HERCULES | owner the owner | [id removed]
"""Item 6: D2 trainer throughput on this 4-core AMX CPU with SYNTHETIC data (numbers only).

Matrix: tile 128 / 384 (/ 512 if --with-512) x fp32 / bf16 autocast, batch 32, rot24 on (as the D2 arms), 4 threads;
384/512 also with the official stitched forward. Micro-batch is the largest in the list that fits in RAM (the first
that runs without being killed). Each cell: 1 warm-up step + N timed optimizer steps, run as its own process
(d2_train.py bench), sequentially, nothing else heavy running. Output: logs/sib/trainer/throughput.json with
steps/hour and the projected wall time of a 12k-step D2 arm per session."""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
import d2_data  # noqa: E402

PY = "/opt/hv-ink/bin/python"
PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"


def cell(work, reg, tile, prec, fwd, micro_list, steps, threads):
    last = None
    for micro in micro_list:
        tag = f"t{tile}_{prec}_{fwd}_m{micro}"
        cfgp = os.path.join(work, tag + ".json")
        subprocess.run([PY, os.path.join(HERE, "d2_train.py"), "make-config", "--arm", f"BENCH{tile}", "--seed", "1",
                        "--tile", str(tile), "--rot24", "--batch", "32", "--micro-batch", str(micro), "--steps", "12000",
                        "--forward", fwd, "--precision", prec, "--threads", str(threads),
                        "--source", f"syn=pairs:{reg}", "--out", cfgp], check=True, capture_output=True)
        out = os.path.join(work, tag)
        t0 = time.time()
        env = dict(os.environ, OMP_NUM_THREADS=str(threads), MKL_NUM_THREADS=str(threads))
        r = subprocess.run([PY, os.path.join(HERE, "d2_train.py"), "bench", "--config", cfgp,
                            "--out", out, "--steps", str(steps), "--warmup", "1"], capture_output=True, text=True,
                           env=env)
        wall = time.time() - t0
        open(os.path.join(work, tag + ".log"), "w").write(r.stdout[-20000:] + "\n---\n" + r.stderr[-20000:])
        last = dict(tile=tile, precision=prec, forward=fwd, micro_batch=micro, rc=r.returncode, wall_s=round(wall, 1))
        if r.returncode == 0:
            b = json.load(open(os.path.join(out, "bench.json")))
            h12k = 12000 * b["median_s_per_step"] / 3600
            last.update(median_s_per_step=b["median_s_per_step"], s_per_step=b["s_per_step"],
                        steps_per_hour=b["steps_per_hour"], peak_rss_GB=b["peak_rss_kb"] * 1024 / 1e9,
                        projected_h_12k_steps=h12k, projected_days_12k_steps=h12k / 24)
            return last
        last["stderr_tail"] = r.stderr[-400:]
    return last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="/work/sib/bench")
    ap.add_argument("--steps", type=int, default=3)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--with-512", action="store_true")
    ap.add_argument("--out", default=os.path.join(REPO, "logs", "sib", "trainer", "throughput.json"))
    a = ap.parse_args()
    os.makedirs(a.work, exist_ok=True)
    reg560 = os.path.join(a.work, "syn560", "registry.json")
    if not os.path.exists(reg560):
        d2_data.write_synthetic_registry(os.path.dirname(reg560), n=40, size=560, seed=101, shard_n=20)
    cells = [(128, "fp32", "full", [32, 16, 8]), (128, "bf16", "full", [32, 16, 8]),
             (384, "fp32", "full", [8, 4, 2]), (384, "bf16", "full", [8, 4, 2]),
             (384, "fp32", "stitched", [8, 4, 2]), (384, "bf16", "stitched", [8, 4, 2])]
    regs = {128: reg560, 384: reg560}
    if a.with_512:
        reg736 = os.path.join(a.work, "syn736", "registry.json")
        if not os.path.exists(reg736):
            d2_data.write_synthetic_registry(os.path.dirname(reg736), n=24, size=736, seed=102, shard_n=12)
        regs[512] = reg736
        cells += [(512, "fp32", "full", [4, 2, 1]), (512, "bf16", "full", [4, 2, 1])]
    res = dict(provenance=PROV, id="d2_trainer_throughput", data="SYNTHETIC (d2_data.write_synthetic_registry)",
               machine=dict(nproc=os.cpu_count(), cpu=next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo")
                                                           if l.startswith("model name")), "?"),
                            amx=("amx_bf16" in open("/proc/cpuinfo").read())),
               threads=a.threads, batch=32, rot24=True, timed_steps=a.steps, warmup_steps=1, cells=[])
    for tile, prec, fwd, ml in cells:
        c = cell(a.work, regs[tile], tile, prec, fwd, ml, a.steps, a.threads)
        res["cells"].append(c)
        print(json.dumps({k: v for k, v in c.items() if k != "s_per_step"}), flush=True)
        json.dump(res, open(a.out, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
