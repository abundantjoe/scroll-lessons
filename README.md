<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="FL-4 ring patches and organizer maps: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# FL-4 ring patches and organizer maps

**Dominion experiment branch** `claude/gifted-bell-gavnl5-fl4t` · First Letters push · 2026-10-02..2026-10-10 · status **COMPLETED** · verdict **NULL**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0268, PHerc0800, PHerc1203.

## Question

After the first FL-4 grows were found to cut across windings, can normal-grid-guided grows of PHerc0268, or organizer segments of the eligible scrolls PHerc0800 and PHerc1203, give ink-model maps with text-like structure that could support a First Letters claim?

## Method

Shared lane branch for fresh lane sessions. DECL-FL-4-A7 (ring1): seeds on one PHerc0268 winding band grown 60 generations with the organizer normal grids, a radial sheet gate (median |cos| >= 0.8, frac>0.8 >= 0.7, spread < 2 mm/cm; a MARGINAL tier added by -A7-E2), C2-NT render and the organizer-hosted 2023 Grand Prize TimeSformer (variant B) in both directions. DECL-FL-5/-A1 (ring2-4): normal-grid patches on three more bands with the official ink_9um step-075000 in both directions plus sheet-piece maps; DECL-FL-6: ink_9um on organizer segments of PHerc0800 (organizer surface volumes) and PHerc1203 (tifxyz rendered here). LLM blind reads were suspended by owner order (OWNER-ORDER-FL4-B); maps went to the owner and were triaged by the orchestrator.

## What ran on this branch

2026-10-02/03: 7 ring1 patches pushed here (4 DONE, 3 of them flagged MARGINAL; 3 FAILED), 15 ring2-4 patch directories (13 DONE, 2 FAILED), 5 PHerc0800 and 19 PHerc1203 organizer-segment runs (the remaining ones ran on the orchestrator's machine). On 2026-10-09/10 the branch also received fleet outputs of DECL-FL-7 ink-model training (logs/fl7/), the DECL-UMB-2 native umbilicus core (logs/umb/native/, partial after container restarts) and the DECL-E2E-3 observability survey (logs/unr/obs/), until the fleet ran out of usage on 2026-10-10.

## Outcome

No candidate. DECL-FL-4-A8: the grows stay on one layer between cracks and jump layers at cracks, and the GP model marked 46-59 % of each patch as ink, so the ring1 maps are void. FL5-ROWSCORE-RESULT: the automated row-structure score is NOT SENSITIVE (0.018 of known-text tiles above the null p99, bar 0.25). FL6-RESULT and -A1: ring2-4 maps are uniform speckle on non-flat renders; PHerc0800 6/6 and PHerc1203 20/20 organizer segments show no row alignment, forward and reverse unrelated, 0 candidates; a two-model agreement check on one PHerc0800 segment was barely above its controls and showed no evidence of ink-like features (FL6-AGREE-RESULT). Nothing submittable; no letter claimed. The later fleet outputs are scored on the research log (FL7-A1-RESULT, UMB2-B6-RESULT, OBS-SURVEY-RESULT).

| key number | meaning | file on this branch |
|---|---|---|
| 0.8826629156537384 | median \|cos\| of the one lane-grown ring1 patch that passed the strict sheet gate (pass true) | `logs/fl4t/ring1/i102/sheet_gate.json` |
| 0.6636259704367361 | median \|cos\| of a ring1 patch that failed the strict gate and was rendered as MARGINAL | `logs/fl4t/ring1/i101/sheet_gate.json` |
| 3 of 7 | ring1 lane patches that ended FAILED (FAILED marker) | `logs/fl4t/ring1/` |
| 0.18471395458210157 | fraction of an own ring2 patch ink_9um map >= 0.5 (forward) | `logs/fl4t/ring2/i4/ink9um_forward.json` |
| 0.059834803921568626 | fraction of a PHerc0800 organizer-segment ink_9um map >= 0.5 (forward) | `logs/fl4t/sv0800/i1/ink9um_forward.json` |
| 0.10154880608764104 | fraction of the largest PHerc1203 organizer-segment ink_9um map >= 0.5 (forward) | `logs/fl4t/tx1203/i14/ink9um_forward.json` |

## Where the records are

- `logs/fl4t/ring1/`
- `logs/fl4t/ring2/`
- `logs/fl4t/ring3/`
- `logs/fl4t/ring4/`
- `logs/fl4t/sv0800/`
- `logs/fl4t/tx1203/`
- `logs/fl7/`
- `logs/umb/native/`
- `logs/unr/obs/`

## Lesson

A gate on surface orientation cannot see layer jumps at cracks; sheet-following and a known-ink positive control must be shown before any map is trusted.

## Related

- claude/gifted-bell-gavnl5 (research log)
- DECL-FL-4-A5
- DECL-FL-4-A6
- DECL-FL-4-A7
- DECL-FL-4-A7-E1
- DECL-FL-4-A7-E2
- DECL-FL-4-A8
- DECL-FL-4-A9
- OWNER-ORDER-FL4-B
- DECL-FL-5
- DECL-FL-5-A1
- FL5-ROWSCORE-RESULT
- DECL-FL-6
- FL6-SV0800-RESULT
- FL6-AGREE-RESULT
- FL6-TX1203-PARTIAL
- FL6-TX1203-RESULT-B
- FL6-RESULT
- FL6-RESULT-A1
- DECL-FL-7
- DECL-UMB-2
- DECL-E2E-3
- OBS-SURVEY-RESULT

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
setsid nohup bash tools/fl4/ring_run.sh <RING> <IDX> 60 > /work/ring.out 2>&1 &
setsid nohup bash tools/fl4/ring_chain.sh <IDX> > /work/chain.out 2>&1 < /dev/null &
bash tools/fl4/orgseg_run.sh sv0800 <IDX>
bash tools/fl4/orgseg_run.sh tx1203 <IDX>
python3 tools/fl4/rowscore.py <px_per_mm> <png>...
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
