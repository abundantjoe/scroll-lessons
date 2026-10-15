<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Submission package factory: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Submission package factory

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-factory` · ink-model training and checkpoint screening · 2026-09-25..2026-09-26 · status **TOOL** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHerc0139.

## Question

Can a submission package (image, mesh, render, tools, reproduce script, manifest) be built reproducibly and checked mechanically, as T-FACTORY in DECL-FACTORY requires, using a DRY RUN on a non-eligible bank mesh?

## Method

The session built a canonical PNG/TIFF writer, an image builder (linear CT window, measured 1 cm scale bar, DRY RUN stamp), an official-renderer wrapper, a package maker, and a verifier with 16 mechanical checks that trusts nothing inside the package. It added a reproduce script that re-renders from the public volume and compares bytes, and a fault drill that plants faults into copies of a finished package. A coded window rule chose the dry-run window with clearances from sealed and session windows.

## What ran on this branch

On 2026-09-25 (18:28Z to 23:49Z): renderer build, window pick (v1 to v7), three independent factory builds of one DRY RUN package on a PHerc0139 bank mesh, verification, reproduction in a clean directory and the fault drill. No image was opened by the session.

## Outcome

The dry run passed its own checks: verifier 16/16; reproduction byte-identical for raw render, CT panel and PNG; each of 6 planted faults rejected by its intended check; 49 unit tests. The package can never pass as real, because PHerc0139 is not eligible. Only DECL-FACTORY bar (a) was exercised: bar (b), a fresh-agent rebuild within 4 h, and bars (c)-(d) were not tested, and the research log lists FACTORY v1 as not started. The Paris 4 package mode and the licence check were not started, because the session then held for the owner's own resume after a direct owner stop.

| key number | meaning | file on this branch |
|---|---|---|
| 16/16 | verifier checks passed on the DRY RUN package | `logs/sib/factory/verify_dryrun.json` |
| byte-identical (55 s) | reproduce.sh rebuild of raw render, CT panel and PNG in a clean directory | `logs/sib/factory/reproduce_dryrun.json` |
| 6 of 6 | planted faults rejected by their intended check | `logs/sib/factory/fault_drill.json` |
| 63 of 1108 | candidate dry-run windows passing the coded clearance rule | `logs/sib/factory/window_pick.json` |
| 49 passed | verifier unit tests (full repository suite 638 passed) | `logs/sib/factory/REPORT.md` |

## Where the records are

- `logs/sib/factory/REPORT.md`
- `logs/sib/factory/report.json`
- `logs/sib/factory/verify_dryrun.json`
- `logs/sib/factory/reproduce_dryrun.json`
- `logs/sib/factory/fault_drill.json`
- `logs/sib/factory/window_pick.json`
- `logs/sib/factory/ASK.md`
- `logs/sib/factory/STATUS.md`
- `packages/dryrun/`
- `tools/sib/factory/`
- `tests/sib_factory_verify_test.py`

## Lesson

A fault drill must require a clean baseline and a failure of the named check; otherwise it passes vacuously, as the first drill here did.

## Related

- sib-sg
- sib-flat1
- DECL-FACTORY
- DECL-P4-2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
bash tools/sib/factory/setup_renderer.sh
/opt/hv/bin/python tools/sib/factory/pick_window.py
bash tools/sib/factory/run_dryrun.sh
/opt/hv/bin/python tools/sib/factory/verify.py PACKAGE_DIR
bash PACKAGE_DIR/reproduce.sh <volume URL> mesh/<name>
/opt/hv/bin/python tools/sib/factory/fault_drill.py PACKAGE_DIR logs/sib/factory/fault_drill.json
PYTHONPATH=src /opt/hv/bin/python -m pytest -q tests/sib_factory_verify_test.py
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
