<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Red-pigment (Hg/Pb) title detector: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Red-pigment (Hg/Pb) title detector

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-pig-red` · PARIS-4 investigations · 2026-09-26..2026-09-26 · status **INCOMPLETE** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Could a Paris 4 title in cinnabar (HgS) or red lead (Pb3O4, which turns to PbO) be detected in the published raw CT of the title strip?

## Method

Step 1 was a cited memo. It covered thermal and chemical stability at 300-400 C: cinnabar turns to metacinnabar at about 345 C, and the lead stays in place. It also covered grain size, layer thickness and attenuation, with an xraylib table (xcom.json). Step 2 froze the detector rules in params.json before any title-strip number: a control-derived high-intensity threshold, block density, stroke-scale components, planarity and mesh distance, plus a declared injection plan. An addendum recorded the DECL-P4-12 priorities and an analytic detection-limit model at 2.4 um.

## What ran on this branch

Only steps 1-2 and the analytic model ran, on 2026-09-26. The first CT read was a numbers-only depth histogram of control chunks, and the session's safety check refused it. Per the standing rules it was not routed around and no sub-sibling was created. Control calibration, injection-recovery and scoring therefore never ran.

## Outcome

There is no measured result and no title-strip number. The lane stayed BLOCKED on CT access (ASK-1) and asked for a fresh session to run steps 3-4 with params.json unchanged. The only sensitivity figure is an unvalidated analytic prediction: in the pessimistic case about 1.5-1.7 um HgS and 1.1-1.3 um PbO at 2.4 um; in the optimistic case below 0.1 um. In aggregate, mineral red pigments were covered separately by the p4-highz density screen (research log P4-CHANNELS-RESULT-1), not by this lane.

| key number | meaning | file on this branch |
|---|---|---|
| 17.1 /cm and 22.9 /cm | linear attenuation at 78 keV of cinnabar and litharge (PbO) at full density | `logs/sib/p4-pig-red/xcom.json` |
| 1.491-1.705 um | analytic (not injection) pessimistic HgS limit at 2.4 um, PSF sigma 2 voxels | `logs/sib/p4-pig-red/detlim_model_2p4.json` |
| 1.11-1.269 um | analytic pessimistic PbO limit at 2.4 um, PSF sigma 2 voxels | `logs/sib/p4-pig-red/detlim_model_2p4.json` |
| 0 | CT reads completed; steps 3-4 never started | `logs/sib/p4-pig-red/STATUS.md` |

## Where the records are

- `logs/sib/p4-pig-red/MEMO.md`
- `logs/sib/p4-pig-red/params.json`
- `logs/sib/p4-pig-red/xcom.json`
- `logs/sib/p4-pig-red/detlim_model_2p4.json`
- `logs/sib/p4-pig-red/ADDENDUM-1.md`
- `logs/sib/p4-pig-red/ASK.md`
- `logs/sib/p4-pig-red/STATUS.md`
- `tools/sib/p4-pig-red/xcom.py`

## Lesson

When data access is refused, record it and ask rather than work around it; a frozen params.json lets a fresh session resume without redesign.

## Related

- sib-p4-pig-gold
- sib-p4-pig-fe
- sib-p4-highz
- DECL-P4-10
- DECL-P4-12
- DECL-P4-6

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/sib/p4-pig-red/xcom.py <out.json>
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
