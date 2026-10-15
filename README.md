<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="D2 pairs PHerc0814 + protocol check: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# D2 pairs PHerc0814 + protocol check

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-pairs0814` · geometry, reading calibration, tools and records · 2026-09-25..2026-09-26 · status **COMPLETED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0814, PHerc0500P2, PHerc0332, PHerc1451.

## Question

(a) Which scans of PHerc0814, PHerc0500P2, PHerc0332 and PHerc1451 match the JULY (9.362 um, 113 keV) or MAY (8.64 um) acquisition protocol? (b) Build gated 9.362 um <-> 2.399 um D2 training pairs on PHerc0814.

## Method

(a) Protocol fields were read from the official root index and from each volume's metadata.json.

(b) The pairs were built in three stages:
1. Stage A fits a canvas affine per segment from its two organizer meshes.
2. Stage B cuts 384 px patches rendered with the official vc_render_tifxyz (-n 31) and gates them against the organizer 2.399 um surface volume. A patch passes if NCC >= 0.8 at zero shift and >= 7 of its 9 128 px windows align within 1 px. Labels come from the official 2.399 um ink map.
3. Stage C flags same-papyrus patches (CORR-RETRACE-RULE) and duplicates without dropping any, then packs the shards.

## What ran on this branch

2026-09-25 to 2026-09-26 on CPU: all 19 PHerc0814 segments. Two of them were handed to pairs0814b and merged back in stage C. 1502 candidate patches were gated, and 180 shard files (1560.9 MB) were pushed across the two branches.

## Outcome

PHerc0814 and PHerc0500P2 match JULY, PHerc1451 matches MAY, and PHerc0332 matches neither. 564 of 1502 patches pass the gate (0.375), with 11.209 cm^2 of ink and 56.604 cm^2 of blank labels. In a control with the CT shifted, no patch reaches NCC 0.8, so the bar separates aligned from shifted CT. Base-papyrus patches and 70 multi-member duplicate groups (292 passing patches) are flagged for the orchestrator to decide. No PHerc0500P2 pairs were built, because it is a held-out fold candidate.

| key number | meaning | file on this branch |
|---|---|---|
| 564 / 1502 | patches passing the alignment gate (rate 0.375) | `logs/sib/pairs0814/summary.json` |
| 0.791 | median patch NCC at zero shift | `logs/sib/pairs0814/REPORT.md` |
| 0.000 | fraction of shifted-CT controls reaching NCC >= 0.8 | `logs/sib/pairs0814/REPORT.md` |
| 11.209 cm^2 | ink-labelled area in passing patches (blank 56.604 cm^2) | `logs/sib/pairs0814/REPORT.md` |
| 180 files, 1560.9 MB | shards over both branches | `logs/sib/pairs0814/shards.json` |

## Where the records are

- `logs/sib/pairs0814/REPORT.md`
- `logs/sib/pairs0814/summary.json`
- `logs/sib/pairs0814/pair_registry.json`
- `logs/sib/pairs0814/shards.json`
- `logs/sib/pairs0814/protocol_check.json`
- `logs/sib/pairs0814/segment_inventory.json`
- `logs/sib/pairs0814/blockpairs/`

## Lesson

A shifted-CT control showed that the 0.8 NCC bar really measures alignment.

## Related

- sib-pairs0814b
- sib-pairs0139
- DECL-D2
- CORR-RETRACE-RULE

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
bash tools/sib/pairs0814/setup_env_sib.sh
PYTHONPATH=src /opt/hv/bin/python tools/sib/pairs0814/stage_a.py <SEG_ID>
PYTHONPATH=src /opt/hv/bin/python tools/sib/pairs0814/stage_b.py <SEG_ID>
PYTHONPATH=src /opt/hv/bin/python tools/sib/pairs0814/stage_c.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
