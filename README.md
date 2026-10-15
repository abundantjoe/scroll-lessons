<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-OWN seed arm S3 worker: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-OWN seed arm S3 worker

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-own-s3` · own-model and null experiments · 2026-09-27..2026-09-27 · status **STOOD-DOWN** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

This worker was to train P4-OWN seed arm S3 (all of the training zone T, seed 20260929) and predict the exclusion-zone tiles in the declared order. That is the third seed for the seed-agreement rule.

## Method

The plan was to follow own-lead's frozen RECIPE.md (6b5bdc5) and WORKER.md: check out the ckpt-screen-b reader, copy the p4-excl inputs, pass the WORKER.md section 2 tests and build_patches --verify, then train --arm S3, make three inference runs and push the train/ files.

## What ran on this branch

On 2026-09-27 the worker fetched the branches and verified the RECIPE.md sha256. The permission classifier denied the combined setup command ('Untrusted Code Integration'), and at about 14:30Z also the merge of the base branch ('Auto-Mode Bypass'). Neither was retried. It verified read-only that the base branch's reader files are byte-identical to 98cd075. No data build, training or maps.

## Outcome

The orchestrator stood the lane down at 17:54Z (owner decision), and own-lead trained arm S3 itself (seed 20260929; its summary is dated 2026-09-28T18:32Z). The S3 records are on branch claude/gifted-bell-gavnl5-sib-own-lead under logs/sib/own-s3/. No numbers were produced on this branch.

| key number | meaning | file on this branch |
|---|---|---|
| 377784c2bd8dd8617f38ae0e054fbe37684004f6e0d105852e84e16c16a6dfb8 | RECIPE.md sha256, matching RECIPE.md.sha256 | `logs/sib/own-s3/ASK.md` |
| 2 | permission denials (setup checkout, then merge); not bypassed | `logs/sib/own-s3/ASK.md` |

## Where the records are

- `logs/sib/own-s3/STATUS.md`
- `logs/sib/own-s3/ASK.md`
- `logs/sib/own-s3/RESUME.md`

## Lesson

A relayed note from another agent is not owner approval; the blocked worker correctly waited, and the lead carried the arm.

## Related

- sib-own-lead
- sib-own-s2
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
OWN_WORK=/work/own /opt/ckb/bin/python tools/sib/own-lead/train.py --arm S3 --data /work/own/data --recipe logs/sib/own-lead/p4own/recipe.json --out /work/own/arm_S3
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
