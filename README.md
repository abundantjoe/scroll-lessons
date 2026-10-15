<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Rejection-gated surface tracer: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Rejection-gated surface tracer

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-tracer` · ink-model training and checkpoint screening · 2026-09-25..2026-10-01 · status **TOOL** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc1203, PHercParis4, PHerc0175A, PHerc0813, PHerc0490A.

## Question

Can a rejection-gated build of the official VC3D surface tracer grow sheet surfaces without crossings or wrap jumps well enough to pass the T-SURF T0 gate, and can it repair or extend official meshes where they are defective?

## Method

The session built the official VC3D (villa 41701aa) and patched GrowPatch.cpp ('build c'): a NaN-safe distance and cost gate on every candidate, compactness deferral, a final audit and a seed-component filter. It tested the build on synthetic sheet scenes and on PHerc1203 dev seeds, with the T0 seeds excluded by code. It froze presets L15/L20/L25 and wrote a T0 proposal. Later tasks reused build c5 under declarations: a Paris 4 mesh-edge extension (P4-N), local hole re-traces (P4-22, P4-24), First Letters segment auto-growth screens, and Paris 4 inference-map production as a helper.

## What ran on this branch

From 2026-09-25 18:23Z to 2026-10-01: the build and synthetic suite; dev runs on 6 PHerc1203 seeds; a 75-generation T0 self-test on a dev seed; P4-N, P4-22 and P4-24 (geometry only); FL-1 on PHerc0175A, FL-2 on PHerc0813 and FL-4 on PHerc0490A; and S1 and verso inference maps for the Paris 4 own-model programme. T0 itself was never run.

## Outcome

T0 was never declared or run. Dev runs predicted the T0 area bar would fail (L15 median v2 area 0.46 cm^2 against a 3.0 cm^2 bar). Both declared re-traces were NOT ADOPTED, because the self-intersection gate failed (P4-22: 1720 pairs against 1148 on the official mesh; P4-24: 1 pair, 2.3 % of the hole filled). The P4-N extension passed 2 of 4 literal bars. FL-1 produced 0 tiles (no auto-grown segment reached 16 cm^2). FL-2 was stopped with 8 of 24 segments tiled, after a disk-full render loop. FL-4 grew one segment and tiled it before a pre-commit tag rejection blocked later pushes. No read results are on this branch.

| key number | meaning | file on this branch |
|---|---|---|
| 0.46 cm^2 | median v2 area, preset L15, 5 of 6 dev seeds saved (T0 bar >= 3.0 cm^2) | `logs/sib/tracer/dev/summary.json` |
| 1.60 cm^2 | v2 area after truncation in the 75-generation T0 self-test (raw 3.34 cm^2 with 511 crossings) | `logs/sib/tracer/REPORT.md` |
| 1720 vs 1148 | P4-22 self-intersection pairs: re-trace vs official mesh (gate requires 0); NOT ADOPTED | `logs/sib/tracer/p4-22/REPORT.md` |
| 2.3 % | share of the hole filled by the P4-24 re-trace; NOT ADOPTED | `logs/sib/tracer/p4-24/REPORT.md` |
| 2 PASS, 2 FAIL | P4-N mesh extension on the four DECL-P4-13 metrics (7218 vertices, 2.24 cm^2) | `logs/sib/tracer/p4n/REPORT.md` |
| 0 tiles | FL-1 PHerc0175A: 4 auto-grown segments of 0.0-0.30 cm^2, all below 16 cm^2 | `logs/sib/fl-pherc0175a/REPORT.md` |
| 8 of 24 | FL-2 PHerc0813 segments tiled before the task was stopped | `logs/sib/tracer/fl2/STATUS.md` |

## Where the records are

- `logs/sib/tracer/REPORT.md`
- `logs/sib/tracer/report.json`
- `logs/sib/tracer/STATUS.md`
- `logs/sib/tracer/RESUME.md`
- `logs/sib/tracer/dev/`
- `logs/sib/tracer/t0selftest/`
- `logs/sib/tracer/presets/`
- `logs/sib/tracer/p4n/REPORT.md`
- `logs/sib/tracer/p4-22/REPORT.md`
- `logs/sib/tracer/p4-24/REPORT.md`
- `logs/sib/fl-pherc0175a/REPORT.md`
- `logs/sib/tracer/fl2/STATUS.md`
- `logs/sib/tracer/fl4/PHerc0490A/STATUS.md`
- `tools/sib/tracer/`

## Lesson

Gated re-tracing failed exactly where the prediction does not separate adjacent windings, which is also where the official mesh is defective, so better input predictions, not tracer gates, are the bottleneck there.

## Related

- sib-p4-layout
- sib-flat1
- sib-pairs0814b
- DECL-TSURF
- DECL-P4-13
- DECL-P4-22
- DECL-P4-24
- DECL-P4-25
- DECL-P4-26-A2
- DECL-FL-1
- DECL-FL-4-A1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
CFGS='L15 L20 L25' bash tools/sib/tracer/dev_batch.sh <seed>...
/opt/hv/bin/python tools/sib/tracer/t0_run.py --selftest-dev auto_grown_20250923163331524 --family L --presets 15
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
