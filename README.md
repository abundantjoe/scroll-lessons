<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="D2 training pairs, PHerc0139 (held): Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# D2 training pairs, PHerc0139 (held)

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-pairs0139` · geometry, reading calibration, tools and records · 2026-09-25..2026-09-26 · status **STOPPED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0139.

## Question

Build gated 9.362 um <-> 2.399 um training pairs on known-text PHerc0139 for D2 (9 um inputs with 2.4 um targets), excluding the control, title and neighbouring papyrus.

## Method

Each segment gets a 2-D affine between its 9 um and 2.4 um organizer canvases, fitted from the meshes. A 128 px tile is kept only if it passes both tests in gate_spec.json, which was written before any gate number was computed: NCC >= 0.80 at zero shift against the organizer 2.399 um surface volume, and >= 7 of 9 sub-windows aligned within 1 px. Excluded: the controls and title, plus neighbours found by a point-density rule. Labels come from the organizer 2.399 um ink map. Segments are processed in order of label agreement (kappa), then crispness.

## What ran on this branch

2026-09-25 to 2026-09-26: affines for the segments, exclusion v1 (20 segments excluded), the segment order, and frame diagnostics on one segment (40 tiles). A partial build of the first segment (2534 candidates, 652 kept, 4 shards) stayed local and was not pushed. A container restart interrupted the second segment, and then the owner stopped the session.

## Outcome

Stopped and held. The owner stopped this session directly, and relayed orchestrator notices were not treated as lifting that stop. No pair set was pushed or post-checked, and the results of the re-trace re-check were never applied. The frame checks found no coordinate-convention bug: our 9.362 um render against the organizer surface volume gives NCC 0.996 with a 0.03 px shift.

| key number | meaning | file on this branch |
|---|---|---|
| 20 | segments excluded by exclusion v1 (controls, title, named neighbours, 13 more found by the density rule) | `logs/sib/pairs0139/exclusion.json` |
| 652 of 2534 | tiles kept on the first segment before the hold (local only, not pushed) | `logs/sib/pairs0139/ASK.md` |
| 0.996 | NCC of our 9.362 um render against the organizer 9.362 um surface volume (shift 0.03 px) | `logs/sib/pairs0139/ASK.md` |
| 1.55 px | median shift of the organizer 9.362 um surface volume against the 2.399 um reference through the mesh affine | `logs/sib/pairs0139/ASK.md` |

## Where the records are

- `logs/sib/pairs0139/ASK.md`
- `logs/sib/pairs0139/gate_spec.json`
- `logs/sib/pairs0139/exclusion.json`
- `logs/sib/pairs0139/affines.json`
- `logs/sib/pairs0139/segment_order.json`
- `logs/sib/pairs0139/runs.jsonl`

## Lesson

A lane that splits its work must push its handover file before it pauses; two helper lanes waited six hours for one that never came.

## Related

- sib-pairs0139b
- sib-pairs0139c
- sib-pairs0814
- DECL-D2
- CORR-RETRACE-RULE

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
bash tools/sib/pairs0139/vc_build.sh
tools/sib/pairs0139/run.sh exclude /work/p139/py/bin/python tools/sib/pairs0139/exclude.py
PYTHONPATH=src:tools/sib/pairs0139 /work/p139/py/bin/python tools/sib/pairs0139/run_all.py 3000
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
