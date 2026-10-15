<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="First Letters worker: PHerc0306B: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# First Letters worker: PHerc0306B

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-fl-pherc0306b` · First Letters push · 2026-09-30..2026-10-02 · status **STOPPED** · verdict **VOID**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0306B, PHerc0268, PHercParis4.

## Question

Can the DECL-FL-1/-2 First Letters screen find 10 letters within 4 cm2 on PHerc0306B from grown or organizer segments and the official ink model? From DECL-FL-4-A1 the session became an FL-4 lane on PHerc0268.

## Method

Worker of the DECL-FL-1/-2 First Letters screen (pipeline template from sib-fl-pherc0257 at 54b29c96): VC3D auto-grow on the organizer surface prediction (kept iff 0 self-intersections and >= 16 cm2), C2-NT render (31 layers), the official ink_9um step-075000 model in both directions, 2 x 2 cm tiles with manifests; reading was central and blind. The lane added its own numbers-only surface check (surfcheck.py, surfshift.py): fraction of mesh vertices on the surface prediction, and the same at normal offsets as an off-sheet control. From DECL-FL-4-A1 it ran the FL-4 kit as a PHerc0268 inner-winding lane (100-generation grows, C2-NT render, organizer-hosted 2023 Grand Prize TimeSformer variant B in both directions).

## What ran on this branch

FL-1 (2026-09-30): 0 accepted segments (growth lost to container restarts). Paris 4 helper maps (first batch, 2026-09-30). FL-2 primary (2026-10-01): surface check SURFACE_CHECK.json at 02:40Z, HOLD on census use; 16 tiles of 2 segments pushed before the hold; a round-2 retry with the organizer normal grids and a support gate rejected 3 of 3 grows, 0 tiles; stopped by DECL-FL-4-A1. FL-4 PHerc0268 lane 6: 7 grows kept and 1 rejected (141 self-intersections); all 7 renders failed on a full disk; after freeing disk, one segment got GP forward and reverse passes (2026-10-02); one more of its seeds was computed by the orchestrator's local runner (FL4-W48). The fleet stopped at about 08:00Z on 2026-10-02.

## Outcome

The lane's own check voided its FL-2 material: the template's grows (no normal_grid_path) do not follow the surface prediction (on-mesh support equal to off-sheet support, every patch at the geometric maximum area), and a retry with normal grids gave no admissible segment. It named the cause that DECL-FL-4-A5/-A6 confirmed for all FL-4 grows a day later. The central census still read 8 PHerc0306B tiles in wave 1 and 4 windows in FL3-W1: 0 positives, uninformative (gate NOT SENSITIVE). This lane's PHerc0268 FL-4 outputs were read in the FL4 fleet waves (W41/W45/W47; 43 PHerc0268 items read in all, 0 positives) and were then declared VOID by DECL-FL-4-A5.

| key number | meaning | file on this branch |
|---|---|---|
| 0.227 | fraction of segment s0 vertices on the surface prediction (>= 128) | `logs/sib/fl-pherc0306b/fl2/SURFACE_CHECK.json` |
| 0.167 vs 0.233 | prediction support at normal offset 0 vs 16 vox for s0 (no peak at 0: FAIL) | `logs/sib/fl-pherc0306b/fl2/SURFACE_CHECK.json` |
| 3 of 3 | round-2 normal-grid grows rejected (0 tiles kept) | `logs/sib/fl-pherc0306b/fl2/STATUS.md` |
| 7 of 7 | FL-4 renders on 2026-10-01 that failed on 'No space left on device' | `logs/sib/fl-pherc0306b/fl4/PHerc0268/STATUS.md` |

## Where the records are

- `logs/sib/fl-pherc0306b/STATUS.md`
- `logs/sib/fl-pherc0306b/fl2/SURFACE_CHECK.json`
- `logs/sib/fl-pherc0306b/fl2/`
- `logs/sib/fl-pherc0306b/fl4/PHerc0268/`
- `tools/sib/fl-pherc0306b/`

## Lesson

Area and self-intersection gates pass a smooth free surface; a support test with an off-sheet control is what showed the grows were not following the papyrus.

## Related

- claude/gifted-bell-gavnl5 (research log)
- fl4t
- sib-fl-pherc0257 (FL-2 template)
- DECL-FL-1
- DECL-FL-2
- FL2-WAVE1-RESULT
- DECL-FL-3
- FL3-W1-RESULT
- DECL-FL-4-A1
- DECL-FL-4-A2
- DECL-FL-4-A4-A2
- DECL-FL-4-A4-A2-E4
- FL4-W48-RESULT
- DECL-FL-4-A5
- DECL-FL-4-A6
- DECL-FL-5
- DECL-P4-25-A10-A1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
setsid nohup bash tools/sib/fl-pherc0306b/fl2/watchdog.sh >/dev/null 2>&1 &
python3 tools/sib/fl-pherc0306b/fl2/surfcheck.py ...
python3 tools/sib/fl-pherc0306b/fl2/surfshift.py ...
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
