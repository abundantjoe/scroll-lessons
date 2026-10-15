<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Offload archive of closed work folders: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Offload archive of closed work folders

**Dominion experiment branch** `claude/gifted-bell-gavnl5-data` · geometry, reading calibration, tools and records · 2026-09-25..2026-09-26 · status **ARCHIVE** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0841, PHerc0139.

## Question

Where do the bulky but regenerable outputs of finished steps go when the orchestrator's disk is nearly full and the owner has ruled out deleting anything? This branch is the dedicated offload store declared in DECL-OFFLOAD-1.

## Method

tools/offload/git_offload.py pushes each batch as one commit. The commit's tree holds only that batch plus BATCH.json, which lists every file's path, bytes and sha256, and each batch commit has the previous one as its parent. As a result the head tree shows only the newest batch (plus, since 2026-10-15, this README and its banner), and older batches live in history. The tool refuses key files, sealed answers, symlinks, files over 95 MB and raw CT.

## What ran on this branch

Four batches were pushed between 2026-09-25 and 2026-09-26. The first was a 1-file self-test (262461 bytes). The other three came from the closed-20260926T1747 folder: part -00 holds READ-CAL bank data (704 files, 1479821428 bytes); part -01 holds READ-CAL picker work, the C3 gate runs and early D1 files (333 files, 1503093646 bytes); part -02 holds the D1 work folder with renders, alignment gate, inference arrays and summaries (286 files, 408374184 bytes).

## Outcome

Archive only: no experiment ran on this branch. The head commit holds the D1 work folder (closed-20260926T1747-02/d1/), whose summary.json records the D1 build: the alignment gate, the maps and the text-order AUCs. The D1 verdict itself (FAIL) and the C3 and READ-CAL verdicts are recorded in the research log, not here.

| key number | meaning | file on this branch |
|---|---|---|
| 4 | offload batches pushed (self-test plus three closed-work parts) | `BATCH.json` |
| 286 files, 408374184 bytes | size of the head batch closed-20260926T1747-02 (D1 work) | `BATCH.json` |
| 3391551719 bytes | total bytes over all four batches (1324 files); the earlier batches are listed in the BATCH.json of the parent commits | `BATCH.json` of commits 899244af0, d15f21c72, ccbe66515 and 2444e884e (sum) |

## Where the records are

- `BATCH.json`
- `closed-20260926T1747-02/d1/work/summary.json`
- `closed-20260926T1747-02/d1/work/gate.json`
- `closed-20260926T1747-02/d1/work/ledger.tsv`

## Lesson

A chained offload branch with per-file hashes lets finished work leave a full disk without anything being deleted.

## Related

- research-log
- DECL-OFFLOAD-1
- DECL-D1
- DECL-C3
- DECL-READCAL

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. This branch has its own history, unrelated to the research log, and had no README before this one.

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
