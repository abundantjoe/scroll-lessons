<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Same-papyrus contamination tooling: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Same-papyrus contamination tooling

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-contam` · ink-model training and checkpoint screening · 2026-09-25..2026-09-26 · status **STOPPED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0139.

## Question

Can a 3-D geometric test decide which PHerc0139 segments are the same papyrus (re-traces) and group them into papyrus units? Can it certify that an evaluation region lies far enough from every training patch (the FL-09 certificate)?

## Method

Densified the organizer tifxyz meshes 5 x 5 and applied a normal-distance same-papyrus rule to every segment pair: SAME if at least 1000 samples lie within 2 vox and count[0,1) >= 2 x count[2,3), in either direction. Papyrus units are the connected components of SAME, from geometry only. Built contam3d.py and fl09_cert.py with certified distances that subtract proven sampling bounds. Fitted a 2.4 -> 9.362 um transform so that a 2.4 um-only segment could join, and planted known faults on real meshes as a validation gate.

## What ran on this branch

Ran 2026-09-25 18:34-23:44Z: mesh fetch (39 PHerc0139 segments), the transform fit (passes its bars on a held-out check segment), synthetic core tests (pass), a 437-pair units run of about 98 min, the planted-fault run, and the real-data tests (exit 1). At about 23:47Z the owner stopped the session directly. It then held for the owner's own resume, declined relayed GO messages, and committed only ASK.md (2026-09-26 17:48Z).

## Outcome

Under the normal-distance form, 31 of 437 pairs are SAME, giving 13 papyrus units. Every planted fault that was built was caught. Two patch cases were never built because of a placement bug, so all_caught is false. The real-data tests fail on one pair where the distance forms disagree. The pass under the corrected three-form rule (CORR-RETRACE-RULE / DECL-DEVLOOP-A1), the test fixes and REPORT.md were never done. The research log records no adoption of this tooling.

| key number | meaning | file on this branch |
|---|---|---|
| 31 of 437 | PHerc0139 segment pairs judged SAME papyrus (normal-distance form) | `logs/sib/contam/units_0139.json` |
| 13 | papyrus units (connected components of SAME) over 39 segments | `logs/sib/contam/units_0139.json` |
| 9 of 11 | planted-fault cases built, all 9 caught; 2 not built, all_caught = false | `logs/sib/contam/planted_faults_0139.json` |
| 0.061 vox / 0.9964 | median normal distance / coverage of the 2.4 -> 9.362 um transform on its check segment (bars <= 0.25 vox, >= 0.95) | `logs/sib/contam/w030_transform.json` |

## Where the records are

- `logs/sib/contam/ASK.md`
- `logs/sib/contam/units_0139.json`
- `logs/sib/contam/planted_faults_0139.json`
- `logs/sib/contam/w030_transform.json`
- `logs/sib/contam/mesh_manifest_0139.json`
- `logs/sib/contam/proposals/PROPOSALS.md`
- `logs/sib/contam/runs.jsonl`
- `tools/sib/contam/`
- `tests/sib_contam_test_core.py`
- `tests/sib_contam_test_real.py`

## Lesson

A planted-fault gate counts only if every planted case is actually built; a placement bug silently dropped two of them here.

## Related

- sib-tribunal
- sib-sg
- sib-devloop
- sib-pairs0139
- CORR-RETRACE-RULE
- DECL-DEVLOOP-A1
- DECL-READCAL-A2
- DECL-D3-A2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/sib/contam/fetch_meshes.py --manifest logs/sib/contam/mesh_manifest_0139.json
python tools/sib/contam/w030_transform.py --out-json logs/sib/contam/w030_transform.json
pytest -q tests/sib_contam_test_core.py
python tools/sib/contam/units_run.py --manifest logs/sib/contam/mesh_manifest_0139.json ...
python tools/sib/contam/planted_real.py --manifest logs/sib/contam/mesh_manifest_0139.json --units logs/sib/contam/units_0139.json --workers 2 --with-retraces --out logs/sib/contam/planted_faults_0139.json
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
