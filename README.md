<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="First Letters template/pilot: PHerc0257: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# First Letters template/pilot: PHerc0257

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-fl-pherc0257` · First Letters push · 2026-09-30..2026-10-02 · status **STOPPED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0257, PHerc0268, PHercParis4.

## Question

Can the DECL-FL-1/-2 First Letters screen find 10 letters within 4 cm2 on PHerc0257 from grown or organizer segments and the official ink model? This worker's pipeline became the DECL-FL-2 template and the session ran the FL-2 pilot; from DECL-FL-4-A1 it became an FL-4 lane on PHerc0268.

## Method

Worker of the DECL-FL-1/-2 First Letters screen: organizer tifxyz segments if the bucket has any, otherwise VC3D auto-grow on the organizer surface prediction (kept iff 0 self-intersections and >= 16 cm2), C2-NT render (31 layers), the official ink_9um step-075000 model in both directions, and 2 x 2 cm tiles (53.4 px/mm, valid >= 50 %) with manifests; its code at 54b29c96 became the template for every FL-2 worker. Reading was done centrally by blind LLM readers with sealed scoring (FL-2 tile waves, then FL-3 stitched 4 x 4 cm windows), with a held-out PHerc0139 positive-control gate. From DECL-FL-4-A1 (2026-10-01 ~17:20Z) the worker ran the FL-4 kit as a PHerc0268 inner-winding lane: 100-generation grows, C2-NT render, the organizer-hosted 2023 Grand Prize TimeSformer (variant B) in both directions, cover cells and one whole-segment window per direction.

## What ran on this branch

FL-1 (2026-09-30 to 10-01 01:06Z): COMPLETE, 4 auto-grown segments (31.13-31.15 cm2, 0 transverse self-intersections), 32 tiles; this pipeline (commit 54b29c96) became the FL-2 template. FL-2 pilot (2026-10-01): the second (competitor) model's download was refused by the session classifier (DENSE_FAIL.json; arm withdrawn by DECL-FL-2-E1), and the official model's training scrolls were listed (TRAINING_SCROLLS.json); 25 tile manifests, 200 official-model tiles (including the FL-1 segments). Paris 4 helper maps (2026-09-30). FL-4 PHerc0268 lane 5: 8 grows kept on 2026-10-01, every render failed; on 2026-10-02 one segment got GP forward and reverse passes; other seeds of this lane were computed by the orchestrator's local runner (FL4-W46, FL4-W49). The fleet stopped at about 08:00Z on 2026-10-02.

## Outcome

The central census found 0 positives for this scroll (FL2-WAVE1-RESULT: 8 tiles; FL3-W1-RESULT: 46 windows), but the positive-control gate was NOT SENSITIVE in every wave, so these nulls are uninformative, and DECL-FL-5 adds that the auto-grower used in FL-1/FL-2 cut across windings. This lane's PHerc0268 FL-4 outputs were read in the FL4 fleet waves (W41/W45/W47; 43 PHerc0268 items read in all, 0 positives) and were then declared VOID by DECL-FL-4-A5: every FL-4 grow was data-independent (no normal grids) and cut across windings.

| key number | meaning | file on this branch |
|---|---|---|
| 32 | DECL-FL-1 tiles (4 segments x 2x2 cells x 2 directions), joined to the FL-2 census | `logs/sib/fl-pherc0257/STATUS.md` |
| 29 of 32 | FL-1 tiles with ink_score_ge128 inside the [0.01, 0.40] pre-screen band | `logs/sib/fl-pherc0257/STATUS.md` |
| 200 | official ink_9um tiles over 25 FL-2 tile manifests | `logs/sib/fl-pherc0257/fl2/STATUS.md` |
| 8 | FL-4 PHerc0268 grows kept on 2026-10-01, each followed by a failed render | `logs/sib/fl-pherc0257/fl4/PHerc0268/STATUS.md` |

## Where the records are

- `logs/sib/fl-pherc0257/STATUS.md`
- `logs/sib/fl-pherc0257/fl0257_s0/`
- `logs/sib/fl-pherc0257/fl2/`
- `logs/sib/fl-pherc0257/fl2/DENSE_FAIL.json`
- `logs/sib/fl-pherc0257/fl2/TRAINING_SCROLLS.json`
- `logs/sib/fl-pherc0257/fl4/PHerc0268/`
- `tools/sib/fl-pherc0257/`

## Lesson

A 0-positive census under a gate that never passed is uninformative; check that grown surfaces follow the papyrus before rendering or reading them.

## Related

- claude/gifted-bell-gavnl5 (research log)
- fl4t
- sib-pairs0139c (gate builder)
- sib-p4v-14 (second FL-2 worker)
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
- DECL-FL-4-A2
- DECL-FL-4-A3
- DECL-FL-4-A4-A2
- DECL-FL-4-A4-A2-E4
- FL4-W46-RESULT
- FL4-W49-RESULT
- DECL-FL-4-A5
- DECL-FL-5
- DECL-P4-25-A10-A1
- DECL-P4-25-A14
- DECL-P4-25-A16

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run (branch claude/gifted-bell-gavnl5-sib-fl-pherc0257)
bash $REPO/tools/sib/fl-pherc0257/fl2/pipeline.sh >> /work/fl2/pipeline.out 2>&1
bash $REPO/tools/sib/fl-pherc0257/pipeline.sh >> /work/fl0257/pipeline.out 2>&1
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
