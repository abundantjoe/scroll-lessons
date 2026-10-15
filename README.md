<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="P4-F dense mineral-pigment screen: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# P4-F dense mineral-pigment screen

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-highz` · PARIS-4 investigations · 2026-09-26..2026-09-27 · status **COMPLETED** · verdict **NULL**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Is there a dense, high-Z mineral-pigment ink layer (Hg, Pb, Au, Cu, Fe, Egyptian blue) on the traced surfaces of the Paris 4 inner strips that carbon-ink models would miss (DECL-P4-6, -A1, -A2, -A3)?

## Method

Protocols were pushed before any number existed (PROTOCOL.md, PROTOCOL_2p4.md). Thresholds were frozen on known-text controls. The per-tile numeric screen measured: bright-voxel fraction on the sheet vs neighbouring gaps (f_in), letter-scale components and autocorrelation. Also run: 3-D morphology of bright components; NIST-based pigment attenuation physics; and injection-recovery of synthetic pigment letters into real control CT. After both depth calibrations returned STOP, a 9-offset sweep (-60 to +60 um) with a Bonferroni bar was run on both strips. Numbers only; no image viewed.

## What ran on this branch

2026-09-26 to 2026-09-27: E1 (1.129 um, 60 tiles) and E2 (2.4 um, 160 tiles), against controls of 64 and 171 tiles, from level-0 range reads; 20 injection regions per voxel size. The sub-lane p4-highz-c2 ran the 2.4 um control screen. An assigned cross-scroll model tile (P4-O) was stopped after about 12 minutes when that stage's known-text gate failed (0/3); no tile was produced.

## Outcome

0 DENSE-HOTSPOT tiles on E1, E2 and both controls, at every offset. The maximum E2 f_in per offset was 0.38-0.46, against a bar of 0.8. The bright voxels are compact 3-D grains spread evenly in depth, not surface layers, and the inner strips match the control. Injection detection limits (recovery >= 0.8) were Hg/Pb/Au 0.05-0.1 um, CuO 0.5 um, Fe2O3 0.5-1 um and Egyptian blue 2 um; the conservative floors are higher. Mineral-pigment ink at these thicknesses on the traced surfaces is ruled out. Organic dyes and untraced surfaces remain open.

| key number | meaning | file on this branch |
|---|---|---|
| 0 | DENSE-HOTSPOT tiles on E1, E2 and both controls, at every offset | `logs/sib/p4-highz/screen_dstar.json` |
| 0.38-0.46 vs 0.8 | max E2 f_in per offset vs the hotspot bar | `logs/sib/p4-highz/STATUS.md` |
| 0.05-0.1 um | Hg/Pb/Au detection limit, injection-recovery >= 0.8 | `logs/sib/p4-highz/REPORT.md` |
| 2 um | Egyptian blue detection limit (sigma 1 voxel) | `logs/sib/p4-highz/REPORT.md` |
| 0 of 40 | false positives in un-injected control regions | `logs/sib/p4-highz/REPORT.md` |

## Where the records are

- `logs/sib/p4-highz/REPORT.md`
- `logs/sib/p4-highz/STATUS.md`
- `logs/sib/p4-highz/PROTOCOL.md`
- `logs/sib/p4-highz/PROTOCOL_2p4.md`
- `logs/sib/p4-highz/PROTOCOL_dstar.md`
- `logs/sib/p4-highz/screen.json`
- `logs/sib/p4-highz/screen_2p4.json`
- `logs/sib/p4-highz/screen_dstar_E1.json`
- `logs/sib/p4-highz/screen_dstar_E2.json`
- `logs/sib/p4-highz/morph3d.json`
- `logs/sib/p4-highz/pigments.json`
- `logs/sib/p4-highz/inject_C.json`
- `logs/sib/p4-highz/inject_C2.json`
- `logs/sib/p4-highz/panel_ext.json`
- `tools/sib/p4-highz/`

## Lesson

Injection-recovery into real control CT gives a null its meaning, but the linear model also predicts visible carbon ink, which is not seen, so the conservative floors are the honest limits.

## Related

- DECL-P4-6
- DECL-P4-6-A1
- DECL-P4-6-A2
- DECL-P4-6-A3
- DECL-P4-12
- DECL-P4-16
- DECL-P4-14-A4
- P4-CHANNELS-RESULT-1
- sib-p4-highz-c2
- sib-p4-depth
- sib-p4-l2
- sib-p4-pig-cu

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/sib/p4-highz/stage_off.py <scratch> <repo> tiles <material> -60,-45,-30,-15,0,15,30,45,60
python tools/sib/p4-highz/stage_off.py <scratch> <repo> fin <material> -60,-45,-30,-15,0,15,30,45,60
python tools/sib/p4-highz/screen_off.py <scratch> <repo> <control> <target> <o_um,...>
python tools/sib/p4-highz/panel_ext.py <repo> <material>
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
