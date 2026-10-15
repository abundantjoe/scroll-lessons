<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="First Letters worker: PHerc0483B: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# First Letters worker: PHerc0483B

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-fl-pherc0483b` · First Letters push · 2026-09-30..2026-10-01 · status **STOPPED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0483B, PHerc0490A, PHercParis4.

## Question

Can the DECL-FL-1/-2 First Letters screen find 10 letters within 4 cm2 on PHerc0483B from grown or organizer segments and the official ink model? From DECL-FL-4-A1 the session became an FL-4 lane on PHerc0490A.

## Method

Worker of the DECL-FL-1/-2 First Letters screen (pipeline template from sib-fl-pherc0257 at 54b29c96): organizer tifxyz segments if the bucket has any, otherwise VC3D auto-grow on the organizer surface prediction (kept iff 0 self-intersections and >= 16 cm2), C2-NT render (31 layers), the official ink_9um step-075000 model in both directions, and 2 x 2 cm tiles (53.4 px/mm, valid >= 50 %) with manifests. Reading was done centrally by blind LLM readers with sealed scoring (FL-2 tile waves, then FL-3 stitched 4 x 4 cm windows), with a held-out PHerc0139 positive-control gate. From DECL-FL-4-A1 (2026-10-01 ~17:20Z) the worker ran the FL-4 kit as a PHerc0490A inner-winding lane: 100-generation grows, C2-NT render, the organizer-hosted 2023 Grand Prize TimeSformer (variant B) in both directions, tiles per segment.

## What ran on this branch

FL-1 (2026-09-30): blocked when setup_env.sh failed after the villa clone; the listing (0 organizer tifxyz) and 4 seeds were pushed. Paris 4 helper maps (2026-09-30/10-01), including tiles reassigned to it after it passed the byte-identical reproduction gate (DECL-P4-25-A10-A2); it also reported missing public CT chunks behind part of the map list, which became a data-completeness rule (DECL-P4-25-A12). FL-2 primary (2026-10-01): 23 segments tiled, 184 official-model tiles, after environment fixes and a container restart. FL-4 PHerc0490A lane 8: 1 grow kept at 17:23Z on 2026-10-01; nothing after (the usage limit stopped the fleet).

## Outcome

The central census found 0 positives for this scroll (FL2-WAVE1-RESULT: 8 tiles; FL3-W1-RESULT: 38 windows), but the positive-control gate was NOT SENSITIVE in every wave, so these nulls are uninformative, and DECL-FL-5 adds that the auto-grower used in FL-1/FL-2 cut across windings. Its PHerc0490A FL-4 output was never read (DECL-FL-4-A3 limited reading to PHerc0268) and carries no evidence under DECL-FL-4-A5 (every FL-4 grow cut across windings).

| key number | meaning | file on this branch |
|---|---|---|
| 184 | official ink_9um tiles over 23 FL-2 segment manifests | `logs/sib/fl-pherc0483b/fl2/STATUS.md` |
| 11.665195934621718 | cm2 area of the single FL-4 PHerc0490A grow | `logs/sib/fl-pherc0483b/fl4/PHerc0490A/STATUS.md` |

## Where the records are

- `logs/sib/fl-pherc0483b/STATUS.md`
- `logs/sib/fl-pherc0483b/fl2/`
- `logs/sib/fl-pherc0483b/fl4/PHerc0490A/`
- `tools/sib/fl-pherc0483b/`

## Lesson

A 0-positive census under a gate that never passed is uninformative; check that grown surfaces follow the papyrus before rendering or reading them.

## Related

- claude/gifted-bell-gavnl5 (research log)
- fl4t
- sib-fl-pherc0257 (FL-2 template)
- sib-pairs0139c (gate builder)
- DECL-FL-1
- DECL-FL-2
- DECL-FL-2-E1
- DECL-FL-2-E2
- FL2-WAVE1-RESULT
- FL2-WAVE2-GATE
- DECL-FL-3
- FL3-W1-GATE
- FL3-W1-RESULT
- DECL-FL-4-A1
- DECL-FL-4-A3
- DECL-FL-4-A5
- DECL-FL-5
- DECL-P4-25-A10-A1
- DECL-P4-25-A10-A2
- DECL-P4-25-A12
- DECL-P4-25-A14
- DECL-P4-25-A16
- DECL-P4-26-A2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
setsid nohup bash tools/sib/fl-pherc0483b/fl2/watchdog.sh >/dev/null 2>&1 &
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
