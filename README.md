<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Dense-pigment offset sweep, worker 2: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Dense-pigment offset sweep, worker 2

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-hzw2` · PARIS-4 investigations · 2026-09-27..2026-09-27 · status **COMPLETED** · verdict **NULL**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Does the raw 2.4 um Paris 4 CT show a dense (high-Z, mineral-pigment) deposit at any depth within +-60 um of the mesh on the E2 material? This worker computed the second share of the tiles for that screen.

## Method

The lane ran p4-highz's stage_off.py unchanged at commit 3e3a5ba with the frozen T_hi threshold. A wrapper (tools/sib/hzw2/run_off.py) only filters the eligible E2 tiles down to this worker's column block. Records were computed at 9 offsets (-60..+60 um, o_slices = round(o/2.4)) in the off_*.jsonl format and handed to p4-highz, which aggregates them with screen_off.py against the Bonferroni control bar. No screen or verdict is computed on this branch.

## What ran on this branch

On 2026-09-27 the sweep covered 48 E2 tiles (rows 0-7 of the assigned block) at 9 offsets each. A container pause interrupted the run at 03:09Z after 31 tiles, with all records intact. It resumed at 05:53Z, skipped the finished tiles and was done by 06:05Z. A second task (DECL-P4-14-A4) started one PHerc.1667-iteration-5 P4-O tile at 06:44Z with ckpt-screen-b code 98cd075. It was killed at about 12 min, at 06:56Z.

## Outcome

All 48 tiles finished at all 9 offsets. The record keys are identical to the control file, and the sheet slabs per offset match it. The pooled E2 screen (160 tiles) found 0 DENSE-HOTSPOT tiles at all 9 offsets (research log P4-F-SWEEP-RESULT), which closes the mineral-pigment route at CT-detectable thicknesses. The P4-O tile was stopped under P4-O-STAGE-O2S1-RESULT (iteration-5 known-text gate 0/3 FAIL). No tile output exists.

| key number | meaning | file on this branch |
|---|---|---|
| 48/48 tiles x 9 offsets | E2 tiles of this worker's share completed at offsets -60..+60 um | `logs/sib/hzw2/STATUS.md` |
| c88f781a1930f426242dafaca6cf7e4063b9427c56612c3f4697669fbd88ca83 | sha256 of the pushed sweep records file | `logs/sib/hzw2/STATUS.md` |
| 31 | tiles done before the container pause; all records intact, resumed without recomputation | `logs/sib/hzw2/STATUS.md` |
| ~12 min | run time of the P4-O iteration-5 tile (task 2) before it was killed; no output | `logs/sib/hzw2/STATUS.md` |

## Where the records are

- `logs/sib/hzw2/off_E2_hzw2.jsonl`
- `logs/sib/hzw2/STATUS.md`
- `logs/sib/hzw2/RESUME.md`
- `tools/sib/hzw2/run_off.py`

## Lesson

Resumable per-tile records let a container pause cost no recomputation: the run restarted and skipped the 31 tiles it had already finished.

## Related

- sib-p4-highz
- sib-hzw1
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
git worktree add --detach /home/user/hzcode 3e3a5ba
pip install opencv-python-headless tifffile
python3 tools/sib/hzw2/run_off.py /home/user/hzcode /home/user/hzw2scr -60,-45,-30,-15,0,15,30,45,60
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
