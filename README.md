<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="First Letters pilot and helper lane: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# First Letters pilot and helper lane

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-fl-pilot` · First Letters push · 2026-09-30..2026-10-01 · status **STOPPED** · verdict **VOID**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0490A, PHercParis4.

## Question

Pilot for the DECL-FL-1 First Letters screen (an inventory of eligible volumes with organizer segments); the session later served as a helper for Paris 4 map production and as an FL-4 lane on PHerc0490A inner windings.

## Method

tools/sib/fl-pilot/flp.py: anonymous S3 inventory of the eligible volumes, selection of up to 3 volumes with organizer tifxyz, render, 2 x 2 cm tiling. Then Paris 4 own-model maps on assigned tiles under the DECL-P4-25 helper briefs (each helper first reproduces a reference tile byte for byte), verso/forward maps (DECL-P4-26-A2), and the DECL-FL-4-A1 kit on PHerc0490A (lane 14 of 16): 100-generation grow, C2-NT render, GP TimeSformer variant B in both directions, tiles.

## What ran on this branch

2026-09-30: the inventory step started and was superseded after a container restart (no inventory output on the branch). 2026-09-30/10-01: helper maps pushed under s1maps_*/, verso/ and fwd_x/. The FL-2 second-worker run on PHerc1218 was not launched (blocked by the session's permission rule). 2026-10-01 17:40-19:36Z: FL-4 PHerc0490A, 2 segments grown (0 self-intersections), 1 with GP passes in both directions; then the usage limit stopped the fleet.

## Outcome

No result from the pilot itself. The PHerc0490A FL-4 outputs were never read (DECL-FL-4-A3 limited reading to PHerc0268), and DECL-FL-4-A5 later found every FL-4 grow was data-independent and cut across windings, so they carry no evidence. The helper maps fed the orchestrator's Paris 4 work; those results are on the research log.

| key number | meaning | file on this branch |
|---|---|---|
| 11.665503918481923 | cm2 area of the finished FL-4 grow (the same full square every FL-4 grow reached; DECL-FL-4-A5) | `logs/sib/fl-pilot/fl4/PHerc0490A/STATUS.md` |
| 2 | GP variant B tiles (forward + reverse) of the one finished FL-4 segment | `logs/sib/fl-pilot/fl4/PHerc0490A/pherc0490a_fl-pilot_i14/tiles_gp_B/manifest.json` |
| 490a98f9491e1180274ed3a0c0a9c611d73a0109c0e0c0fbba1097562a972488 | GP TimeSformer model sha256 verified at strict load | `logs/sib/fl-pilot/fl4/PHerc0490A/env.txt` |

## Where the records are

- `logs/sib/fl-pilot/STATUS.md`
- `logs/sib/fl-pilot/fl4/PHerc0490A/`
- `logs/sib/fl-pilot/s1maps_O/`
- `logs/sib/fl-pilot/s1maps_P/`
- `logs/sib/fl-pilot/s1maps_Q/`
- `logs/sib/fl-pilot/verso/`
- `tools/sib/fl-pilot/`

## Lesson

A grow gate of area plus zero self-intersections passes data-independent growth; check that a grown surface follows the sheet before spending compute on it.

## Related

- claude/gifted-bell-gavnl5 (research log)
- sib-fl-pherc0257 (FL-2 template)
- DECL-FL-1
- DECL-FL-2
- DECL-P4-25-A10-A1
- DECL-P4-25-A14
- DECL-P4-25-A16
- DECL-P4-26-A2
- DECL-FL-4-A1
- DECL-FL-4-A3
- DECL-FL-4-A5

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
bash tools/sib/fl-pilot/pipeline.sh
bash tools/sib/fl-pilot/fl4/run.sh
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
