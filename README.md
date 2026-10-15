<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="DEV recipe DIST-FT trainer: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# DEV recipe DIST-FT trainer

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-dev-distft` · ink-model training and checkpoint screening · 2026-09-26..2026-09-30 · status **INCOMPLETE** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0814, PHercParis4, PHerc0800.

## Question

Does a full fine-tune of the base 9 um ink model, distilled from the organizer 2.4 um maps with soft targets (DEV-LOOP recipe 3, DIST-FT, with NULL and REV controls), sharpen 9 um maps on the frozen DEV registry?

## Method

The session wrapped the pinned D2 trainer with a soft-target switch (target = reference / 255 on every pair-valid pixel, official loss unchanged). Paired DIST-FT, DIST-FT-NULL (fixed derangement, seed 20260925) and DIST-FT-REV arms were planned at 2500 steps each at batch 32, keeping only final-step weights and doing no checkpoint selection. Scoring was to use the frozen DEV-LOOP evaluator (sigma_eq), with training-pair hold-outs taken from the DEV registry. Real training was gated on a METRIC-HASH of the frozen DEV registry and evaluator plus 'GO DEV DIST-FT'.

## What ran on this branch

Phase 1 on 2026-09-26: 12 synthetic tests and a 20-step synthetic smoke per arm (fp32, 4 threads), plus a provisional hold-out count on PHerc0814 pair-registry metadata. From 2026-09-26 21:45Z the session was re-tasked to the P4-O cross-scroll checkpoint census (DECL-P4-14-A1): inference of the official PHerc.1667-iteration-2 checkpoint over 108 Paris 4 inference tiles. On 2026-09-30 it was re-tasked again to a First Letters pass-3 screen, which was only launched on this branch.

## Outcome

The DIST-FT gate never opened: the DEV-LOOP freeze and its METRIC-HASH were never recorded, so no real-data training step ran and there is no DEV result. The P4-O run lost its work to three container reclaims, produced 0 tiles and was stopped on 2026-09-30 without output. A within-tile resume tool (tested bitwise) remains on the branch. The provisional hold-out check dropped 121 of 564 gated PHerc0814 patches.

| key number | meaning | file on this branch |
|---|---|---|
| 12 passed | synthetic DIST-FT tests | `logs/sib/dev-distft/READY.md` |
| 0.628 -> 0.533 | DIST-FT synthetic smoke loss, step 1 to step 20 (16.66 s/step median); synthetic only, no ink information | `logs/sib/dev-distft/smoke/DIST-FT/summary.json` |
| 0.632 -> 0.569 | DIST-FT-NULL synthetic smoke loss over 20 steps (17.26 s/step median) | `logs/sib/dev-distft/smoke/DIST-FT-NULL/summary.json` |
| 121 dropped, 443 kept | provisional hold-out effect on the 564 gated PHerc0814 pair patches | `logs/sib/dev-distft/STATUS.md` |
| 0 of 108 | P4-O iteration-2 inference tiles produced before the task was stopped | `logs/sib/dev-distft/STATUS.md` |

## Where the records are

- `logs/sib/dev-distft/READY.md`
- `logs/sib/dev-distft/STATUS.md`
- `logs/sib/dev-distft/ASK.md`
- `logs/sib/dev-distft/RESUME.md`
- `logs/sib/dev-distft/smoke/`
- `logs/sib/dev-distft/holdout_check.json`
- `logs/sib/dev-distft/bench_ab.json`
- `logs/sib/dev-distft/p4o/iteration-2/`
- `logs/sib/fl3-pherc0800/STATUS.md`
- `tools/sib/dev-distft/`

## Lesson

Hours-long inference tiles on reclaimable containers need resume within a tile; resuming only at tile boundaries lost every tile to reclaims.

## Related

- sib-devloop
- sib-devloop2
- sib-dev-lcsoft
- sib-trainer
- sib-ckpt-screen-b
- DECL-DEVLOOP
- DECL-DEVLOOP-A1
- DECL-D2
- DECL-P4-14
- DECL-P4-14-A1
- DECL-P4-14-A2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
bash tools/sib/dev-distft/env/setup_env.sh
/opt/hv-ink/bin/python -m pytest -q -p no:cacheprovider --basetemp=/work/distft/pt tools/sib/dev-distft/tests/test_distft.py
/opt/hv-ink/bin/python tools/sib/dev-distft/distft.py synth --out /work/distft/smoke/syn --n 64 --size 384 --seed 7
/opt/hv-ink/bin/python tools/sib/dev-distft/distft.py make-config --arm DIST-FT --out /work/distft/smoke/DIST-FT.json --batch 32 --steps 20 --threads 4 --ckpt-every 10 --log-every 1 --subtile --source syn=pairs:/work/distft/smoke/syn
/opt/hv-ink/bin/python tools/sib/dev-distft/distft.py train --config /work/distft/smoke/DIST-FT.json --out /work/distft/smoke/run_DIST-FT
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
