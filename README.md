<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Gold-ink title detector: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Gold-ink title detector

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-pig-gold` · PARIS-4 investigations · 2026-09-26..2026-09-27 · status **COMPLETED** · verdict **NULL**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Could a Paris 4 title in gold (leaf or shell gold) be detected in the published CT of the title strip? If so, is there any gold-like signal there?

## Method

Step 1 was a physics memo: xraylib attenuation, the Au K-edge at 80.725 keV, leaf about 0.34 um thick from an ancient written source, and the reconstruction chain taken from the published metadata. Step 2 was an inventory of scan pairs that bracket the K-edge. The thin-layer ridge detector (v2) replaced v1 after a single control pilot showed v1 insensitive; this change is disclosed. Its params.json was frozen from the controls only, before any title-strip number. Injection-recovery planted Greek-capital glyphs at 6 Au-equivalent thicknesses x 2 papyrus densities, at 12 locations in each of 4 materials. False positives were measured with a virtual glyph, unrotated and rot-90. Then the E1 (60) and E2 (160) title-strip tiles were scored (DECL-P4-10, DECL-P4-12 items 3 and 5).

## What ran on this branch

This ran 2026-09-26 to 2026-09-27, numbers only. The controls were C1 (64 tiles, 1.129 um) and C2 (168 tiles, 2.4 um level 1). The two planned sub-siblings (e1, e2) hit the account session limit before doing any work, so this branch ran all injection and scoring itself with the same frozen code.

## Outcome

E2 (2.4 um) shows no gold. 12/12 letters are recovered at >= 0.05 um Au-equivalent (papyrus density 1.5), and 0/12 at 0.01 um. The scan shows 0 DECL-P4-10 hotspots. 8 tiles passed the non-excluding DECL-P4-12 area and in-sheet rule, but all had Z_max <= 88, against a minimum injected Z_max of 154.5 for a 0.1 um layer. So no letter-scale gold layer >= 0.1 um exists in the scored E2 area (about 62,400 mm2). E1 (1.129 um L1) is INSENSITIVE (best 3/12) and rules nothing out. No usable Au K-edge scan pair exists.

| key number | meaning | file on this branch |
|---|---|---|
| 0.05 um | E2 detection limit, Au-equivalent, papyrus density 1.5 (0.02 um at density 0.5) | `logs/sib/p4-pig-gold/injection/summary.json` |
| 93.6 | highest tile Z anywhere on the E2 strip | `logs/sib/p4-pig-gold/REPORT.md` |
| 154.5 | minimum injected Z_max for a 0.1 um gold layer on E2 (density 1.5) | `logs/sib/p4-pig-gold/REPORT.md` |
| 3/12 | best E1 sensitivity at any thickness (insensitive) | `logs/sib/p4-pig-gold/injection/summary.json` |
| 0 | DECL-P4-10 hotspots on E1 and on E2 | `logs/sib/p4-pig-gold/hotspots.json` |
| 0/12 | virtual-glyph false positives, unrotated and rot-90, in every material | `logs/sib/p4-pig-gold/injection/summary.json` |

## Where the records are

- `logs/sib/p4-pig-gold/REPORT.md`
- `logs/sib/p4-pig-gold/scores.json`
- `logs/sib/p4-pig-gold/hotspots.json`
- `logs/sib/p4-pig-gold/injection/`
- `logs/sib/p4-pig-gold/control/`
- `logs/sib/p4-pig-gold/title/`
- `logs/sib/p4-pig-gold/MEMO.md`
- `logs/sib/p4-pig-gold/params.json`
- `logs/sib/p4-pig-gold/kedge_inventory.json`
- `tools/sib/p4-pig-gold/`

## Lesson

One frozen detector can rule a pigment out on one material and be blind on another, so report each material's sensitivity separately.

## Related

- sib-p4-pig-fe
- sib-p4-pig-red
- sib-p4-highz
- DECL-P4-10
- DECL-P4-12
- DECL-P4-6

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/sib/p4-pig-gold/kedge_inventory.py <scratch> <out.json>
python tools/sib/p4-pig-gold/freeze.py <outdir> <params.json>
python tools/sib/p4-pig-gold/inject.py <params.json> <scratch> <out.jsonl> <MAT> <n_locations> [--procs 4]
python tools/sib/p4-pig-gold/summarize_inj.py <params.json> <out.json> <inj_*.jsonl ...>
python3 tools/sib/p4-pig-gold/run_tiles.py E2 /tmp/g/scr /tmp/g/out --procs 4 --threads 24
python3 tools/sib/p4-pig-gold/score.py logs/sib/p4-pig-gold/params.json E2 /tmp/g/out /tmp/g/scr <out.json> --excl <flags file>
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
