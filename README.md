<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="First Letters worker: PHerc0490A: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# First Letters worker: PHerc0490A

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-fl-pherc0490a` · First Letters push · 2026-09-30..2026-10-01 · status **STOPPED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0490A.

## Question

Can the DECL-FL-1/-2 First Letters screen find 10 letters within 4 cm2 on PHerc0490A from grown or organizer segments and the official ink model? From DECL-FL-4-A1 the session was assigned as FL-4 lane 0 on PHerc0490A.

## Method

Worker of the DECL-FL-1/-2 First Letters screen (pipeline template from sib-fl-pherc0257 at 54b29c96): organizer tifxyz segments if the bucket has any, otherwise VC3D auto-grow on the organizer surface prediction (kept iff 0 self-intersections and >= 16 cm2), C2-NT render (31 layers), the official ink_9um step-075000 model in both directions, and 2 x 2 cm tiles (53.4 px/mm, valid >= 50 %) with manifests. Reading was done centrally by blind LLM readers with sealed scoring (FL-2 tile waves, then FL-3 stitched 4 x 4 cm windows), with a held-out PHerc0139 positive-control gate. The FL-4 kit (GP TimeSformer on PHerc0490A inner windings) was assigned under DECL-FL-4-A1 but never run here.

## What ran on this branch

FL-1 (2026-09-30): step 1 failed in setup_env. The Paris 4 helper assignment was held by the session's own permission layer and its tiles were reassigned (DECL-P4-25-A10-A2). FL-2 primary (2026-10-01): 14 of 22 segments tiled and pushed, 112 official-model tiles; the keepalive re-arm was refused by the session's permission check at 16:07Z and the pipeline did not continue. FL-4: NOT STARTED, held for the owner's explicit go-ahead (18:31Z on 2026-10-01).

## Outcome

The central census found 0 positives for this scroll (FL2-WAVE1-RESULT: 8 tiles; FL3-W1-RESULT: 26 windows), but the positive-control gate was NOT SENSITIVE in every wave, so these nulls are uninformative, and DECL-FL-5 adds that the auto-grower used in FL-1/FL-2 cut across windings. No FL-4 work was done on this branch.

| key number | meaning | file on this branch |
|---|---|---|
| 112 | official ink_9um tiles over 14 FL-2 segment manifests | `logs/sib/fl-pherc0490a/fl2/STATUS.md` |
| 14/22 | FL-2 segments tiled and pushed when the pipeline stopped | `logs/sib/fl-pherc0490a/fl4/PHerc0490A/STATUS.md` |

## Where the records are

- `logs/sib/fl-pherc0490a/STATUS.md`
- `logs/sib/fl-pherc0490a/fl2/`
- `logs/sib/fl-pherc0490a/fl4/PHerc0490A/STATUS.md`
- `tools/sib/fl-pherc0490a/`

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
- DECL-P4-25-A10-A2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
setsid nohup bash tools/sib/fl-pherc0490a/fl2/watchdog.sh >/dev/null 2>&1 &
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
