<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Remote sealed-read harness E1: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Remote sealed-read harness E1

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-rh-e1` · geometry, reading calibration, tools and records · 2026-09-26..2026-10-02 · status **COMPLETED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4, PHerc0800, PHerc0268.

## Question

Run sealed blind reads of PHercParis4 census material in a sibling container under DECL-REMOTE-HARNESS-1, so that the orchestrator's disk and context stay free and every reader session can be audited.

## Method

Each batch follows the same steps:
1. Normalise the builder's manifest with the hash-pinned tools, then build the keys, the N0 null tiles and the jobs.
2. Push COMMIT A (the keys' sha256, briefs, image manifest and builder ref) before any reader starts.
3. Run fresh Opus readers whose prompt is exactly the brief. They write age-encrypted answers to the orchestrator's key.
4. Audit each transcript: only the listed images were read, prompt == brief, and the sealed output exists.
5. Push COMMIT B with the sealed answers, transcripts and audit.

The harness never decrypts or scores.

## What ran on this branch

2026-09-26 to 2026-09-30: batches E1 (8 readers), M2a (8), F1 (8), L2S a and b (6 + 15), W1 block windows (2), OWN_F1 (6) and OWN_F2/F3 (12), for 65 reader sessions in all. Later orders:
- own-model map helper passes;
- an FL-2 PHerc0800 pipeline (complete on 2026-10-01);
- an FL-4 PHerc0268 lane, whose record ends mid-run on 2026-10-02 at 07:30Z.

## Outcome

Every audited session was VALID in every batch: 0 violations, 0 unread images, prompt == brief and 0 re-runs. Decryption and scoring were the orchestrator's and are recorded in the research log, not on this branch. Two tool-input mismatches came up: a missing coverage field and a partial last session. Both were raised as ASKs and fixed by declared tool changes, not by editing the inputs.

| key number | meaning | file on this branch |
|---|---|---|
| 65 | reader sessions run and audited VALID across 8 batches | `logs/sib/rh-e1/STATUS.md` |
| 8/8 | E1 sessions audited VALID with 0 violations | `logs/sib/rh-e1/B/audit.json` |
| 60 | eligible E1 census tiles after the declared coverage rule | `logs/sib/rh-e1/STATUS.md` |

## Where the records are

- `logs/sib/rh-e1/STATUS.md`
- `logs/sib/rh-e1/ASK.md`
- `logs/sib/orders/rh-e1.txt`
- `logs/sib/rh-e1/A/`
- `logs/sib/rh-e1/B/audit.json`
- `logs/sib/rh-e1/M2a/`
- `logs/sib/rh-e1/F1/`
- `logs/sib/rh-e1/L2S/`
- `logs/sib/rh-e1/L2Sb/`
- `logs/sib/rh-e1/W1/`
- `logs/sib/rh-e1/OWN_F1/`
- `logs/sib/rh-e1/fl2/STATUS.md`
- `logs/sib/rh-e1/fl4/PHerc0268/STATUS.md`

## Lesson

Commit the keys and briefs before any reader starts, and never let the harness see the answers.

## Related

- sib-rh-e2
- sib-tribunal
- DECL-REMOTE-HARNESS-1
- DECL-HARNESS-A1
- DECL-P4-4
- DECL-P4-5
- DECL-P4-6
- DECL-P4-12-A2
- DECL-P4-23

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/sib/rh-e1/rh.py commit_a <tag> <out_dir> <builder_ref> <key_batch> <jobs_batch>
python tools/sib/rh-e1/rh.py audit <jobs_batch> <out_dir> <subagent_dir>
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
