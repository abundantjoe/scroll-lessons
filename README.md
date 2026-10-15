<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Dense-pigment offset sweep, worker 1: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Dense-pigment offset sweep, worker 1

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-hzw1` · PARIS-4 investigations · 2026-09-27..2026-09-27 · status **COMPLETED** · verdict **NULL**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Does the raw 2.4 um Paris 4 CT show a dense (high-Z, mineral-pigment) deposit at any depth within +-60 um of the mesh on the E2 material? This worker computed one share of the tiles for that screen.

## Method

The lane ran p4-highz's frozen DECL-P4-6 numeric screen code unchanged: stage_off.py at commit 3e3a5ba with the frozen T_hi threshold from thresholds_2p4.json. A wrapper (tools/sib/hzw1/run_cols.py) only filters the tiles down to this worker's column block. Each tile was scored at 9 offsets from -60 to +60 um in 15 um steps, and the per-tile, per-offset records were pushed. p4-highz then aggregated them with screen_off.py against a Bonferroni bar built from 171 control tiles. No screen or verdict is computed on this branch.

## What ran on this branch

On 2026-09-27 the sweep covered 40 eligible E2 tiles at 9 offsets each. The first run stopped at 7/40 when a usage-limit pause restarted the container; it resumed at 05:57Z, skipped the finished tiles and completed at 06:24Z (EXIT 0). A second task (DECL-P4-14-A4) then started one PHerc.1667-iteration-5 P4-O tile with ckpt-screen-b's WORKER.md pipeline (code 98cd075) at 06:44Z. That run was killed about 13 min in, at 06:57Z.

## Outcome

All 40 tiles finished at all 9 offsets, and the offset-0 records matched p4-highz's stage_b_E2.jsonl exactly (40/40). The pooled E2 screen (160 tiles from p4-highz, hzw1 and hzw2) found 0 DENSE-HOTSPOT tiles at all 9 offsets (research log P4-F-SWEEP-RESULT). That closes the mineral-pigment route at CT-detectable thicknesses. The second task was stopped under P4-O-STAGE-O2S1-RESULT after iteration-5 failed its known-text gate 0/3, and it left no tile output.

| key number | meaning | file on this branch |
|---|---|---|
| 40/40 tiles x 9 offsets | E2 tiles of this worker's share completed at offsets -60..+60 um (15 um steps) | `logs/sib/hzw1/STATUS.md` |
| 40/40 exact | offset-0 records equal to p4-highz stage_b_E2.jsonl (n_hi, stroke, acf, acf_rot90) | `logs/sib/hzw1/STATUS.md` |
| 40 | per-tile records (each with 9 offsets) in the pushed sweep file | `logs/sib/hzw1/off_E2_hzw1.jsonl` |
| ~13 min of ~4 h | run time of the P4-O iteration-5 tile (task 2) before it was killed; no tile output | `logs/sib/hzw1/STATUS.md` |

## Where the records are

- `logs/sib/hzw1/off_E2_hzw1.jsonl`
- `logs/sib/hzw1/STATUS.md`
- `logs/sib/hzw1/RESUME.md`
- `tools/sib/hzw1/run_cols.py`
- `tools/sib/hzw1/regress0.py`
- `logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5/run_563.log`

## Lesson

Splitting a frozen screen across workers with a tile filter only, and checking the offset-0 records exactly against the parent's own records, kept the merged sweep consistent.

## Related

- sib-p4-highz
- sib-hzw2
- sib-ckpt-screen-b
- DECL-P4-6-A3
- DECL-P4-6-A4
- DECL-P4-14-A4
- P4-F-SWEEP-RESULT
- P4-O-STAGE-O2S1-RESULT

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
git fetch origin claude/gifted-bell-gavnl5-sib-p4-highz claude/gifted-bell-gavnl5-sib-pairs0814b claude/gifted-bell-gavnl5-sib-p4-tiles-b
pip install opencv-python-headless tifffile
git worktree add --detach <scr>/hzrepo 3e3a5ba
python3 tools/sib/hzw1/run_cols.py <scr>/hzrepo <scr>/hz E2 <COL_FROM> <COL_TO> -60,-45,-30,-15,0,15,30,45,60
python3 tools/sib/hzw1/regress0.py <scr>/hzrepo <scr>/hz
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
