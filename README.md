<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="First Letters worker: PHerc1203: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# First Letters worker: PHerc1203

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-fl-pherc1203` · First Letters push · 2026-09-30..2026-10-02 · status **STOPPED** · verdict **VOID**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc1203, PHerc0268.

## Question

Can the DECL-FL-1/-2 First Letters screen find 10 letters within 4 cm2 on PHerc1203 from organizer segments and the official ink model? From DECL-FL-4-A1 the session was an FL-4 lane on PHerc0268.

## Method

DECL-FL-1 worker on organizer segments: select the organizer raw tifxyz (drop version snapshots and T0 tracer test ids), check each with vc_tifxyz_selfcross, render C2-NT (31 layers), run the official ink_9um step-075000 in both directions and tile at 2 x 2 cm (make_tiles.py). Under DECL-FL-4-A1 the session ran the FL-4 kit as a PHerc0268 inner-winding lane: 100-generation grows, C2-NT render, the organizer-hosted 2023 Grand Prize TimeSformer (variant B) in both directions, cover cells and one whole-segment window per direction.

## What ran on this branch

FL-1 (2026-09-30): organizer raw tifxyz used (22 dirs; 17 pass checks after excluding the 5 T0 tracer test ids); the 3 largest picked (16.10, 12.53 and 11.79 cm2), all 3 NOT clean by vc_tifxyz_selfcross; one render finished (193 s) and inference started; no tile was pushed. The Paris 4 helper task was not started (its tiles were reassigned, DECL-P4-25-A10-A2). No FL-2 output is on this branch. FL-4 PHerc0268 lane 13 (fresh session, 2026-10-02 06:04-07:59Z): 2 grows kept, 1 segment with GP forward and reverse passes; the keepalive stopped at the 2 h background limit and was not restarted.

## Outcome

No First Letters tile from this branch was read. This lane's PHerc0268 FL-4 outputs were read in the FL4 fleet waves (W41/W45/W47; 43 PHerc0268 items read in all, 0 positives) and were then declared VOID by DECL-FL-4-A5: every FL-4 grow was data-independent (no normal grids) and cut across windings.

| key number | meaning | file on this branch |
|---|---|---|
| 17 | PHerc1203 organizer raw segments passing checks (of 22; 5 T0 ids excluded) | `logs/sib/fl-pherc1203/NOTES.md` |
| 15927/19911 | transverse self-contacts (two triangulations) of the largest picked organizer segment | `logs/sib/fl-pherc1203/NOTES.md` |
| 8 | GP variant B cover entries (4 cells x 2 directions) of the finished FL-4 segment | `logs/sib/fl-pherc1203/fl4/PHerc0268/pherc0268_fl-pherc1203_i13/cover_gp_B/manifest.json` |

## Where the records are

- `logs/sib/fl-pherc1203/NOTES.md`
- `logs/sib/fl-pherc1203/STATUS.md`
- `logs/sib/fl-pherc1203/progress.log`
- `logs/sib/fl-pherc1203/fl4/PHerc0268/`
- `tools/sib/fl-pherc1203/`

## Lesson

Organizer segments are not automatically clean: check self-intersections before tiling, since a tile over a crossing may mix sheets.

## Related

- claude/gifted-bell-gavnl5 (research log)
- fl4t
- sib-census (second FL-2 worker for PHerc1203)
- DECL-FL-1
- DECL-FL-2
- DECL-FL-4-A1
- DECL-FL-4-A4-A2
- DECL-FL-4-A4-A2-E3
- DECL-FL-4-A4-A2-E4
- DECL-FL-4-A5
- DECL-P4-25-A10-A2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python3 tools/sib/fl-pherc1203/select_segments.py
bash tools/sib/fl-pherc1203/pipeline.sh
python3 tools/sib/fl-pherc1203/make_tiles.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
