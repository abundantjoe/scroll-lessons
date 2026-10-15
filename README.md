<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-OWN seed arm S2 worker: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-OWN seed arm S2 worker

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-own-s2` · own-model and null experiments · 2026-09-27..2026-09-27 · status **STOOD-DOWN** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

This worker was to train P4-OWN seed arm S2 (all of the training zone T, seed 20260928) and predict the exclusion-zone tiles in the declared order. That is the second of three seeds needed for the seed-agreement rule.

## Method

The plan was to follow own-lead's frozen RECIPE.md (6b5bdc5) and WORKER.md: set up the ckpt-screen-b reader, apply RECIPE-A1 (lazy shard loader in train.py), pass test_own.py and build_patches --verify, then train --arm S2 and make three inference runs, with npz arrays for the known-text check tiles.

## What ran on this branch

On 2026-09-27 the worker fetched the branches, verified the RECIPE sha256, installed the environment and copied the p4-excl inputs (8 files, 7.1M). It verified read-only that the base branch carries reader files with the expected sha256. The permission classifier denied the reader checkout ('Untrusted Code Integration'). The worker did not merge the base branch or apply RECIPE-A1, since the denial covers bringing that code in by any route. No tests, data build, training or maps.

## Outcome

The orchestrator stood the lane down at 17:54Z (owner decision), and own-lead trained arm S2 itself (seed 20260928, finished 2026-09-28). The S2 records and maps are on branch claude/gifted-bell-gavnl5-sib-own-lead under logs/sib/own-s2/. No weights or maps exist on this branch.

| key number | meaning | file on this branch |
|---|---|---|
| 377784c2...6dfb8 | RECIPE.md sha256, checked OK with sha256sum -c | `logs/sib/own-s2/RESUME.md` |
| 8 files, 7.1M | p4-excl inputs (7ea9f34) copied before the block | `logs/sib/own-s2/RESUME.md` |
| 9a8ad9b2e83191fb42cb423db4b0e4e35cd213921ba1578db760d5b879c31c56 | expected train.py sha256 under RECIPE-A1 (not applied) | `logs/sib/own-s2/RESUME.md` |

## Where the records are

- `logs/sib/own-s2/STATUS.md`
- `logs/sib/own-s2/ASK.md`
- `logs/sib/own-s2/RESUME.md`

## Lesson

Checking hashes read-only lets a blocked worker confirm its inputs without crossing a permission boundary.

## Related

- sib-own-lead
- sib-own-s3
- sib-ckpt-screen-b
- sib-p4-excl
- DECL-P4-23
- METRIC-HASH-45
- METRIC-HASH-46
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
OWN_WORK=/work/own /opt/ckb/bin/python tools/sib/own-lead/train.py --arm S2 --data /work/own/data --recipe logs/sib/own-lead/p4own/recipe.json --out /work/own/arm_S2
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
