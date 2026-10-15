<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="D2 trainer build and tests: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# D2 trainer build and tests

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-trainer` · ink-model training and checkpoint screening · 2026-09-25..2026-09-30 · status **TOOL** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0814.

## Question

Build the D2 (TRAIN-1) trainer: arm presets P128/P384/NULL/REV, determinism, paired sampling, a 3-D patch registry for contamination checks, and reclaim-safe resume. Then measure CPU throughput and propose the D2 amendment.

## Method

d2_train.py generalises the D3 trainer on official villa 41701aa components and always starts from the base ink_9um seed42 step-075000 checkpoint, which it checks by sha256. It has data adapters for every pair layout, the DECL-D2 label rule, a NULL derangement, REV depth reversal, rotations, subtiling, and bf16 refused unless an AMX gate passes. Supporting tools are resume-state sharding, contamination checks and a pair-freeze tool. The tests prove bitwise D3 equivalence, determinism, paired sampling and bitwise resume. A throughput matrix and a DECL-D2-A1 proposal with an ASK list fed the orchestrator.

## What ran on this branch

From 2026-09-25 18:43Z to 2026-09-26 05:35Z on a 4-vCPU AMX host: test suites, a throughput benchmark on synthetic data, a remote-shard push and fetch test, full-convolution and parameter-diff checks, and pair-freeze dry runs on real PHerc0814 pair-registry metadata (no training). On 2026-09-30 the session wrote a First Letters pass-2 pipeline on another scroll; it was not launched, because the safety check refused a detached self-pushing loop.

## Outcome

The trainer was delivered and tested (26/26, later 29/29), and the D2 arms copied it. It never trained on real data, because D2 never received its amendment or GO and is recorded as blocked for lack of a GPU. Throughput set the CPU cost: P128 about 1.7 days and P384 about 14.4 days per 12,000-step arm at fp32. After the Q6 ruling, the trainer refuses any network remote for weights. The session's delete of its test ckpt ref was refused by the safety check and was left for the owner or orchestrator. The pairs0814 stage-C dry run matched 564 patches with 0 label mismatches.

| key number | meaning | file on this branch |
|---|---|---|
| 26 passed, later 29 passed | trainer unit + integration suite (pytest_all_2, then pytest_all_3 after the Q6 guard) | `logs/sib/trainer/REPORT.md` |
| 11.94 s/step (1.66 d) | P128 fp32 median step and projected 12,000-step time on the AMX host (bf16 6.79 s/step) | `logs/sib/trainer/throughput.json` |
| 103.98 s/step (14.4 d) | P384 fp32 full-forward median step and projected 12,000-step time (bf16 64.11 s/step) | `logs/sib/trainer/throughput.json` |
| 414,952,758 bytes | full resume state (weights + AdamW + RNG) in 5 shards; save + push + prune 90.3 s | `logs/sib/trainer/REPORT.md` |
| 564 patches, 0 mismatches | real pairs0814 stage-C union dry run (180/180 file hashes) | `logs/sib/trainer/REPORT.md` |
| 146 keys | state keys that differ between the base 128-config build and a 384-config build | `logs/sib/trainer/param_diff_384.json` |

## Where the records are

- `logs/sib/trainer/REPORT.md`
- `logs/sib/trainer/report.json`
- `logs/sib/trainer/ASK.md`
- `logs/sib/trainer/throughput.json`
- `logs/sib/trainer/proposals/decl_d2_a1.txt`
- `logs/sib/trainer/PAIR_FREEZE_SPEC.md`
- `logs/sib/trainer/DATA_INTERFACE.md`
- `logs/sib/trainer/full_conv_check.json`
- `logs/sib/trainer/param_diff_384.json`
- `logs/sib/trainer/freeze_dryrun_u0814/`
- `logs/sib/fl2-pherc1218/STATUS.md`
- `tools/sib/trainer/`

## Lesson

Weights pushed to git as force-pushed orphans leave large unreachable objects and need a cleanup path; the later ruling refused network remotes for weights altogether.

## Related

- sib-trainer-ckpt
- sib-d2-p128
- sib-d2-p384
- sib-d2-null
- sib-d2-rev
- sib-amx
- sib-pairs0814
- sib-pairs0139
- DECL-D2
- DECL-D2-A1 (proposal, never declared)
- DECL-AMX-1
- DECL-OFFLOAD-1
- CORR-RETRACE-RULE

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
/opt/hv-ink/bin/python -m pytest -q tests/sib_trainer_units_test.py tests/sib_trainer_integration_test.py
/opt/hv-ink/bin/python tools/sib/trainer/bench_throughput.py --steps 3 --with-512
/opt/hv-ink/bin/python tools/sib/trainer/param_diff_384.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
