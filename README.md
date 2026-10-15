<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Labelled-adjacency flags + helper jobs: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Labelled-adjacency flags + helper jobs

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-excl` · PARIS-4 investigations · 2026-09-26..2026-10-01 · status **COMPLETED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4, PHerc0826, PHerc0490A.

## Question

Which Paris 4 census tiles lie within 1.2 mm of the organizers' labelled (known-ink) segments and so must be flagged as labelled-adjacent (DECL-P4-2 item 1, DECL-P4-4 item 2)? The lane later served as a helper for label certification, own-model map jobs and First Letters segment growth.

## Method

Exact point-to-triangulated-surface distances from every tile's mesh points to the official meshes of the 8 labelled segments. A KD-tree search with a covering bound makes this exact without densification. A fail-closed all-vertex check was added, and tiles under 1.2 mm were flagged. Only mesh coordinates, metadata and hashes were used. Later jobs: certification of training-label shards (DECL-P4-23); a pixel-AUC check of own-model arms against organizer labels with a label-deranged null; frozen-code own-model inference maps with reproducibility gates (DECL-P4-25-A10/-A14/-A16, DECL-P4-26-A2); and First Letters auto-grown segments (DECL-FL-2).

## What ran on this branch

2026-09-26 to 2026-10-01: flags for four tile sets (160, 171, 106 and 100 tiles) with 21/21 synthetic tests; 229 label shards; own-model map PNGs (s1maps_O/P/Q, verso, fwd_x); 4 grown PHerc0826 segments (about 31.13 cm2 each, 32 official tiles); then 1 grown PHerc0490A segment (11.665 cm2, 0 self-intersections) with 1 tile, where the record ends.

## Outcome

The flags are final: 120/160 and 139/171 tiles on the two 2.4 um strips, and 106/106 and 100/100 on the two 1 um prediction strips. The all-vertex pass changed one flag that the sampled points had missed. Own-model arms S1 and S2 reach pooled pixel AUC 0.9781 and 0.9769 against organizer labels, versus 0.5335 for the label-deranged null. Map reproducibility gates passed with identical PNG sha256; one stale-checkpoint PASS was disclosed and replaced by a fresh recompute. The PHerc0826 seed list was capped at 8 by the template logic (ASK). This lane makes no hypothesis verdict of its own.

| key number | meaning | file on this branch |
|---|---|---|
| 120 of 160 | labelled-adjacent tiles on the inner 2.4 um strip | `logs/sib/p4-excl/excl_a.json` |
| 139 of 171 | labelled-adjacent tiles on the known-text 2.4 um strip | `logs/sib/p4-excl/excl_b.json` |
| 21/21 | synthetic distance tests passed (batched, per-point and brute force agree) | `logs/sib/p4-excl/tests.json` |
| 0.9781 | pooled pixel AUC of own-model arm S1 against organizer labels | `logs/sib/p4-excl/p4own/colm1_auc_S1.json` |
| 0.5335 | pooled pixel AUC of the label-deranged null | `logs/sib/p4-excl/p4own/colm1_auc_NULL.json` |
| 4 segments / 32 tiles | PHerc0826 First Letters segments grown and official tiles made | `logs/sib/p4-excl/fl2/STATUS.md` |
| 11.665 cm2 | area of the single PHerc0490A segment grown before the record ends | `logs/sib/p4-excl/fl4/PHerc0490A/grow/pherc0490a_p4-excl_i11.json` |

## Where the records are

- `logs/sib/p4-excl/REPORT.md`
- `logs/sib/p4-excl/STATUS.md`
- `logs/sib/p4-excl/RESUME.md`
- `logs/sib/p4-excl/ASK.md`
- `logs/sib/p4-excl/excl_a.json`
- `logs/sib/p4-excl/excl_b.json`
- `logs/sib/p4-excl/excl_d_a.json`
- `logs/sib/p4-excl/excl_d_b.json`
- `logs/sib/p4-excl/label_fractions.json`
- `logs/sib/p4-excl/p4own/`
- `logs/sib/p4-excl/fl2/`
- `logs/sib/p4-excl/fl4/PHerc0490A/`
- `tools/sib/p4-excl/`

## Lesson

A fail-closed check over every mesh vertex caught a labelled-adjacent tile that a 4096-point sample had missed.

## Related

- DECL-P4-2
- DECL-P4-4
- DECL-P4-21
- DECL-P4-23
- DECL-P4-25-A10
- DECL-P4-25-A14
- DECL-P4-25-A16
- DECL-P4-26-A2
- DECL-FL-2
- sib-p4-tiles-a
- sib-p4-tiles-b
- sib-p4-layout

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python3 tools/sib/p4-excl/test_surfdist.py
bash tools/sib/p4-excl/fetch.sh <out_mesh_dir>
python3 tools/sib/p4-excl/build.py <src_mesh_dir> <struct_dir>
python3 tools/sib/p4-excl/process.py <strip a|b> <npz> <commit> <blob> <struct_dir> <out_json> [<strip_mesh_dir> <grid_json>]
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
