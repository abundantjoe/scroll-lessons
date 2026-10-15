<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="D2 P128 arm trainer setup: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# D2 P128 arm trainer setup

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-d2-p128` · ink-model training and checkpoint screening · 2026-09-26..2026-09-26 · status **INCOMPLETE** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0814.

## Question

Can the P128 arm of decision D2 (TRAIN-1, fold L-0841: base recipe, 128 px tiles, 24 x 15 deg rotations, seed 1) be set up to train reproducibly on CPU and start at GO D2?

## Method

The session pinned the environment to the project's ink freeze, copied the trainer from the trainer lane byte-identically (commit 8475920), verified the base ink_9um checkpoint, ran the trainer test suites at the pinned and the later trainer commit, and ran a 30-step synthetic P128 smoke with a hard-exit-and-resume test. It also recomputed the DECL-D2 pair filter on the trainer's dry-run allowlist and checked it against the DEV-LOOP hold-out segments. Open choices went to ASK.md with defaults, and nothing was to train before GO D2.

## What ran on this branch

Phase 1 only, on 2026-09-26, on a 4-vCPU Cascade Lake container with no AMX (fp32). The smoke used a 256-patch synthetic registry. The hold-out check used only registry metadata of the PHerc0814 dry-run pair allowlist; no image was opened and no real training step ran.

## Outcome

Phase 1 passed: 26/26 tests at the pinned commit and 30/30 at the later one, bitwise-equal losses and weights after resume, 18.35 s/step. The independent filter reproduced the 329-patch dry-run allowlist exactly and found that 121 of those patches lie on DEV hold-out segments, which DECL-DEVLOOP-A1 excludes from D2 training. The default recorded was to stop and ask if the freeze lacked that hold-out. The orchestrator's 06:01Z check-in accepted the defaults for preparation only. The session then idled until GO D2, which never came: no D2 amendment was declared and the research log records D2 as blocked for lack of a GPU.

| key number | meaning | file on this branch |
|---|---|---|
| 18.35 s/step | median step time, P128 fp32, 4 threads, batch 32 (synthetic smoke, 30 steps) | `logs/sib/d2-p128/smoke_result.json` |
| 61.2 h (2.55 d) | projected loop time for 12,000 steps on this CPU at fp32 | `logs/sib/d2-p128/READY.md` |
| 6.85 GB | peak RSS of the smoke run | `logs/sib/d2-p128/smoke_result.json` |
| 26/26 and 30/30 | trainer tests passed at the pinned commit 8475920 and at the later commit 08d7e42 | `logs/sib/d2-p128/STATUS.md` |
| 121 of 329 | dry-run allowlist patches that lie on DEV hold-out segments | `logs/sib/d2-p128/holdout_check.json` |

## Where the records are

- `logs/sib/d2-p128/READY.md`
- `logs/sib/d2-p128/STATUS.md`
- `logs/sib/d2-p128/ASK.md`
- `logs/sib/d2-p128/smoke_result.json`
- `logs/sib/d2-p128/holdout_check.json`
- `logs/sib/d2-p128/runs.jsonl`
- `tools/sib/d2-p128/`

## Lesson

An independent recomputation of the pair filter showed that the dry-run allowlist overlapped DEV hold-out segments, so hold-outs have to be applied in the freeze record and cannot be assumed.

## Related

- sib-trainer
- sib-devloop
- sib-pairs0814
- sib-d2-p384
- sib-d2-null
- sib-d2-rev
- DECL-D2
- DECL-D2-A1 (proposal, never declared)
- DECL-DEVLOOP-A1
- DECL-AMX-1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
bash tools/sib/d2-p128/setup_p128_env.sh
bash tools/sib/d2-p128/smoke_p128.sh
python3 tools/sib/d2-p128/holdout_check.py logs/sib/d2-p128/holdout_check.json
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
