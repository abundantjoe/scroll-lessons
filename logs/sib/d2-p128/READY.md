Provenance: Project HERCULES | owner the owner | [id removed]

# d2-p128 READY (phase 1 complete; synthetic data only)

Task d2-p128 covers one arm of D2 (TRAIN-1): fold L-0841, arm P128 (tile 128, 24 x 15 deg rotations), seed 1.
Phase 1 is done. No real data was fetched or trained on. No image, rendered slice or ink map was opened, written or
described. No PHerc0841 data and no eligible-scroll data were touched. Weights stay local under /work and are not in git.
Real training waits for a GO D2 message that names the pair-freeze record and the RULES.md IDs.

## 1. Environment
- Container: 4 vCPU, 15 GB RAM, no GPU, disk 24 GB free on / after the smoke.
- CPU: Intel Xeon @ 2.80 GHz, family 6, model 85, stepping 7 (Cascade Lake), KVM guest, L3 33 MiB.
- ISA flags: avx, avx2, avx512f/dq/cd/bw/vl, avx512_vnni.
  **amx_bf16: ABSENT** (no amx_* and no avx512_bf16 flag in /proc/cpuinfo). This is a different, slower CPU than the
  2.1 GHz AMX machine in docker/TOOLING.md and the trainer's throughput.json. bf16 training (DECL-AMX-1 scope) is
  therefore not usable on this container. The arm runs fp32, which is also the declared default.
- nproc 4. free -g total 15. Full lscpu, flags and torch parallel info: out/20260926T002336Z_sysinfo.log.
- Setup: tools/sib/d2-p128/setup_p128_env.sh. It is the subset of docker/env/setup_env.sh needed for training:
  - villa sparse checkout at 41701aa0eaa1aa765523db3f9f972b5830abf549;
  - /opt/hv-ink, Python 3.13.12, torch 2.14.0+cpu, torchvision 0.29.0+cpu (download.pytorch.org cpu index);
  - every hv-ink-freeze.txt pin, installed with --no-deps. All versions match; the only differences are 5 name-case
    normalisations, e.g. PyYAML/pyyaml;
  - D3's extra packages (scipy, scikit-image, lazy_loader, fft-conv-pytorch, SimpleITK, pandas, connected-components-3d,
    numba, llvmlite), installed with --no-deps, plus pytest and pygments;
  - villa vesuvius added through a .pth path entry, as the trainer session did.
  First attempt: rc 1 (cc3d missing). Fixed and re-run: rc 0. Both runs are logged in runs.jsonl.
- torch: MKL-DNN v3.12.0, OpenMP backend. Threads during the smoke: intra 4, interop 1.

## 2. Code (pinned copy, unchanged)
Source: origin/claude/gifted-bell-gavnl5-sib-trainer at commit 8475920fa1a8dd7a753c426be0ebd592851ad884.
Every copy is byte-identical to that commit, and every sha256 equals the trainer's report.json `code_sha256`.

| tools/sib/d2-p128/ | sha256 |
|---|---|
| d2_train.py | fdbe236cc2cf46664c3d0558e58c7594220a4ce105fde3b5453d634680496f24 |
| d2_data.py | 5b7a6a5df4f07cf75ef84b63899e531c040b0cb13d8b45b7c180ac2b10a7676b |
| ckpt_shards.py | ba6db9991e14000b9ba051244c6ae2fa59928b4c6094cc64316ca559cbf3b974 |
| contam_check.py | 0e30cabbc762979f5b197c0365815dc5915048626c6a01ffb571c643b9f1321e |
| bench_throughput.py | a30101ccbd05b7cb6d4fc862301ea57ce3d46d183f8f466ebc01ab0e942b5181 |
| runlog.sh | 44805ecfe195bc3cd08d0139bbb3a9d2ebcbf2de880f97150b4674c64b715b2c |
| tests/sib_trainer_units_test.py | f4f8046173403f36edc16c3e938f4bdfa912ddd696dc253cd0d6063068405346 |
| tests/sib_trainer_integration_test.py | 162a48a7754c3a867854f0ffe06d47ffa6ec4679ab41939e6301d80b493df4b6 |

- My own helpers are listed in code_manifest.json. They are setup_p128_env.sh, runlog_p128.sh (runlog.sh with the log
  directory changed to logs/sib/d2-p128) and smoke_p128.sh. None of them changes trainer code.
- The proposed amendment DECL-D2-A1 (logs/sib/trainer/proposals/decl_d2_a1.txt) is read but is not binding. Nothing
  here depends on it.

## 3. Base checkpoint
- ink_9um hybrid_3d2d seed42 step-075000, from HF scrollprize/ink_9um revision 7109667e2607db1b90c37c8b09cb876ea7fe7bb1,
  path hybrid_3d2d-seed42/step-075000.pth.
