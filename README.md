<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Checkpoint screen A: 9um/hecate/dino: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Checkpoint screen A: 9um/hecate/dino

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-ckpt-screen-a` · ink-model training and checkpoint screening · 2026-09-26..2026-09-30 · status **STOOD-DOWN** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md).

## Question

Can three official checkpoints (ink_9um seed43, hecate_9.6um, ink_3d_dino_guided) be screened on the DEV-LOOP known-text windows? Are any of them eligible for the P4-O cross-scroll run, i.e. is Paris 4 absent from their documented training data? The lane was later assigned PHerc.1667-iteration-0 for P4-O.

## Method

Ran phase 1 of DECL-DEVLOOP-SCREEN: verified weights by sha256 against the catalogue, took each input spec from its card or embedded config, and wrote a wrapper (screen_wrap.py) that emits the devloop map format. The wrapper was smoke-tested for cost on synthetic volumes. For P4-O, each card's training-data statement was quoted into provenance.json before any inference. For iteration-0, a banded chunk reader was built and self-tested on synthetic data against the card's tiling loop.

## What ran on this branch

On 2026-09-26: specs, wrapper and synthetic smoke runs (ink_9um seed43 34.2 s and hecate 849.3 s on a 31 x 512 x 512 synthetic input; ink_3d_dino_guided was not screened because its card documents only a 2.4 um input), the provenance screen, and iteration-0 preparation. The DEV screen never ran because its METRIC-HASH and GO SCREEN never arrived. The iteration-0 inference launch was refused by the session's permission layer at 21:28Z. On 2026-09-30 a First Letters pass-3 task on PHerc0483 was held for an explicit owner go and never launched.

## Outcome

Provenance: 0 of 3 checkpoints are eligible for P4-O, because each one's own documentation states Paris 4 training data. No tile, map or manifest exists for iteration-0. DECL-P4-14-A2 item 4 dropped iteration 0 rather than route around the permission block, so batch o1 never existed. No DEV screen map was made, and no CT data was read on this branch.

| key number | meaning | file on this branch |
|---|---|---|
| 0 of 3 | checkpoints eligible for P4-O (documented Paris 4 training data) | `logs/sib/ckpt-screen-a/p4o/provenance.json` |
| 34.2 s / 849.3 s | synthetic smoke runtime for ink_9um seed43 / hecate_9.6um (4 threads, fp32) | `logs/sib/ckpt-screen-a/SPECS.json` |
| 3.5-4.1 s | per model window in the iteration-0 reader self-test (synthetic, 4 threads fp32; max abs diff 0.0 vs the card loop) | `logs/sib/ckpt-screen-a/STATUS.md` |
| ~450-480 h | projected single-worker cost for the 108-tile P4-O grid for iteration-0 | `logs/sib/ckpt-screen-a/STATUS.md` |

## Where the records are

- `logs/sib/ckpt-screen-a/STATUS.md`
- `logs/sib/ckpt-screen-a/SPECS.json`
- `logs/sib/ckpt-screen-a/SUBSIBS.md`
- `logs/sib/ckpt-screen-a/p4o/provenance.json`
- `logs/sib/ckpt-screen-a/sources/`
- `logs/sib/ckpt-screen-a/runs.jsonl`
- `tools/sib/ckpt-screen-a/`

## Lesson

Quoting each checkpoint's training-data statement before any inference turned eligibility into a documentation check instead of a judgment made after seeing maps.

## Related

- sib-ckpt-screen-b
- sib-ckpt-screen-c
- sib-devloop
- sib-chain2um
- DECL-DEVLOOP-SCREEN
- DECL-P4-14
- DECL-P4-14-A1
- DECL-P4-14-A2
- P4-O-PROVENANCE

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
/opt/hv-ink/bin/python tools/sib/ckpt-screen-a/screen_wrap.py selftest
/opt/hv-ink/bin/python tools/sib/ckpt-screen-a/screen_wrap.py ink9 --render /work/sa/synth512.zarr --ckpt /work/ckpt/ink_9um/hybrid_3d2d-seed43/step-075000.pth --out /work/sa/smoke/ink9_512 --wid synth512 --threads 4
/opt/hv-ink/bin/python tools/sib/ckpt-screen-a/make_specs.py
/opt/p4o/bin/python tools/sib/ckpt-screen-a/p4o_selftest.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
