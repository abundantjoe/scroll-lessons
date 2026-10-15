<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Checkpoint screen B: PHerc.1667 family: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Checkpoint screen B: PHerc.1667 family

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-ckpt-screen-b` · ink-model training and checkpoint screening · 2026-09-26..2026-09-30 · status **COMPLETED** · verdict **FAILED**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Can the six public PHerc.1667-iteration checkpoints be screened, and are they eligible (no Paris 4 training data)? Does the latest one, iteration-5, separate ink from papyrus on a PHercParis4 2.4 um surface volume well enough to pass the declared known-text gate?

## Method

Ran phase 1 of DECL-DEVLOOP-SCREEN (weights, card code, the infer_1667.py wrapper, a synthetic smoke test and an in-sample table), then wrote provenance.json quoting each card before any inference. For P4-O, the official HF model code ran unchanged at the card geometry: 2.4 um level 0, 62 slices, 256 px windows, stride 128, clip(0,200)/255, fp32. Tiles were built with tools/sib/ckpt-screen-b/p4o_tiles.py, split across the parent, three sub-siblings and later fleet workers, and merged with sha256 and code-commit checks into a manifest. A separate harness read the manifest under the declared stage rule.

## What ran on this branch

From 2026-09-26 to 2026-09-27: phase 1 (smoke 6/6 pass), provenance, and iteration-5 tile inference at about 3.3-4.2 CPU-h per 2 x 2 cm tile on 4 vCPU. Builder fixes were needed for a crash after each tile, for resumable 15-min checkpoints, and for two memory overruns. The final interim manifest holds 13 tiles. After the gate result, an undeclared, numbers-only input re-normalisation test was run. On 2026-09-30 the session was reassigned to a First Letters pass-3 worker task on PHerc0483; at the last commit its environment build was still running.

## Outcome

Provenance: all 6 iterations are eligible. Their documented training data are PHerc1667, or PHerc0500P2/0343P/0009B for iteration-0, with a Kinetics initialisation. The first stage read of iteration-5 failed its known-text gate (P4-O-STAGE-O2S1-RESULT), so the batch is uninformative rather than a null. The model did not separate ink from papyrus on this volume at this geometry, which the record attributes to domain shift. No further iteration-5 tiles were started. The re-normalisation test showed only a small affine correction, so no renormalised run was proposed. The DEV-screen gate never opened, so no DEV map exists.

| key number | meaning | file on this branch |
|---|---|---|
| 6 of 6 | PHerc.1667 iterations eligible for P4-O (no documented Paris 4 / Scroll 1 data) | `logs/sib/ckpt-screen-b/p4o/provenance.json` |
| FAIL (uninformative) | iteration-5 known-text gate at the first stage read | `logs/sib/ckpt-screen-b/STATUS.md` |
| 13 | iteration-5 tiles in the final interim manifest | `logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5/manifest.json` |
| 3.3-4.2 CPU-h | cost per 2 x 2 cm tile per checkpoint (4 vCPU, fp32, stride 128) | `logs/sib/ckpt-screen-b/p4o/SUBSIBS.md` |
| a = 1.152, b = -0.065 | fitted affine input correction toward the training statistics implied by the weights (small) | `logs/sib/ckpt-screen-b/p4o/renorm_test.json` |
| 83,317,825 | parameters of the shared ResNet3D-50 + 2-D U-Net architecture | `logs/sib/ckpt-screen-b/SPECS.json` |

## Where the records are

- `logs/sib/ckpt-screen-b/STATUS.md`
- `logs/sib/ckpt-screen-b/RESUME.md`
- `logs/sib/ckpt-screen-b/SPECS.json`
- `logs/sib/ckpt-screen-b/smoke.json`
- `logs/sib/ckpt-screen-b/insample.json`
- `logs/sib/ckpt-screen-b/p4o/provenance.json`
- `logs/sib/ckpt-screen-b/p4o/ASK.md`
- `logs/sib/ckpt-screen-b/p4o/WORKER.md`
- `logs/sib/ckpt-screen-b/p4o/SUBSIBS.md`
- `logs/sib/ckpt-screen-b/p4o/merges.jsonl`
- `logs/sib/ckpt-screen-b/p4o/renorm_test.json`
- `logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5/manifest.json`
- `logs/sib/fl3-pherc0483b/STATUS.md`
- `tools/sib/ckpt-screen-b/`

## Lesson

A cross-scroll model with clean provenance can still be blind on a new scan; the known-text gate exposed the domain gap before any target tile was interpreted.

## Related

- sib-ckpt-screen-b-s1
- sib-ckpt-screen-b-s2
- sib-ckpt-screen-b-s3
- sib-ckpt-screen-a
- sib-ckpt-screen-c
- sib-chain2um
- sib-pairs0814b
- DECL-DEVLOOP-SCREEN
- DECL-P4-14
- DECL-P4-14-A1
- DECL-P4-14-A2
- DECL-P4-14-A3
- P4-O-PROVENANCE
- P4-O-STAGE-O2S1-RESULT
- DECL-P4-23

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
uv venv /opt/ckb --python 3.11
VIRTUAL_ENV=/opt/ckb uv pip install torch --index-url https://download.pytorch.org/whl/cpu
VIRTUAL_ENV=/opt/ckb uv pip install "transformers==4.57.6" safetensors numpy opencv-python-headless tifffile imagecodecs "zarr<3" pillow requests
/opt/ckb/bin/python tools/sib/ckpt-screen-b/fetch.py cards 5
/opt/ckb/bin/python tools/sib/ckpt-screen-b/fetch.py model.safetensors 5
OMP_NUM_THREADS=4 P4O_WORK=/work/p4o setsid nohup /opt/ckb/bin/python tools/sib/ckpt-screen-b/p4o_tiles.py --iteration 5 --out logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5 --tiles "R,C" >> /work/p4o/worker.log 2>&1 < /dev/null &
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
