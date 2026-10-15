<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Remote sealed-read harness E2: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Remote sealed-read harness E2

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-rh-e2` · geometry, reading calibration, tools and records · 2026-09-26..2026-09-30 · status **COMPLETED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4, PHerc0826.

## Question

Run sealed blind reads of PHercParis4 census material (first E2: raw 2.4 um CT tiles built by pairs0814b) in a sibling container under DECL-REMOTE-HARNESS-1, with every reader session auditable.

## Method

The same protocol as rh-e1, with tools pinned by hash:
- normalise the manifest, then build the keys, N0 null tiles and jobs;
- COMMIT A before any reader;
- fresh Opus readers whose prompt is exactly the brief, with answers age-encrypted to the orchestrator's key;
- transcript audit, then COMMIT B.

A void session gets exactly one re-run under its pre-committed brief, and the re-run is disclosed. The harness never decrypts or scores.

## What ran on this branch

2026-09-26 to 2026-09-30: 12 batches with 199 reader jobs (200 audited attempts, counting one void attempt that was re-run once): the E2 census (20 sessions over 160 tiles), the L2 census (3 + 17 sessions) and 9 further PHercParis4 census batches (159 sessions), whose names and results are withheld under the release's confidentiality rule.

The last order (2026-09-30), an FL-1 PHerc0826 pipeline, was blocked at launch.

## Outcome

199 of 200 audited sessions were VALID. The one void attempt was a reader killed by an API rate limit before any tool call; it was re-run once under its pre-committed brief, and the re-run was valid. Three sessions sealed their answer but lost the final DONE reply to the rate limit; they were disclosed and kept. Scoring was the orchestrator's (research log). The session's permission check denied the FL-1 PHerc0826 launch, and the lane did not work around it. It recorded that PHerc0826 has no organizer segments on the bucket.

| key number | meaning | file on this branch |
|---|---|---|
| 20/20 | E2 census sessions audited VALID (160 tiles, 0 violations, 0 re-runs) | `logs/sib/rh-e2/B/audit.json` |
| 200 | reader sessions audited across 12 batches (199 valid plus 1 void attempt re-run once) | `logs/sib/rh-e2/STATUS.md` |
| 1 | void session re-run once under its committed brief | `logs/sib/rh-e2/STATUS.md` |

## Where the records are

- `logs/sib/rh-e2/STATUS.md`
- `logs/sib/rh-e2/RESUME.md`
- `logs/sib/rh-e2/ASK.md`
- `logs/sib/orders/rh-e2.txt`
- `logs/sib/rh-e2/A/`
- `logs/sib/rh-e2/B/audit.json`
- `logs/sib/rh-e2/L2/`

## Lesson

A session lost to a rate limit gets one disclosed re-run under its committed brief; a second re-run would mean choosing between sealed answers.

## Related

- sib-rh-e1
- sib-pairs0814b
- sib-tribunal
- DECL-REMOTE-HARNESS-1
- DECL-P4-5
- DECL-P4-12
- DECL-FL-1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/sib/rh-e2/commit_a.py <A_dir> <batch> <null_batch> <jobs_batch> <builder_branch> <builder_commit> <manifest> <tiles_dir> <norm_manifest_json> <variant>
python tools/sib/rh-e2/audit_e2.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
