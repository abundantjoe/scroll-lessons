<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="AMX bf16 speed and equivalence gate: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# AMX bf16 speed and equivalence gate

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-amx` · ink-model training and checkpoint screening · 2026-09-25..2026-09-26 · status **COMPLETED** · verdict **FAILED**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md).

## Question

How much does Intel AMX bf16 (and int8) speed up CPU inference and training of the official 9 um base ink model? Would bf16 ink maps be equivalent enough to fp32 maps to replace them?

## Method

Benchmarked the sha256-verified official base checkpoint (scrollprize/ink_9um seed42 step-075000) in fp32 and in CPU bf16 autocast, at 1-4 threads, with and without channels_last, on random inputs only. Also profiled per-module time and FLOPs, tried three int8 routes, and prototyped a frozen-encoder cached-feature path. Built an equivalence gate (tools/sib/amx/amx_gate.py with unit tests), ran the full official inference chain in fp32 and bf16 on a random volume as a forecast, and drafted DECL-AMX-1.

## What ran on this branch

Ran on 2026-09-25 (18:20-19:31Z) on a 4-vCPU AMX Xeon container: two passes of a 24-row speed grid (5 warm-up and 20 timed iterations each), int8 feasibility, a per-module profile, cached-feature equivalence on 16 random tiles, a precision ablation on 32 random tiles, and a full-chain smoke on a synthetic 21 x 640 x 640 volume. No scroll data was read. The same session then started DEV-loop recipe R1, a frozen-encoder letter-context model (logs/sib/devloop-r1/). Its code and tests were built on synthetic data only, and at initialisation it was bitwise equal to the official CLI.

## Outcome

AMX kernels are used. At 4 threads bf16 gives a 1.60-1.74x inference speed-up and a 1.83-2.06x training-step speed-up. int8 is not feasible in the pinned environment. On synthetic input the bf16 maps reach Pearson 0.99943/0.99910, but only 98.18 %/97.72 % of pixels are within +-2 grey levels, so they fail the proposed 99.9 % bar. The orchestrator therefore declared DECL-AMX-1 for training parity only and kept every ink map in fp32. No bf16 training-parity (P16) result is on this branch. The devloop-r1 follow-on stayed blocked, waiting for training shards and an evaluation path (STATUS: not done). A later P4-O assignment to this session (DECL-P4-14-A1/A2) left nothing on this branch.

| key number | meaning | file on this branch |
|---|---|---|
| 1.60-1.74x | bf16 vs fp32 inference speed-up, batch 4, 4 threads, over two passes | `logs/sib/amx/REPORT.md` |
| 1.83-2.06x | bf16 vs fp32 full training-step speed-up, batch 8, D3 recipe, 4 threads | `logs/sib/amx/REPORT.md` |
| 98.18 % / 97.72 % | pixels within +-2 grey levels, bf16 vs fp32 official chain on a synthetic volume (forward/reverse); bar 99.9 %, gate verdict FAIL | `logs/sib/amx/synth_chain_gate.json` |
| 0.99943 / 0.99910 | Pearson, bf16 vs fp32 map on the synthetic chain (forward/reverse) | `logs/sib/amx/REPORT.md` |
| 55 % | share of fp32 inference time spent in the 3-D stem, which holds 24 % of FLOPs | `logs/sib/amx/profile_split.json` |
| 14.6x / 13.3x | decoder-only cached-feature training step vs full step (fp32 / bf16); cached output bitwise equal to the full model (max \|diff\| 0) | `logs/sib/amx/cache_path.json` |
| 0 Linear modules | dynamic int8 quantization is a no-op; FX and PT2E routes failed | `logs/sib/amx/int8_feas.json` |
| 12 passed | unit tests of the equivalence gate | `logs/sib/amx/out/pytest_gate.log` |

## Where the records are

- `logs/sib/amx/REPORT.md`
- `logs/sib/amx/report.json`
- `logs/sib/amx/summary.json`
- `logs/sib/amx/bench_grid.jsonl`
- `logs/sib/amx/bench_grid_rep.jsonl`
- `logs/sib/amx/synth_chain_gate.json`
- `logs/sib/amx/precision_ablation.json`
- `logs/sib/amx/profile_split.json`
- `logs/sib/amx/cache_path.json`
- `logs/sib/amx/int8_feas.json`
- `logs/sib/amx/ASK.md`
- `logs/sib/amx/proposals/decl_amx_1.txt`
- `logs/sib/amx/runs.jsonl`
- `logs/sib/devloop-r1/ASK.md`
- `logs/sib/devloop-r1/runs.jsonl`
- `tools/sib/amx/`
- `tools/sib/devloop-r1/`

## Lesson

A Pearson of 0.999 can hide a failing per-pixel tolerance, so a precision change for ink maps has to be gated on the pixel bar.

## Related

- sib-chain2um
- sib-devloop
- sib-pairs0139
- DECL-AMX-1
- DECL-D3-A1
- DECL-D3-A2
- DECL-C3
- DECL-P4-14-A1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
tools/sib/amx/run_grid.sh
cd tools/sib/amx && /opt/hv-ink/bin/python profile_split.py --threads 4 --out ../../../logs/sib/amx/profile_split.json
cd tools/sib/amx && /opt/hv-ink/bin/python cache_path.py --threads 4 --out ../../../logs/sib/amx/cache_path.json
cd tools/sib/amx && /opt/hv-ink/bin/python int8_feas.py --threads 4 --out ../../../logs/sib/amx/int8_feas.json
/opt/hv-ink/bin/python tools/sib/amx/synth_chain.py logs/sib/amx/synth_chain_gate.json
cd tools/sib/amx && /opt/hv-ink/bin/python precision_ablation.py ../../../logs/sib/amx/precision_ablation.json
source /opt/hv/bin/activate && PYTHONPATH=src pytest -q tests/sib_amx_test_gate.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
