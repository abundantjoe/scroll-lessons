Provenance: Project HERCULES | owner the owner | [id removed]

# d2-rev READY (PHASE 1 complete; no real data touched)

Task: D2 (TRAIN-1), fold L-0841, arm REV (P384 with every 21-slice input stack reversed in depth, labels unchanged),
seed 1. This session trains nothing on real data until the orchestrator sends "GO D2", naming the pair-freeze record
and the RULES.md IDs. Everything below is SYNTHETIC. No image was opened, written or described, and no weights were
pushed anywhere. Every command is in `logs/sib/d2-rev/runs.jsonl`, failures included.

## 1. Environment (pinned)

| Item | Value |
|---|---|
| Host | Intel Xeon @ 2.80 GHz, 4 vCPU (1 thread/core, 1 socket), L3 33 MiB; 15 GiB RAM, no swap; disk 28 GB free |
| AMX | **ABSENT**. Flags include avx512f/dq/cd/bw/vl and avx512_vnni. There is no amx_bf16, amx_tile, amx_int8 or avx512_bf16. bf16 training is not possible here, so **fp32 only**. |
| villa | /work/villa sparse checkout, commit 41701aa0eaa1aa765523db3f9f972b5830abf549 (vesuvius only) |
| venv | /opt/hv-ink, Python 3.13.12. torch 2.14.0+cpu and torchvision 0.29.0+cpu; the other packages from docker/env/hv-ink-freeze.txt with --no-deps. `uv pip freeze` equals the freeze file except for the `huggingface-hub` name spelling, plus pytest 9.1.1. villa src is on the path through a `.pth` entry (the editable install needs Python >= 3.14). |
| extra deps | /work/d3_timing/pylib, used via PYTHONPATH (`--no-deps --target`). These are the exact D3 versions from logs/d1/d3_timing.json: scipy 1.18.1, scikit-image 0.26.0, lazy_loader 0.6, fft-conv-pytorch 1.2.0, SimpleITK 2.5.6, pandas 3.0.6, connected-components-3d 4.1.0, numba 0.67.0, llvmlite 0.49.0. They are needed by the official train/augmentation imports (cc3d), which hv-ink-freeze.txt does not list. |
| threads | OMP_NUM_THREADS=MKL_NUM_THREADS=4; torch intra 4, interop 1; deterministic algorithms on |

## 2. Code (sha256)

These files are byte-identical copies of `tools/sib/trainer/` at commit 8475920fa1a8dd7a753c426be0ebd592851ad884, checked
against `git show` of that commit.

| file | sha256 |
|---|---|
| d2_train.py | fdbe236cc2cf46664c3d0558e58c7594220a4ce105fde3b5453d634680496f24 |
| d2_data.py | 5b7a6a5df4f07cf75ef84b63899e531c040b0cb13d8b45b7c180ac2b10a7676b |
| ckpt_shards.py | ba6db9991e14000b9ba051244c6ae2fa59928b4c6094cc64316ca559cbf3b974 |
| contam_check.py | 0e30cabbc762979f5b197c0365815dc5915048626c6a01ffb571c643b9f1321e |
| bench_throughput.py | a30101ccbd05b7cb6d4fc862301ea57ce3d46d183f8f466ebc01ab0e942b5181 |
| runlog.sh | 44805ecfe195bc3cd08d0139bbb3a9d2ebcbf2de880f97150b4674c64b715b2c |
| tests_ref/sib_trainer_units_test.py | f4f8046173403f36edc16c3e938f4bdfa912ddd696dc253cd0d6063068405346 |
| tests_ref/sib_trainer_integration_test.py | 162a48a7754c3a867854f0ffe06d47ffa6ec4679ab41939e6301d80b493df4b6 |

These files were written by this session:

| file | sha256 |
|---|---|
| rl.sh (run logger) | 3fa986a2b0b85eeb3c1361caf5d5f3ecbb70ac2f41b8dc0890794e36d9e250d3 |
| rev_pairing_check.py | b34d33ff12b0d30df99d1025d4a9b801be93f1bd9a60a84c17032ae6d865e8b0 |
| smoke.sh | 71b983319eedf6427b838197d913134624b759d36cb4f2ae9ead6c3d99eae386 |

Newer trainer commit: `origin/claude/gifted-bell-gavnl5-sib-trainer` is now at 08d7e42.
- It adds `--data-root`, a `blockpairs` loader and `pair_freeze.py`, plus a guard that refuses any network remote for resume shards (the DECL-OFFLOAD-1 ruling).
- The d2_train.py diff leaves sampling, REV reversal, the step and the resume state unchanged.
- This session still runs the pinned 8475920 copy. It changes only if the orchestrator names another commit.
- Under 8475920, Phase 2 never passes `--remote-ref`. Resume states stay local under /work.

## 3. Base checkpoint

- Checkpoint: ink_9um hybrid_3d2d seed42 step-075000.
- Source: HF scrollprize/ink_9um, revision 7109667e2607db1b90c37c8b09cb876ea7fe7bb1, path `hybrid_3d2d-seed42/step-075000.pth`.
- Local copy: /work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth, 138,360,039 bytes.
- sha256 e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab: **VERIFIED** with `sha256sum -c`. The trainer re-checks it on every start.

## 4. Tests

