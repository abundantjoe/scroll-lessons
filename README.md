<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-OWN fold arm F3 worker: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-OWN fold arm F3 worker

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-own-f3` · own-model and null experiments · 2026-09-27..2026-09-27 · status **STOOD-DOWN** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

This worker was to train P4-OWN fold arm F3, predict its 24 held-out tiles in order and compute the held-out pixel AUC (DECL-P4-23 item 6(a)).

## Method

The plan was to follow own-lead's frozen RECIPE.md (6b5bdc5) and WORKER.md: check out the ckpt-screen-b reader, copy the p4-excl inputs (archive 7ea9f34), run the environment tests and build_patches --verify, then train --arm F3, infer the 24 held-out tiles and run auc.py.

## What ran on this branch

On 2026-09-27 the branch was created from 6b5bdc5 and the RECIPE.md sha256 was verified. At about 13:15Z the permission classifier denied the reader checkout ('Untrusted Code Integration'). At 14:25Z it also denied the merge of the base branch that carried the same reader files ('Auto-Mode Bypass'). Neither was bypassed. No data build, training, maps or numbers were produced.

## Outcome

The orchestrator stood the lane down at 17:54Z (owner decision), and own-lead ran arm F3. Its held-out pixel AUC was 0.9401, recorded in logs/sib/own-f3/heldout_auc.json on branch claude/gifted-bell-gavnl5-sib-own-lead.

| key number | meaning | file on this branch |
|---|---|---|
| 377784c2bd8dd8617f38ae0e054fbe37684004f6e0d105852e84e16c16a6dfb8 | RECIPE.md sha256, verified equal to RECIPE.md.sha256 | `logs/sib/own-f3/ASK.md` |
| 2 | permission denials (checkout, then merge); not routed around | `logs/sib/own-f3/ASK.md` |

## Where the records are

- `logs/sib/own-f3/STATUS.md`
- `logs/sib/own-f3/ASK.md`
- `logs/sib/own-f3/RESUME.md`

## Lesson

Shared code should be committed into the recipe branch with its hashes, not checked out from another branch at run time.

## Related

- sib-own-lead
- sib-ckpt-screen-b
- sib-p4-excl
- sib-own-f1
- sib-own-f2
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
OWN_WORK=/work/own /opt/ckb/bin/python tools/sib/own-lead/train.py --arm F3 --data /work/own/data --recipe logs/sib/own-lead/p4own/recipe.json --out /work/own/arm_F3
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
