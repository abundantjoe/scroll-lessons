<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-OWN fold arm F1 worker: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-OWN fold arm F1 worker

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-own-f1` · own-model and null experiments · 2026-09-27..2026-09-27 · status **STOOD-DOWN** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

This worker was to train P4-OWN fold arm F1 (two of the three contiguous training-tile groups), predict its 24 held-out tiles in the declared order and report the held-out pixel AUC (DECL-P4-23 item 6(a)).

## Method

The plan was to follow own-lead's frozen RECIPE.md (commit 6b5bdc5) and WORKER.md. That meant importing the shared ckpt-screen-b reader (code 98cd075), building the environment and passing test_own.py, rebuilding and verifying the 4000-patch data set, then train.py --arm F1, infer.py on the held-out list and auc.py.

## What ran on this branch

On 2026-09-27 the branch was created at 6b5bdc5 and the RECIPE sha256 was verified. At about 13:13Z the session's permission classifier denied the setup step, a checkout of tools/sib/ckpt-screen-b/ from 98cd075 ('Untrusted Code Integration'). The worker did not route around the denial. It also declined the relayed RECIPE-A1 checkout and a merge-based unblock (14:22Z), because only the owner could approve them. No environment, data build, training or prediction ran.

## Outcome

The orchestrator stood the lane down at 17:54Z (owner decision), and own-lead ran arm F1 itself. That run's held-out pixel AUC was 0.9418, recorded on branch claude/gifted-bell-gavnl5-sib-own-lead in logs/sib/own-f1/heldout_auc.json. This branch holds only the ASK, RESUME and STATUS notes.

| key number | meaning | file on this branch |
|---|---|---|
| 6b5bdc5 | branch base, the frozen RECIPE commit; RECIPE sha256 verified | `logs/sib/own-f1/RESUME.md` |
| 1 | setup step denied by the session permission classifier; not routed around | `logs/sib/own-f1/ASK.md` |
| dfc9ea1 | last work commit; nothing merged, checked out or run beyond the base | `logs/sib/own-f1/STATUS.md` |

## Where the records are

- `logs/sib/own-f1/STATUS.md`
- `logs/sib/own-f1/ASK.md`
- `logs/sib/own-f1/RESUME.md`

## Lesson

Workers that must run code imported from another branch need that permission granted before dispatch; otherwise the lead ends up running every arm itself.

## Related

- sib-own-lead
- sib-ckpt-screen-b
- sib-p4-excl
- sib-own-f2
- sib-own-f3
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
OWN_WORK=/work/own /opt/ckb/bin/python tools/sib/own-lead/train.py --arm F1 --data /work/own/data --recipe logs/sib/own-lead/p4own/recipe.json --out /work/own/arm_F1
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
