<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="2.4 um canonical ink chain on CPU: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# 2.4 um canonical ink chain on CPU

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-chain2um` · ink-model training and checkpoint screening · 2026-09-25..2026-09-30 · status **COMPLETED** · verdict **INCONCLUSIVE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0139, PHercParis4.

## Question

Can the official 2.4 um canonical ink model (scrollprize/ink_canonical_2um) run end to end on CPU and reproduce the organizer's own ink map on a labelled PHerc0139 control? What does it cost per cm^2?

## Method

Rendered a code-selected, organizer-labelled PHerc0139 control region (0.185 cm^2 scored, 0.280 cm^2 crop) with vc_render_tifxyz -n 63 --flip-normals. Ran the official inference code unchanged in both depth orders: fp32 for both, plus emulated bf16 for the text order. Scored AUC and Pearson against the organizer labels and the organizer map with the hashed project metric. Checked render fidelity against the organizer surface volume, and tested depth-order naming directly with an unflipped render.

## What ran on this branch

Ran 2026-09-25/26 on a 4-vCPU Xeon without AMX: four 260-tile inference passes (fp32 forward, fp32 reverse, bf16 forward, and fp32 reverse on an unflipped render) plus fidelity checks. On 2026-09-26 it also built a streaming input reader and a 108-tile hash manifest for the P4-O checkpoint runs on a PHercParis4 surface volume (logs/sib/chain2um/p4o/). No model was run on Paris 4 here. On 2026-09-30 the session prepared a First Letters pass-2 worker pipeline for PHerc0483, but the session's safety check refused the launch.

## Outcome

The fp32 chain in the official FORWARD order reproduces the organizer map at r 0.999986 (AUC 0.88795 against the organizer map's 0.88798). The official REVERSE order carries no signal (AUC 0.47070). The order called 'reverse' in earlier records is the text order of the unflipped render frame. The GATE-E2E-0139 bar as written (AUC >= 0.90) is not reached even by the organizer's own map on this control, and the control is not the declared window set. The orchestrator therefore did not record the gate as passed, and CHAIN VALID stayed blocked. Emulated bf16 was 98.41 % within +-2 grey levels (bar 99.9 %), which supports keeping fp32 as the chain of record.

| key number | meaning | file on this branch |
|---|---|---|
| 0.999986 | Pearson r of our fp32 FORWARD map vs the organizer map on the scored region | `logs/sib/chain2um/chain2um_results.json` |
| 0.88795 | AUC vs organizer labels, our fp32 FORWARD map (organizer map: 0.88798) | `logs/sib/chain2um/chain2um_results.json` |
| 0.47070 | AUC of the official REVERSE order on the same render (no ink signal) | `logs/sib/chain2um/chain2um_results.json` |
| 98.41 % | crop pixels within +-2 grey levels, emulated bf16 vs fp32 (DECL-AMX-1 part I bar 99.9 %) | `logs/sib/chain2um/REPORT.md` |
| 0.999997-0.999998 | pooled Pearson of the --flip-normals render vs the organizer surface volume (best unflipped: 0.22) | `logs/sib/chain2um/REPORT.md` |
| about 2.4 h wall per cm^2 per order | fp32 cost projection on 4 non-AMX vCPU (about 9.6 core-h); 8.21 s per tile forward | `logs/sib/chain2um/REPORT.md` |

## Where the records are

- `logs/sib/chain2um/REPORT.md`
- `logs/sib/chain2um/STATUS.md`
- `logs/sib/chain2um/chain2um_results.json`
- `logs/sib/chain2um/eval_all.json`
- `logs/sib/chain2um/cost_projection.json`
- `logs/sib/chain2um/control_selection.json`
- `logs/sib/chain2um/proposals/DECL-CHAIN-ORDER-proposal.md`
- `logs/sib/chain2um/p4o/README.md`
- `logs/sib/chain2um/p4o/manifest.json`
- `logs/sib/chain2um/p4o/verify_render.json`
- `logs/sib/chain2um/p4o/verify_level2.json`
- `logs/sib/chain2um/runs.jsonl`
- `logs/sib/fl2-pherc0483a/STATUS.md`

## Lesson

Name the depth order by the render frame, not by the word 'reverse': the same text order is FORWARD on a --flip-normals render and REVERSE on an unflipped one.

## Related

- sib-amx
- sib-ckpt-screen-a
- sib-ckpt-screen-b
- sib-ckpt-screen-c
- DECL-AMX-1
- DECL-CHAINVALID
- DECL-P4-14
- DECL-FL-1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
curl -fsSL -C - https://huggingface.co/scrollprize/ink_canonical_2um/resolve/075855bc69317ef6febf39a0d9d687b27d2b7c29/{r152_3ddec_v2_l5_epoch13.ckpt,README.md,config.json}
/work/pyq/bin/python tools/sib/chain2um/pick_control.py logs/sib/chain2um/control_selection.json
/work/bin/vc vc_render_tifxyz -v <vol> --remote-url <vol> --segmentation <mesh> --scale 1 --group-idx 0 --num-slices 63 --slice-step 1 --voxel-size 2.399 --voxel-unit micrometer --flip-normals --crop-x <x> --crop-y <y> --crop-width 3456 --crop-height 1408 --cache-gb 4 --zarr-output /work/c2um/render/<name>.zarr
tools/sib/chain2um/run_passes.sh forward:fp32 reverse:fp32
/work/pyq/bin/python tools/sib/chain2um/eval2um.py logs/sib/chain2um/control_selection.json logs/sib/chain2um/eval_all.json forward_fp32=/work/c2um/maps/forward_fp32 reverse_fp32=/work/c2um/maps/reverse_fp32
OMP_NUM_THREADS=1 /opt/hv-ink/bin/python -m pytest -q -p no:cacheprovider tests/sib_chain2um_test_official_semantics.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
