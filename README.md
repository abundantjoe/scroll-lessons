<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="DEV recipe LC384-SOFT trainer: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# DEV recipe LC384-SOFT trainer

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-dev-lcsoft` · ink-model training and checkpoint screening · 2026-09-26..2026-09-27 · status **INCOMPLETE** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Does a frozen-encoder letter-context head (384 px of context on cached base-encoder features) trained on soft teacher targets (DEV-LOOP recipe 2, LC384-SOFT, with NULL and REV controls) sharpen 9 um maps on the frozen DEV registry?

## Method

The session reused the amx lane's devloop-r1 code byte-identically and added only a declared '--targets soft' switch (masked BCE against reference / 255, no thresholds, no ignored band). It also added a fail-closed soft-target builder. The ASK ruling kept the encoder frozen, as declared, although the task text had said 'unfrozen'. A resumable phase-2 pipeline (pool, feature caches, soft targets, then RECIPE, NULL, REV at 2000 steps) refuses to run without 'GO DEV LC384-SOFT', a METRIC-HASH id and a matching hold-out registry hash.

## What ran on this branch

Phase 1 on 2026-09-26: 11 upstream unit tests and a 20-step synthetic smoke per arm on 75 fake tiles (fp32, 4 threads), plus a cost-only benchmark of the undeclared unfrozen-encoder variant. From 2026-09-26 21:39Z the session ran P4-O inference (DECL-P4-14-A1/-A2) of the official PHerc.1667-iteration-1 checkpoint over a planned 108-tile Paris 4 grid in fp32, about 3 h per tile, until 2026-09-27 10:19Z.

## Outcome

Phase 2 never ran: the DEV-LOOP freeze and its METRIC-HASH were never recorded, so there is no DEV result for LC384-SOFT. The P4-O run committed 4 inference tiles (of 108 planned) before the branch's last commit. The tiles were never viewed by this session, and any reading of them is outside this branch. The session also recorded an upstream builder bug: a TypeError after each tile is written stops multi-tile calls after the first tile.

| key number | meaning | file on this branch |
|---|---|---|
| 0.360 s/step | RECIPE arm synthetic smoke step time (frozen encoder, fp16 feature cache); loss 0.731 -> 0.696, synthetic only | `logs/sib/dev-lcsoft/smoke_synth.json` |
| about 0.65 h | estimated training time for RECIPE + NULL + REV at 2000 steps each | `logs/sib/dev-lcsoft/READY.md` |
| 7.67 s/step (21x) | cost of the undeclared unfrozen-encoder reading, priced only | `logs/sib/dev-lcsoft/bench_unfrozen.json` |
| 11 of 11 | upstream devloop-r1 unit tests passing in this environment | `logs/sib/dev-lcsoft/READY.md` |
| 4 | P4-O iteration-1 inference tiles committed (n_tiles in the manifest) | `logs/sib/dev-lcsoft/p4o/PHerc.1667-iteration-1/manifest.json` |

## Where the records are

- `logs/sib/dev-lcsoft/READY.md`
- `logs/sib/dev-lcsoft/STATUS.md`
- `logs/sib/dev-lcsoft/ASK.md`
- `logs/sib/dev-lcsoft/config.json`
- `logs/sib/dev-lcsoft/smoke_synth.json`
- `logs/sib/dev-lcsoft/bench_unfrozen.json`
- `logs/sib/dev-lcsoft/p4o/PHerc.1667-iteration-1/manifest.json`
- `tools/sib/dev-lcsoft/`

## Lesson

When a task text and the declaration disagree, build the declared recipe and only price the other reading; that kept the frozen encoder in line with DECL-DEVLOOP-A1.

## Related

- sib-amx
- sib-devloop
- sib-dev-distft
- sib-ckpt-screen-b
- sib-pairs0814b
- DECL-DEVLOOP
- DECL-DEVLOOP-A1
- DECL-P4-14-A1
- DECL-P4-14-A2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
bash tools/sib/dev-lcsoft/setup_py.sh
PYTHONPATH=/work/lcsoft/pylib OMP_NUM_THREADS=4 /opt/hv-ink/bin/python tools/sib/dev-lcsoft/smoke.py --root /work/lcsoft/smoke --steps 20 --threads 4 --out-json logs/sib/dev-lcsoft/smoke_synth.json
PYTHONPATH=/work/lcsoft/pylib OMP_NUM_THREADS=4 /opt/hv-ink/bin/python tools/sib/dev-lcsoft/bench_unfrozen.py --threads 4 --steps 3 --out-json logs/sib/dev-lcsoft/bench_unfrozen.json
PYTHONPATH=/work/lcsoft/pylib OMP_NUM_THREADS=4 /opt/hv-ink/bin/python -m pytest -q -p no:cacheprovider tools/sib/dev-lcsoft/test_upstream_lc.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