- Local copy: /work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth.
- sha256 e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab: **VERIFIED** (sha256sum -c OK; the setup
  logs show it). This matches data/catalogue/checkpoints.json.
- The trainer checks it again at every start.

## 4. Unit and integration tests
- Command: pytest on tests/sib_trainer_units_test.py and tests/sib_trainer_integration_test.py, run in a scratch
  worktree of commit 8475920f (the tests import from tools/sib/trainer; the code there is byte-identical to the copy).
- Run 1 (pytest_units_integration): 5 passed, 21 errors. Every error happened at fixture setup, because the --basetemp
  parent directory /work/sib did not exist. This was my setup error, not a code failure.
- Run 2 (pytest_units_integration_2): **26 passed, 0 failed in 1338 s**. Output sha256 63b193d7...9597.
- The 26 include:
  - bitwise D3 equivalence for CTRL, FA, NULLA and REVA;
  - determinism;
  - paired sampling;
  - local and remote-shard resume;
  - bf16 refusal without the gate.

## 5. Synthetic smoke of this arm (smoke_p128.sh, run smoke_p128, exit 0)
Synthetic registry: d2_data.write_synthetic_registry, n 256, S 184 (the corner-free size for T 128), seed 1,
registry.json sha256 06846e72...d84c.

Config (smoke_cfg.json, config sha256 2e23202b89f0460105dd15966baa23bbe0cfa91f8cc494666d2c4436464bc5cc):
- arm P128, seed 1, tile 128, rot24 on, subtile on;
- batch 32, micro-batch 32, 30 steps;
- fp32, 4 threads;
- z window 17 of 21, jitter +-2, offset 0;
- AdamW lr 2e-5 constant, wd 3e-5, clip 1.0 (the trainer default; the D2 recipe is pinned by the orchestrator);
- log every step;
- ckpt-every 10, only so that saves happen inside 30 steps (the real run uses 250);
- no remote ref.

| Measure | Value |
|---|---|
| Median s/step, run A (30 steps) | **18.35 s** (mean 18.51, min 17.14, max 21.75; step 1 21.75) |
| Median s/step, resumed leg of B (10 steps) | 18.22 s |
| Peak RSS, run A | **6.85 GB** (6,852,544 kB) |
| Peak RSS, resumed leg (loads the resume state) | 7.32 GB |
| Finite losses | 30 / 30; loss step 1 0.6264, step 30 0.4645 (synthetic, meaningless as a metric) |
| Local resume state | 414,975,484 bytes; save 0.3-0.4 s |
| Save + resume test | B: hard exit (99) after step 25, last save at step 20; resumed from local state at step 20, ran to 30 |
| Resume identity | per-step losses 1-30 **bitwise equal** to A; final weights **bitwise equal** (torch.equal on every tensor); model_final.pth sha256 identical for A and B: 2fdb87d51d89cba1441739faa1cc282054afa340594d9662d496cd59ead13c07; sample digest equal |

Full numbers: smoke_result.json. Step log: out/20260926T004641Z_smoke_p128.log.

## 6. Forecast for the real arm (numbers only; nothing launched)
- 12,000 steps x 18.35 s = **61.2 h (2.55 d)** of loop time at fp32 on this CPU.
- That is 1.54 x the trainer's 11.94 s/step on the AMX machine. Local checkpoint saves add < 1 min in total.
- Real-data s/step may differ, so it will be re-measured in the first 50-step log window.
- Peak RAM of about 7 GB leaves room in 15 GB.
- Disk: one resume state is 415 MB and only the latest is kept; model_final is 138 MB.

## 7. Open items for the orchestrator (my defaults; nothing waits on me)
1. **Reclaim risk over about 61 h.**
   - Resume states are local (/work) only. A container reclaim would lose them, and the run would restart from step 0.
   - The trainer's remote-shard option pushes 415 MB per save to a separate git ref. That would be a push to a branch
     other than my session branch, and the brief forbids it without permission. It also conflicts with DECL-OFFLOAD-1
     / ASK 6 repo growth.
   - Default: local-only saves every 250 steps and a nohup job with a harness-tracked waiter, unless the GO message
     authorises a ckpt ref.
2. **Recipe.** DECL-D2 says "base recipe, batch 32, 12k steps, 24 x 15 deg rotations". The optimiser (trainer default
   AdamW 2e-5 constant vs the base SGD/cosine), --subtile and source filters are proposal items (DECL-D2-A1 4b-4e).
   I will run exactly what the GO message and RULES.md IDs declare, and nothing else.
3. **Precision.** fp32 only: this container has no AMX.
