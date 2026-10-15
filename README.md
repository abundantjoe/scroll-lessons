<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="First Letters worker: PHerc0846B: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# First Letters worker: PHerc0846B

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-fl-pherc0846b` · First Letters push · 2026-09-30..2026-10-01 · status **STOPPED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0846B, PHerc0490A.

## Question

Can the DECL-FL-1/-2 First Letters screen find 10 letters within 4 cm2 on PHerc0846B from grown or organizer segments and the official ink model? From DECL-FL-4-A1 the session became an FL-4 lane on PHerc0490A.

## Method

Worker of the DECL-FL-1/-2 First Letters screen (pipeline template from sib-fl-pherc0257 at 54b29c96): VC3D auto-grow on the organizer surface prediction (kept iff 0 self-intersections and >= 16 cm2), C2-NT render (31 layers), the official ink_9um step-075000 model in both directions, 2 x 2 cm tiles with manifests; reading was central and blind. The lane added a numbers-only geometry check (onsurf.py: 300 random vertices per segment tested against the surface prediction and the masked CT). From DECL-FL-4-A1 it ran the FL-4 kit as a PHerc0490A inner-winding lane (100-generation grows, C2-NT render, organizer-hosted 2023 Grand Prize TimeSformer variant B in both directions).

## What ran on this branch

FL-1 (2026-09-30): never got past environment setup (0 segments, 0 tiles). FL-2 primary (2026-10-01 from 02:14Z): 20 auto grows kept; the geometry check (GEOMETRY_CHECK.json, 05:48Z) flagged them as runaway meshes; 5 segments tiled, 40 official-model tiles, the last at 05:48Z. FL-4 PHerc0490A lane 12: 2 grows kept, 1 segment with GP forward and reverse passes by 19:10Z on 2026-10-01; then the usage limit stopped the fleet.

## Outcome

The lane's geometry check found that the kept FL-2 grows are mostly off the papyrus: few vertices lie on the surface prediction or inside the scroll's CT mask, and 15 of 20 stop at the generation cap rather than at data, so the area plus self-intersection gate does not catch runaway meshes. The central census found 0 positives for this scroll (FL2-WAVE1-RESULT: 8 tiles; FL3-W1-RESULT: 10 windows), but the positive-control gate was NOT SENSITIVE in every wave, so these nulls are uninformative. Its PHerc0490A FL-4 outputs were never read (DECL-FL-4-A3 limited reading to PHerc0268) and carry no evidence under DECL-FL-4-A5 (every FL-4 grow cut across windings).

| key number | meaning | file on this branch |
|---|---|---|
| 0.1955 | median fraction of sampled vertices on the surface prediction over the 20 kept FL-2 grows (range 0.127-0.33) | `logs/sib/fl-pherc0846b/fl2/GEOMETRY_CHECK.json` |
| 0.215-0.677 | range of the fraction of vertices inside the scroll CT mask | `logs/sib/fl-pherc0846b/fl2/GEOMETRY_CHECK.json` |
| 15 of 20 | kept grows that stop at the 31.13 cm2 generation cap | `logs/sib/fl-pherc0846b/fl2/GEOMETRY_CHECK.json` |
| 40 | official ink_9um tiles over 5 FL-2 segment manifests | `logs/sib/fl-pherc0846b/fl2/STATUS.md` |

## Where the records are

- `logs/sib/fl-pherc0846b/STATUS.md`
- `logs/sib/fl-pherc0846b/fl2/GEOMETRY_CHECK.json`
- `logs/sib/fl-pherc0846b/fl2/`
- `logs/sib/fl-pherc0846b/fl4/PHerc0490A/`
- `tools/sib/fl-pherc0846b/`

## Lesson

Measure how much of a grown mesh lies inside the scroll's CT mask before rendering it; area and self-intersection gates miss runaway meshes.

## Related

- claude/gifted-bell-gavnl5 (research log)
- fl4t
- sib-fl-pherc0257 (FL-2 template)
- sib-fl-pherc0306b (same grower defect)
- DECL-FL-1
- DECL-FL-2
- DECL-FL-2-E1
- FL2-WAVE1-RESULT
- DECL-FL-3
- FL3-W1-RESULT
- DECL-FL-4-A1
- DECL-FL-4-A3
- DECL-FL-4-A5
- DECL-FL-5

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
setsid nohup bash tools/sib/fl-pherc0846b/fl2/watchdog.sh >/dev/null 2>&1 &
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