The tests were run on the pinned commit's tree, extracted with `git archive`.
- Unit: `tests/sib_trainer_units_test.py`, **14 passed**.
- Integration: `tests/sib_trainer_integration_test.py`, **12 passed** in 22 min 26 s.
  - It covers determinism (P128, P384 NULL micro-batched, P384 REV stitched), P384/NULL/REV paired sampling, subtile coverage and seed sensitivity.
  - It covers local and remote-shard resume, bitwise. The remote there is a local bare repo in a temp dir, so nothing went to the network.
  - It covers D3 equivalence (CTRL, FA, NULLA, REVA) and bf16 refusal without a gate.
- The first attempts failed before the D3 pylib was installed (`ModuleNotFoundError: cc3d`, and `scipy` for contam_check). Both are logged.

## 5. Synthetic smoke of this arm (logs/sib/d2-rev/smoke.json, sha256 53b7ca46cba4d0fd0b3a102dac92dab0236df07261b8b44748fd05d0a9ba7c5b)

Data: `d2_data.write_synthetic_registry(n=40, size=546, seed=11, shard_n=20)`, registry sha256 2f1607d6...346c.
S 546 = ceil(384 sqrt2)+2, so rotations are corner-free.

Config: `make-config --arm REV --seed 1 --batch 32 --micro-batch 4 --steps 10 --rot24 --subtile --threads 4 --z-jitter 2
--z-centre-offset 0 --lr 2e-5 --weight-decay 3e-5 --forward full --precision fp32 --hash-sources --log-every 1
--ckpt-every 5`. The resulting config sha256 is 343e7118267ef2773ccd49c61b337670b62de8b2adfadcd081cd13923d170e48.

| Measure | Result |
|---|---|
| steps / finite losses | 10 / 10; loss 0.6245 -> 0.5120 (monotone) |
| **median s/step** | **147.78 s** (range 145.6-151.0; batch 32 = 8 x 4, full 384 px forward, fp32, 4 threads) |
| **peak RSS** | **9.10 GiB** (9,542,768 kB) for the uninterrupted run; 9.37 GiB for the resumed process |
| resume state | 414,961,596 bytes, saved in 0.28 s (local only) |
| model_final | 138,362,143 bytes, kept local (/work/sib/d2rev_smoke), never pushed |
| trainer check | `rev_syn_exact_depth_reverse: true` |

### 5a. Save and resume (DECL-D3-A2 item 4 style)

- **U** ran 10 steps uninterrupted.
- **I** used the same config, was killed with `--die-after 7` (exit 99), and resumed from the local step-5 state, logged as `resume from_step 5 source local`.
- **All 10 losses were bitwise equal, and the final weights sha256 matched: U = I = 02f4c02cd575d230fc707835c1fe7225f930f0c21069f53edc5c85d032d7209a. PASS.**

### 5b. REV = P384 on depth-reversed stacks, paired with P384 (rev_pairing_check.py; 2 steps, batch 32 = 8 x micro 4)

Three separate processes ran the pinned trainer unchanged:
- **A** = P384 on R;
- **B** = REV on R;
- **C** = P384 on R, with every stack depth-reversed by the check script itself (independently of the trainer's REV code).

The P384 and REV configs differ only in `arm` and `rev` (config sha256: P384 c022249b...afbf2, REV 3df8355f...5959).

| per step (both steps) | result |
|---|---|
| model input x, B == C bitwise, all 8 micro-batches | true |
| x, B != A, all micro-batches (the reversal is applied) | true |
| ink labels and supervision masks equal in A, B, C | true |
| python / numpy / torch global RNG, sampling and rotation generators equal in A, B, C after each draw | true |
| drawn (patch, z offset, rotation) lists and the trainer's sample_digest equal in A, B, C | true |
| loss and grad norm, B == C bitwise | true |

**PASS.** REV sees exactly P384's patch, z-jitter, rotation and augmentation sequence, and differs only by the depth order of its inputs.

Caveat: bitwise identity holds only within one way of running the trainer, not across two.
- The same entrypoint reproduces bitwise: U vs I across 3 processes, and B vs C.
- The in-process check and the CLI give the same step-1 loss and grad norm bitwise, but at step 2 they differ by about 4e-8 relative (0.57154854387 vs 0.57154856622).
- The config fields that differ (steps, ckpt interval, pinned source hash) do not enter the maths; the official optimizer ignores num_iterations.
- The drift is therefore fp32 CPU kernel non-reproducibility between process setups, below the fp32 noise floor.
- The paired draw sequence is unaffected.

## 6. Throughput and wall time on this host

12,000 steps x 147.8 s = 492.6 h = **20.5 days** per arm-seed. This is fp32, full forward, batch 32 = 8 x 4, and excludes checkpoint time and restarts.

The trainer session's proposal measured 103.98 s/step for fp32 full on an AMX host. This host has no AMX and is about 42 % slower.

## 7. Phase-2 plan (only after GO D2; the recipe is whatever is declared, never changed here)

1. Fetch the named pair-freeze shards and verify every sha256 against the freeze record.
2. Build the config with `make-config --arm REV --seed 1` and the declared flags, sources and allowlists (`--hash-sources`).
   Record the config sha256 before step 1, and check that the declared recipe is identical to P384 apart from `arm` and `rev`.
3. Launch `nohup d2_train.py train --config cfg.json --out /work/d2/REV_s1` with a harness-tracked waiter.
   - Resume state every 250 steps, local only; no `--remote-ref`.
   - Losses go to logs/sib/d2-rev/train_log.jsonl every 50 steps: mean loss, grad norm, lr, s/step.
   - Logs are pushed hourly. Weights stay local.
4. At the end, record the model_final sha256 and write summary.json and REPORT.md, then stop.
