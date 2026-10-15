<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Checkpoint screen C + iteration-4 run: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Checkpoint screen C + iteration-4 run

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-ckpt-screen-c` · ink-model training and checkpoint screening · 2026-09-26..2026-09-28 · status **INCOMPLETE** · verdict **UNKNOWN**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

Can five further official checkpoints (three TimeSformers, resnet50_7.9um_scroll1_frags and fiber_ink_4class_selfdistill) be screened on DEV windows, and are any of them eligible for P4-O? As a P4-O builder, the lane then had to run PHerc.1667-iteration-4 on the PHercParis4 surface volume.

## Method

Ran phase 1 of the DEV screen: sha256-verified weights, input specs from cards and the registry, the screen_infer.py wrapper, a synthetic smoke test, an in-sample table and runtimes. Wrote provenance.json with quoted training-data statements. The iteration was fixed by a rule that does not depend on results (DECL-P4-14-A2 item 3). P4-O tiles were computed by the parent and three sub-siblings with ckpt-screen-b's builder pinned by sha256 (fp32, card geometry). A declared bf16-vs-fp32 equivalence check on one gate tile came first, and a merge loop built an interim manifest.

## What ran on this branch

Phase 1 and provenance ran on 2026-09-26. Iteration-4 inference started 2026-09-27 01:06Z, at 4.05 s per window, or about 4.9 CPU-h per 2 x 2 cm tile at 4 threads fp32. The bf16 check ran on 2026-09-27. An OOM incident, fixed upstream, cost about 6 h of parent compute. The sub-siblings were archived on 2026-09-28 08:00Z (not by this session), and their remaining tiles were reassigned to the parent. The last commit, 2026-09-28 20:21Z, is an interim manifest of 14 fp32 tiles.

## Outcome

Provenance: 0 of 5 checkpoints are eligible. The reasons are Scroll 1 / Paris 4 training, Paris 4 pretraining or self-distillation, or ambiguous pretraining. The bf16 check FAILED: 8.94 % of mesh-valid pixels differ by more than 2/255 against a 1 % limit, so all iteration-4 tiles are fp32. The interim manifest met the stage threshold, but no stage read of iteration-4 is recorded on this branch or in the research log, so its outcome is unknown. The DEV screen never ran because its gate never opened.

| key number | meaning | file on this branch |
|---|---|---|
| 0 of 5 | checkpoints eligible for P4-O | `logs/sib/ckpt-screen-c/p4o/provenance.json` |
| 0.0894 | fraction of mesh-valid pixels with \|bf16 - fp32\| > 2/255 on the check tile (limit 0.01; FAIL) | `logs/sib/ckpt-screen-c/p4o/bf16_check.json` |
| 14 | fp32 iteration-4 tiles in the interim manifest at the last commit | `logs/sib/ckpt-screen-c/p4o/PHerc.1667-iteration-4/manifest.json` |
| 4.05 s | measured time per 256 x 256 model window at 4 threads fp32 (about 4.9 CPU-h per tile) | `logs/sib/ckpt-screen-c/ASK.md` |
| 624 CPU-min | DEV-screen runtime per 2 cm window for four screenable checkpoints, both orders | `logs/sib/ckpt-screen-c/STATUS.md` |

## Where the records are

- `logs/sib/ckpt-screen-c/STATUS.md`
- `logs/sib/ckpt-screen-c/RESUME.md`
- `logs/sib/ckpt-screen-c/ASK.md`
- `logs/sib/ckpt-screen-c/SPECS.json`
- `logs/sib/ckpt-screen-c/insample.json`
- `logs/sib/ckpt-screen-c/smoke/`
- `logs/sib/ckpt-screen-c/p4o/provenance.json`
- `logs/sib/ckpt-screen-c/p4o/bf16_check.json`
- `logs/sib/ckpt-screen-c/p4o/SUBSIBS.md`
- `logs/sib/ckpt-screen-c/p4o/PHerc.1667-iteration-4/manifest.json`
- `tools/sib/ckpt-screen-c/`

## Lesson

A one-tile bf16 equivalence check, run before production tiles, settled precision cheaply and kept the material fp32.

## Related

- sib-ckpt-screen-c-s1
- sib-ckpt-screen-c-s2
- sib-ckpt-screen-c-s3
- sib-ckpt-screen-b
- sib-ckpt-screen-a
- sib-chain2um
- DECL-DEVLOOP-SCREEN
- DECL-P4-14
- DECL-P4-14-A2
- DECL-P4-14-A3
- P4-O-PROVENANCE-2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
bash tools/sib/ckpt-screen-c/fetch_ckpts.sh
bash tools/sib/ckpt-screen-c/smoke_all.sh
/opt/hv-ink/bin/python tools/sib/ckpt-screen-c/smoke_check.py /work/ckscr/smoke/smoke384.npy /work/ckscr/smoke/out
/opt/hv-ink/bin/python tools/sib/ckpt-screen-c/p4o_run.py (wraps ckpt-screen-b p4o_tiles.py pinned by sha256)
/opt/hv-ink/bin/python tools/sib/ckpt-screen-c/p4o_bf16check.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
