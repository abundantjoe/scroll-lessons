<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="FE detector: 2.4 um family run: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# FE detector: 2.4 um family run

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-pig-fe-e2` · PARIS-4 investigations · 2026-09-26..2026-09-26 · status **COMPLETED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4.

## Question

This was a sub-task of p4-pig-fe. It ran the frozen FE (ochre) detector on the 2.4 um family, the known-text control C2 and the title strip E2, including injection-recovery, so the parent could report the detection limit at the 2.4 um voxel.

## Method

It ran tools/sib/p4-pig-fe/run_family.py C2 E2 with 12 injection locations per material, from the parent at the params freeze, with no code or parameter change. The run calibrated on the control (sigma0 = 1.4826 MAD; theta = p99 of control z together with rot-90 z) and measured leave-one-out false positives. It then injected synthetic letters on C2 and E2 (three regimes x 2/5/10/20 um) and scored all 160 E2 tiles.

## What ran on this branch

This ran 2026-09-26 18:30Z-19:05Z. The C2 maps used 191,240 chunks (11,032 absent) and 182,432,734 positions; the E2 maps used 170,172 chunks. Run 1 crashed at the start of E2 injection because this clone lacked a remote ref that the frozen params read (an environment fault). The ref was fetched and the identical command rerun.

## Outcome

C2 control: sigma0 2.21971, theta 13.8444, leave-one-out false positives 2/188. The rot-90 null is identical to z on every tile; this was flagged, because it adds no independent sample. Injection: 0/12 at every thickness up to 20 um in the electron-density regimes, on C2 and E2. In the mu regime, 12/12 at 10 and 20 um on C2, and 9/12 at 10 um and 12/12 at 20 um on E2. E2 scores: median z 9.107, maximum 14.042, 1 of 160 tiles above theta, consistent with the null. These numbers feed the parent's verdict: insensitive at 5-10 um, with a mu-regime limit of 20 um on E2.

| key number | meaning | file on this branch |
|---|---|---|
| 13.8444 | theta for the 2.4 um family (p99 of control z and rot-90 z) | `logs/sib/p4-pig-fe/24/STATUS.md` |
| 2/188 | leave-one-out false positives on control C2 | `logs/sib/p4-pig-fe/24/STATUS.md` |
| 12/12 | C2 recovery in the standard mu regime (x10.9) at 10 um | `logs/sib/p4-pig-fe/24/injection_C2.json` |
| 9/12 | E2 recovery in the standard mu regime at 10 um (12/12 at 20 um) | `logs/sib/p4-pig-fe/24/injection_E2.json` |
| 0/12 | recovery in both electron-density regimes at 2-20 um on C2 and E2 | `logs/sib/p4-pig-fe/24/injection_E2.json` |
| 14.042 | maximum E2 tile z (median 9.107; 1 of 160 tiles above theta) | `logs/sib/p4-pig-fe/24/scores_E2.json` |

## Where the records are

- `logs/sib/p4-pig-fe/24/STATUS.md`
- `logs/sib/p4-pig-fe/24/scores_C2.json`
- `logs/sib/p4-pig-fe/24/injection_C2.json`
- `logs/sib/p4-pig-fe/24/injection_E2.json`
- `logs/sib/p4-pig-fe/24/scores_E2.json`
- `logs/sib/p4-pig-fe/24/run_log.jsonl`

## Lesson

Pin every git ref a frozen detector reads to a commit SHA; these params named branch tips, so a rerun depends on fetch time.

## Related

- sib-p4-pig-fe
- sib-p4-pig-fe-e1
- sib-pairs0814b
- sib-p4-tiles-b
- DECL-P4-10
- DECL-P4-12

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/sib/p4-pig-fe/run_family.py C2 E2 /tmp/fe24 claude/gifted-bell-gavnl5-sib-p4-pig-fe-e2 12
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
