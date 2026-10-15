<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Iteration-4 tile worker s2 (screen C): Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Iteration-4 tile worker s2 (screen C)

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-ckpt-screen-c-s2` · ink-model training and checkpoint screening · 2026-09-27..2026-09-28 · status **STOPPED** · verdict **UNKNOWN**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

This is a worker for the ckpt-screen-c P4-O run. Its job was to compute an assigned subset of PHerc.1667-iteration-4 tiles on the PHercParis4 surface volume with the pinned builder.

## Method

Ran tools/sib/ckpt-screen-c/p4o_run.py around ckpt-screen-b's builder at 98cd075, with file hashes pinned and the checkpoint sha256-verified. Precision was fp32, final because the parent's bf16 check failed. Each finished tile was pushed for the parent to merge, and interrupted tiles resumed from 15-min checkpoints.

## What ran on this branch

Spawned 2026-09-27 01:08Z. Three tiles were completed on 2026-09-27. One of them restarted from scratch after its process died with no checkpoint, and was relaunched with the parent's updated driver at 18:59Z. A fourth tile was in progress at the last commit (21:11Z). The session was archived on 2026-09-28 08:00Z, not by the parent.

## Outcome

This branch holds 3 fp32 iteration-4 tiles, which the parent merged into its interim manifest. No stage read of iteration-4 is recorded, so the material's outcome is unknown.

| key number | meaning | file on this branch |
|---|---|---|
| 3 | fp32 iteration-4 tiles produced on this branch | `logs/sib/ckpt-screen-c-s2/RESUME.md` |
| a1612b1f... | verified sha256 prefix of the iteration-4 model.safetensors | `logs/sib/ckpt-screen-c-s2/RESUME.md` |

## Where the records are

- `logs/sib/ckpt-screen-c-s2/RESUME.md`
- `logs/sib/ckpt-screen-c-s2/PHerc.1667-iteration-4/`

## Lesson

A tile with no surviving checkpoint costs its full runtime again, so the checkpoint interval bounds the loss from a container restart.

## Related

- sib-ckpt-screen-c
- sib-ckpt-screen-c-s1
- sib-ckpt-screen-c-s3
- sib-ckpt-screen-b
- DECL-P4-14
- DECL-P4-14-A2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
/opt/hv-ink/bin/python tools/sib/ckpt-screen-c/p4o_run.py (see logs/sib/ckpt-screen-c-s2/RESUME.md)
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
