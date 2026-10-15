<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="D2 P384 arm trainer setup: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# D2 P384 arm trainer setup

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-d2-p384` · ink-model training and checkpoint screening · 2026-09-26..2026-09-26 · status **INCOMPLETE** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md).

## Question

Can the P384 arm of decision D2 (TRAIN-1, fold L-0841: 384 px tiles, seed 1) be set up to train reproducibly on CPU, and what does 'full' 384 px forward mean for the unchanged base model?

## Method

The session built a training-only environment, copied the pinned trainer (commit 8475920) byte-identically, verified the base checkpoint and ran the trainer suite. It then ran a 10-step synthetic P384 smoke with a hard-exit-and-resume test. It also measured the parameter difference between the base-config build and a build configured for 384 px patches, and checked pairing and hold-out handling against the pair-freeze spec on the later trainer commit.

## What ran on this branch

Phase 1 only, on 2026-09-26, on a 4-vCPU 2.10 GHz host with AMX present; the smoke ran at fp32. Synthetic data only (40 patches at 560 px). No real data, image or 0841 material was touched.

## Outcome

Phase 1 passed: 26 of 26 tests, identical per-step losses and bitwise-equal final weights after resume, 129.16 s/step. 'Full' P384 trains the unchanged 128-built model on 384 px tiles: a 384-configured build differs in 146 state keys and cannot load the base weights. The session found a fail-open path in the trainer: allow_ids is silently ignored for the 'pairs' and 'd3_pool' source kinds, so an allowlist of 34 of 40 synthetic patches loaded all 40. It recommended a guard to the trainer owner. Real training never started: no D2 amendment or GO D2 was issued, and D2 is recorded as blocked for lack of a GPU.

| key number | meaning | file on this branch |
|---|---|---|
| 129.16 s/step | median step time, P384 full forward, fp32, 4 threads, batch 32 (synthetic smoke) | `logs/sib/d2-p384/smoke_result.json` |
| 430.5 h (17.9 days) | projected loop time for 12,000 steps of one arm at fp32 in one session | `logs/sib/d2-p384/smoke_result.json` |
| 9.89 GB | peak RSS of smoke run A | `logs/sib/d2-p384/smoke_result.json` |
| 146 keys; 34,546,498 vs 47,871,298 params | difference between the base 128-config build and a 384-config build (strict load of base weights fails) | `logs/sib/d2-p384/param_diff.json` |
| 40 of 40 loaded | fail-open finding: an allowlist of 34 patches was ignored for kind 'pairs' | `logs/sib/d2-p384/pairing_check.json` |
| 26 passed | trainer unit and integration tests (14 + 12) | `logs/sib/d2-p384/READY.md` |

## Where the records are

- `logs/sib/d2-p384/READY.md`
- `logs/sib/d2-p384/smoke_result.json`
- `logs/sib/d2-p384/param_diff.json`
- `logs/sib/d2-p384/pairing_check.json`
- `logs/sib/d2-p384/cfg.json`
- `logs/sib/d2-p384/runs.jsonl`
- `tools/sib/d2-p384/`

## Lesson

Allowlists must fail closed: the trainer silently ignored allow_ids for some source kinds, and only an explicit synthetic test exposed it.

## Related

- sib-trainer
- sib-d2-p128
- sib-d2-null
- sib-d2-rev
- DECL-D2
- DECL-D2-A1 (proposal, never declared)
- DECL-D3-A1
- DECL-OFFLOAD-1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
bash tools/sib/d2-p384/setup_env_d2.sh
/opt/hv-ink/bin/python tools/sib/d2-p384/param_diff.py
bash tools/sib/d2-p384/smoke_p384.sh
/opt/hv-ink/bin/python tools/sib/d2-p384/pairing_check.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
