<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-OWN label-derangement NULL worker: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-OWN label-derangement NULL worker

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-own-null` · own-model and null experiments · 2026-09-27..2026-09-27 · status **STOOD-DOWN** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

This worker was to train the P4-OWN NULL arm, which is the S1 recipe with label shards spatially deranged between patches. It would predict the same maps as the S arms and the F-arm held-out pixels, so that DECL-P4-23 items 6(a) and 6(d) have a hallucination and chance control.

## Method

The plan was to follow own-lead's frozen RECIPE.md (6b5bdc5) and WORKER.md: set up the ckpt-screen-b reader, copy the p4-excl inputs and pass the environment tests, then build the data, train --arm NULL with the fixed derangement (no fixed point), run four prediction runs and run auc.py on each fold's held-out pixels.

## What ran on this branch

On 2026-09-27 the branch was created at 6b5bdc5 and the RECIPE.md sha256 was verified. The permission classifier denied the order's setup command ('Untrusted Code Integration'), and the worker did not route around it. It did not apply the RECIPE-A1 checkout (13:15Z) or the orchestrator's merge-based unblock (14:23Z), treating both as the same denied outcome. Nothing was built, trained or predicted.

## Outcome

The orchestrator stood the lane down at 17:54Z (owner decision), and own-lead ran the NULL arm (2500 steps, deranged labels). Its held-out pixel AUC was 0.4972 / 0.5074 / 0.5240 on the F1 / F2 / F3 pixels, recorded in logs/sib/own-null/heldout_auc_F{1,2,3}.json on branch claude/gifted-bell-gavnl5-sib-own-lead. That is chance level, as a deranged-label control should be.

| key number | meaning | file on this branch |
|---|---|---|
| 377784c2bd8dd8617f38ae0e054fbe37684004f6e0d105852e84e16c16a6dfb8 | RECIPE.md sha256, verified equal to RECIPE.md.sha256 | `logs/sib/own-null/ASK.md` |
| 1 | setup command denied by the session permission classifier; not routed around | `logs/sib/own-null/ASK.md` |
| 4 | prediction runs the arm would have made (col. -1 arrays, two map runs, held-out maps) | `logs/sib/own-null/RESUME.md` |

## Where the records are

- `logs/sib/own-null/STATUS.md`
- `logs/sib/own-null/ASK.md`
- `logs/sib/own-null/RESUME.md`

## Lesson

A NULL arm is only useful if it actually runs; when the dedicated worker was blocked, the lead had to run the control too.

## Related

- sib-own-lead
- sib-ckpt-screen-b
- sib-p4-excl
- DECL-P4-23
- METRIC-HASH-45
- P4-OWN-G1-RESULT

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
# from logs/sib/own-lead/p4own/WORKER.md at 6b5bdc5; the first command is the step the permission classifier denied
git checkout 98cd075 -- tools/sib/ckpt-screen-b/ && git reset -q tools/sib/ckpt-screen-b
sha256sum logs/sib/own-lead/p4own/RECIPE.md   # must equal RECIPE.md.sha256
(cd tools/sib/own-lead && OWN_WORK=/work/own/test /opt/ckb/bin/python test_own.py)   # must end ALL OK
OWN_WORK=/work/own /opt/ckb/bin/python tools/sib/own-lead/train.py --arm NULL --data /work/own/data --recipe logs/sib/own-lead/p4own/recipe.json --out /work/own/arm_NULL
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
