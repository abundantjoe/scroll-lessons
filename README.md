<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-OWN own ink model: coordination and arms: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-OWN own ink model: coordination and arms

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-own-lead` · own-model and null experiments · 2026-09-27..2026-10-01 · status **COMPLETED** · verdict **PASSED**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Can a CNN trained from scratch on Paris 4's own labelled 2.4 um papyrus detect this scroll's ink? The training excludes a held-out zone X and a 1.2 mm 3-D margin around it. The model has to pass held-out folds, a label-derangement NULL and the G1 blind-legibility gate before any X map is interpreted.

## Method

The model is a 3-D-to-2-D CNN with 232,697 parameters, random init and no pretrained weights. Its input is slices 23-84 of the organizer 2.4 um surface volume, and it was trained with masked BCE + Dice at output stride 4 on organizer ink labels mapped onto the certified training zone T (certified by p4-excl). The recipe was frozen and hashed before any training step (RECIPE.md, commit 6b5bdc5; METRIC-HASH-45). Seven arms: three contiguous-group folds F1-F3, three seeds S1-S3 on all of T, and a NULL with spatially deranged labels. Held-out pixel AUC uses Mann-Whitney, and the remote harness ran the G1 blind census on the F-arm held-out tiles.

## What ran on this branch

Work ran from 2026-09-27 to 2026-10-01 on 4-vCPU CPU containers. Steps: tools with synthetic tests (ALL OK), a CPU timing test, a feasibility check and a 4000-patch build (17.04 GB), then the recipe freeze. The six sub-worker sessions were blocked by permission denials, so own-lead trained all seven arms itself, 2500 steps each, finishing by 2026-09-28. It predicted 24 held-out tiles per fold plus the NULL's held-out maps, and made S-arm and NULL maps of zone X. Later it made further S1 maps for declared census batches (DECL-P4-25 amendments) and verso-mode S1 maps for the DECL-P4-26-A2 offset channel. 45 of its 80 assigned verso maps were pushed by the last commit.

## Outcome

P4-OWN was feasible (45,262 ink cells against a bar of 2000). Held-out pixel AUC was F1 0.9418, F2 0.9415 and F3 0.9401. The label-deranged NULL scored 0.4972 / 0.5074 / 0.5240 on the same pixels. S1 reached pixel AUC 0.978 pooled on 6 organizer-labelled known-text tiles inside the never-trained zone X (research log, own-model S1 held-out AUC entry). The G1 legibility gate passed in both variants (sigma2t 46/72 = 63.9 %, block 58/72 = 80.6 %, bar 30 %; research log P4-OWN-G1-RESULT), so P4-OWN was declared informative. Census results from these maps are recorded in the research log, not on this branch.

| key number | meaning | file on this branch |
|---|---|---|
| 45,262 | labelled 64-px cells with >= 2 % ink in T (feasibility bar 2000) | `logs/sib/own-lead/p4own/feasibility.json` |
| 4000 patches, 17,039,468,032 bytes | training patch build fixed in the frozen recipe | `logs/sib/own-lead/p4own/recipe_final.json` |
| 377784c2bd8dd8617f38ae0e054fbe37684004f6e0d105852e84e16c16a6dfb8 | sha256 of the frozen RECIPE.md, pushed before any training step | `logs/sib/own-lead/p4own/RECIPE.md.sha256` |
| 0.9418 | F1 held-out pixel AUC | `logs/sib/own-f1/heldout_auc.json` |
| 0.9415 | F2 held-out pixel AUC | `logs/sib/own-f2/heldout_auc.json` |
| 0.9401 | F3 held-out pixel AUC | `logs/sib/own-f3/heldout_auc.json` |
| 0.4972 / 0.5074 / 0.5240 | NULL (label-deranged) pixel AUC on the F1 / F2 / F3 held-out pixels | `logs/sib/own-null/heldout_auc_F1.json`, `heldout_auc_F2.json`, `heldout_auc_F3.json` |
| 0.563 | S1 final training loss after 2500 steps | `logs/sib/own-lead/STATUS.md` |
| 232,697 | model parameters (cfg A, random init) | `logs/sib/own-lead/p4own/RECIPE.md` |

## Where the records are

- `logs/sib/own-lead/STATUS.md`
- `logs/sib/own-lead/SUBSIBS.md`
- `logs/sib/own-lead/p4own/RECIPE.md`
- `logs/sib/own-lead/p4own/recipe_final.json`
- `logs/sib/own-lead/p4own/feasibility.json`
- `logs/sib/own-lead/p4own/timing.json`
- `logs/sib/own-f1/heldout_auc.json`
- `logs/sib/own-f2/heldout_auc.json`
- `logs/sib/own-f3/heldout_auc.json`
- `logs/sib/own-null/`
- `logs/sib/own-s1/`
- `logs/sib/own-s2/`
- `logs/sib/own-s3/`
- `tools/sib/own-lead/`

## Lesson

A recipe hashed before training, held-out folds and a label-derangement NULL near AUC 0.5 together made the 0.94 held-out AUC and the G1 pass auditable before any target map was read.

## Related

- sib-own-f1
- sib-own-f2
- sib-own-f3
- sib-own-s2
- sib-own-s3
- sib-own-null
- sib-p4-excl
- sib-ckpt-screen-b
- sib-rh-e1
- DECL-P4-23
- DECL-P4-23-A1
- DECL-P4-23-A2
- DECL-P4-26-A2
- METRIC-HASH-45
- P4-OWN-G1-RESULT

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
# from logs/sib/own-lead/RESUME.md and p4own/WORKER.md (ckpt-screen-b reader from 98cd075 is not committed on this branch)
git checkout 98cd075 -- tools/sib/ckpt-screen-b/ && git reset -q tools/sib/ckpt-screen-b
(cd tools/sib/own-lead && OWN_WORK=/work/own/test /opt/ckb/bin/python test_own.py)
OWN_WORK=/work/own /opt/ckb/bin/python tools/sib/own-lead/build_patches.py --excl /work/own/excl --out /work/own/data --patch 256 --core 192 --max-patches 4000 --verify logs/sib/own-lead/p4own/build_manifest.json
setsid nohup /opt/ckb/bin/python tools/sib/own-lead/run_arms.py --train-threads 2 --pred-threads 2 >> /work/own/run_arms.log 2>&1 < /dev/null &
# after any container restart: setsid nohup tools/sib/own-lead/watchdog.sh >> /work/own/watchdog.log 2>&1 < /dev/null &
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
