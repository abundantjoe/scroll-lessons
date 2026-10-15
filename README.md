<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-F 2.4 um control screen (sub-lane): Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-F 2.4 um control screen (sub-lane)

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-highz-c2` · PARIS-4 investigations · 2026-09-26..2026-09-26 · status **COMPLETED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

As a sub-sibling of p4-highz, run the pre-registered P4-F per-tile numeric screen (stage B) on the 2.4 um known-text control strip, so the parent finishes in about half the time.

## Method

The lane waited for the parent's frozen 2.4 um thresholds, merged them, and ran the parent's stage_b.py unchanged on every control tile. Numbers only. Checkpoints were pushed every 30 tiles. Tools, thresholds and protocol were not modified.

## What ran on this branch

2026-09-26, 18:39Z to 21:42Z: 171 control tiles (171 unique), process exited normally, 0 error lines in the log, no restarts.

## Outcome

Done, 171/171. The parent also finished the last 20 tiles itself, believing this run had stopped at 151. In all 171 records, the two runs agree in every field except wall-clock time. The parent's P4-F result (0 dense hotspots) is therefore consistent with this branch.

| key number | meaning | file on this branch |
|---|---|---|
| 171/171 | control tiles screened | `logs/sib/p4-highz-c2/stage_b_C2.jsonl` |
| 0 | error or traceback lines in the run log | `logs/sib/p4-highz-c2/STATUS.md` |

## Where the records are

- `logs/sib/p4-highz-c2/STATUS.md`
- `logs/sib/p4-highz-c2/stage_b_C2.jsonl`
- `logs/sib/p4-highz-c2/stage_b_c2.log`

## Lesson

A frozen, deterministic tool let two independent runs of the same control be checked record by record.

## Related

- sib-p4-highz
- DECL-P4-6
- DECL-P4-6-A1
- DECL-P4-6-A2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
pip install numpy requests opencv-python-headless tifffile scipy pillow
mkdir -p /tmp/hz && python3 tools/sib/p4-highz/stage_b.py /tmp/hz "$PWD" tiles C2 > /tmp/hz/stage_b_c2.log 2>&1
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
