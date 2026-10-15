<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="D2 pairs PHerc0814, second half: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# D2 pairs PHerc0814, second half

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-pairs0814b` · geometry, reading calibration, tools and records · 2026-09-25..2026-10-02 · status **COMPLETED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0814, PHercParis4, PHerc1545, PHerc0268.

## Question

Build the D2 pairs for the two PHerc0814 segments handed over by pairs0814, with its code unchanged. Later orders used the session as a builder and harness helper.

## Method

pairs0814's stage A and B code ran unchanged, and the outputs were copied to this lane's paths. Stage A was re-derived and compared field by field with pairs0814's. The later jobs followed fixed kits:
- a 160-tile reading-material build for a PHercParis4 census (E2: raw 2.4 um CT slab means, DECL-P4-5);
- one harness stage of sealed reads;
- own-model map helper passes;
- an FL-2 lane on PHerc1545;
- an FL-4 lane on PHerc0268.

## What ran on this branch

- 2026-09-25 to 2026-09-26: 545 candidate patches over 2 segments (156.27 cm^2 valid, 136 blocks).
- 2026-09-26: E2 material, 160 tiles.
- 2026-09-27 to 2026-10-01: the harness stage and the map helper passes (12 verso and 4 forward maps).
- 2026-10-01: FL-2 on PHerc1545 tiled 23 grown segments before DECL-FL-4-A1 stopped FL-2.
- 2026-10-02: FL-4 on PHerc0268 grew surfaces and wrote GP tiles until the background keepalive hit its time limit; it was not re-armed.

## Outcome

235 of 545 patches pass (43.1 %). Stage A reproduced pairs0814's geometry and labels bit for bit, and the final stage C on pairs0814 merged both halves. The helper outputs are pushed with hashes; scoring was the orchestrator's. The session stopped on 2026-10-02, part-way through FL-4, when its keepalive reached the maximum background time.

| key number | meaning | file on this branch |
|---|---|---|
| 235 / 545 | patches passing the alignment gate on the two handed-over segments (43.1 %) | `logs/sib/pairs0814b/REPORT.md` |
| 160 | read-eligible E2 tiles built for the PHercParis4 census | `logs/sib/pairs0814b/e2/REPORT.md` |
| 23 | PHerc1545 grown segments tiled in FL-2 before the stop | `logs/sib/pairs0814b/fl2/STATUS.md` |

## Where the records are

- `logs/sib/pairs0814b/REPORT.md`
- `logs/sib/pairs0814b/registry/`
- `data/sib/pairs0814b/blockpairs/`
- `logs/sib/pairs0814b/e2/REPORT.md`
- `logs/sib/pairs0814b/rh/STATUS.md`
- `logs/sib/pairs0814b/STATUS.md`
- `logs/sib/pairs0814b/fl2/STATUS.md`
- `logs/sib/pairs0814b/fl4/PHerc0268/STATUS.md`

## Lesson

Re-running the parent lane's stage A and checking it field by field made the split build verifiably identical.

## Related

- sib-pairs0814
- sib-rh-e2
- DECL-D2
- DECL-P4-5
- DECL-REMOTE-HARNESS-1
- DECL-FL-2
- DECL-FL-4-A1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
bash tools/sib/pairs0814b/fl4/setup_gp.sh
bash tools/sib/pairs0814b/fl4/run.sh
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
