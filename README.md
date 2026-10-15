<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-OWN fold arm F2 worker: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-OWN fold arm F2 worker

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-own-f2` · own-model and null experiments · 2026-09-27..2026-09-27 · status **STOOD-DOWN** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

This worker was to train P4-OWN fold arm F2, predict its 24 held-out tiles and compute the held-out pixel AUC (DECL-P4-23 item 6(a)).

## Method

The plan was to follow own-lead's frozen RECIPE.md (6b5bdc5) and WORKER.md: set up the ckpt-screen-b reader tools (98cd075), copy the p4-excl inputs, run the environment tests (ALL OK) and build_patches --verify, then train --arm F2, infer the 24 held-out tiles with one commit each, and run auc.py to produce heldout_auc.json.

## What ran on this branch

On 2026-09-27 the branch was set at 6b5bdc5 and the RECIPE.md sha256 matched. At 13:13Z the permission classifier denied the setup checkout ('Untrusted Code Integration'). At 14:23Z it also denied the orchestrator-suggested merge of the base branch ('Auto-Mode Bypass'). Neither was retried or circumvented, and nothing was built, trained or predicted.

## Outcome

The orchestrator stood the lane down at 17:54Z (owner decision), and own-lead ran arm F2. Its held-out pixel AUC was 0.9415, recorded in logs/sib/own-f2/heldout_auc.json on branch claude/gifted-bell-gavnl5-sib-own-lead. This branch holds only notes.

| key number | meaning | file on this branch |
|---|---|---|
| 377784c2...6dfb8 | RECIPE.md sha256, verified equal to RECIPE.md.sha256 | `logs/sib/own-f2/ASK.md` |
| 2 | permission denials (checkout, then merge); neither routed around | `logs/sib/own-f2/ASK.md` |
| 24 | held-out tiles the arm would have predicted | `logs/sib/own-f2/RESUME.md` |

## Where the records are

- `logs/sib/own-f2/STATUS.md`
- `logs/sib/own-f2/ASK.md`
- `logs/sib/own-f2/RESUME.md`

## Lesson

A permission denial blocks the outcome rather than one command, so rerouting through a merge was denied too; the fix had to come from the owner or a reassignment.

## Related

- sib-own-lead
- sib-ckpt-screen-b
- sib-p4-excl
- sib-own-f1
- sib-own-f3
- DECL-P4-23
- METRIC-HASH-45
- METRIC-HASH-47
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
OWN_WORK=/work/own /opt/ckb/bin/python tools/sib/own-lead/train.py --arm F2 --data /work/own/data --recipe logs/sib/own-lead/p4own/recipe.json --out /work/own/arm_F2
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
