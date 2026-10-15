<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="DEV-LOOP registry and evaluator: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# DEV-LOOP registry and evaluator

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-devloop` · ink-model training and checkpoint screening · 2026-09-25..2026-09-26 · status **STOPPED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0139, PHerc0814.

## Question

Build the DEV-LOOP harness (DECL-DEVLOOP): a certified registry of known-text DEV windows outside every sealed set and base-training papyrus, and a sigma_eq evaluator that ranks candidate 9 um ink models against the 2.4 um reference.

## Method

The session wrote a registry builder with rules fixed before each run (material, sampling, same-papyrus exclusion of base-training traces, used-window exclusions, window selection by seeded permutation), iterated it to v3, and certified it under CORR-RETRACE-RULE. The evaluator renders each window, applies a CT registration gate, runs official inference in both depth orders, and computes sigma_eq, blank blob-f180 and a CHANCE control. It also drafted first_recipes.md (LC384-FROZEN, LC384-SOFT, DIST-FT, DIST-FT-384), which became DECL-DEVLOOP-A1.

## What ran on this branch

From 2026-09-25 18:37Z to 2026-09-26: mesh fetches, registry v1 to v3, the v4 certificate, 21 synthetic evaluator tests and CT renders of the 9 DEV windows. No model map was made on any DEV window.

## Outcome

Registry v3 holds 9 windows: PHerc0139 4 text + 1 blank and PHerc0814 4 text + 0 blanks, all 9 accepted by the v4 certificate. Under DECL-DEVLOOP-A1, PHerc0814 would not count toward FINALIST without blanks. The freeze (FREEZE.md, hold-out list, METRIC-HASH) was never done: the owner stopped this session directly, and from 2026-09-26 it held for the owner's own resume, which never came. As a result, the DEV recipe lanes and the official-checkpoint screen never received GO.

| key number | meaning | file on this branch |
|---|---|---|
| 9 windows | DEV registry v3: PHerc0139 4 text + 1 blank; PHerc0814 4 text + 0 blanks | `logs/sib/devloop/dev_registry.json` |
| 9 of 9 accepted | CORR-RETRACE-RULE certificate (v4) of the DEV windows | `logs/sib/devloop/dev_certificate_v4.json` |
| 21 passed | synthetic evaluator tests | `logs/sib/devloop/ASK.md` |
| 0 | model maps produced on any DEV window | `logs/sib/devloop/ASK.md` |

## Where the records are

- `logs/sib/devloop/ASK.md`
- `logs/sib/devloop/dev_registry.json`
- `logs/sib/devloop/dev_certificate_v4.json`
- `logs/sib/devloop/history/`
- `logs/sib/devloop/proposals/first_recipes.md`
- `logs/sib/devloop/runs.jsonl`
- `tools/sib/devloop/`
- `tests/sib_devloop_evaluator.py`

## Lesson

One unfinished freeze step in a shared metric harness blocked every downstream recipe and checkpoint screen that depended on it.

## Related

- sib-devloop2
- sib-dev-lcsoft
- sib-dev-distft
- sib-amx
- sib-d2-p128
- DECL-DEVLOOP
- DECL-DEVLOOP-A1
- DECL-DEVLOOP-SCREEN
- DECL-READCAL-A2
- CORR-RETRACE-RULE

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
/opt/hv/bin/python tools/sib/devloop/fetch.py meshes9 PHerc0139
/opt/hv/bin/python tools/sib/devloop/fetch.py meshes9 PHerc0814
bash tools/sib/devloop/env/setup_env.sh
env PYTHONPATH=src OMP_NUM_THREADS=3 /opt/hv/bin/python tools/sib/devloop/registry.py
env PYTHONPATH=src /opt/hv/bin/python tools/sib/devloop/evaluate.py render
env PYTHONPATH=src /opt/hv/bin/python tools/sib/devloop/certify_v4.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
