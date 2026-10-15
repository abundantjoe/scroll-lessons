<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Fleet worker: verso maps and FL grows: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Fleet worker: verso maps and FL grows

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4v-01` · PARIS-4 investigations · 2026-09-30..2026-10-02 · status **STOPPED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4, PHerc0125, PHerc0268.

## Question

This worker lane served three fleet orders in turn. (1) P4-OFF: verso-mode offset ink maps on the Paris 4 title-strip segment (DECL-P4-26-A2). (2) First Letters DECL-FL-2: auto-grow plus official-model ink tiles on PHerc0125, seed lane 0. (3) DECL-FL-4: auto-grow on PHerc0268.

## Method

(1) The lane ran the frozen infer_verso.py with own-lead's infer.py unchanged and the hash-verified S1 model on 6 assigned tiles, verso then forward, after a forward reproducibility check. (2) PHerc0125 has no organizer tifxyz segments, so the lane auto-grew segments from the organizer surface prediction and umbilicus. It rejected grows with self-crossings, then rendered, ran the official ink model and cut tiles, pushing per seed. Deviations D1-D5 were disclosed. (3) It ran the fleet kit's auto-grow on PHerc0268.

## What ran on this branch

This ran 2026-09-30 23:29Z to 2026-10-02 07:43Z. P4-OFF: 6 verso and 6 forward maps, and the reproducibility check passed byte-identical. FL-2: 24 grow attempts, 22 segments kept, 176 official-model tiles, 2 grows rejected for self-crossings; then stopped by order DECL-FL-4-A1. FL-4: 8 grows kept (about 11.67 cm2 each), but all 8 renders failed on the first attempt (0/8). After a restart the lane produced partial output for one segment, then stopped when its keep-alive background command hit the time limit and was not restarted.

## Outcome

This was a production worker with no verdict of its own. Its verso maps, together with other workers' maps, fed the P4-OFF verso census, recorded in the research log as P4-OFF-VW-RESULT: no candidate. The PHerc0125 tiles feed the DECL-FL-2 census waves recorded in the research log. The PHerc0268 lane was left incomplete (ALL_DONE absent).

| key number | meaning | file on this branch |
|---|---|---|
| 6 + 6 | verso and forward P4-OFF maps produced (forward repro PASS) | `logs/sib/p4v-01/STATUS.md` |
| 22 / 176 | PHerc0125 segments kept / official-model tiles produced | `logs/sib/p4v-01/fl2/STATUS.md` |
| 2 | PHerc0125 grows rejected for self-crossings | `logs/sib/p4v-01/fl2/STATUS.md` |
| 0/8 | PHerc0268 renders completed on the first pass (lane incomplete) | `logs/sib/p4v-01/fl4/PHerc0268/STATUS.md` |

## Where the records are

- `logs/sib/p4v-01/STATUS.md`
- `logs/sib/p4v-01/verso/`
- `logs/sib/p4v-01/fwd_x/`
- `logs/sib/p4v-01/fl2/`
- `logs/sib/p4v-01/fl4/PHerc0268/`
- `tools/sib/p4v-01/`

## Lesson

A long detached pipeline needs an approved way to persist; a keep-alive that hits its time limit leaves the lane silently incomplete.

## Related

- sib-own-lead
- DECL-P4-26-A2
- DECL-FL-2
- DECL-FL-2-E1
- DECL-FL-4-A1
- DECL-FL-4-A2

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

## Quick start (as recorded, not re-run)

```bash
# as recorded, not re-run
python tools/p4/infer_verso.py --model <pth> --summary <summary.json> --tiles "<seg:r,c>;..." --out logs/sib/<you>/verso --threads 2
python tools/sib/own-lead/infer.py --model <pth> --summary <summary.json> --tiles "..." --out logs/sib/<you>/fwd_x --threads 2
setsid nohup bash tools/sib/p4v-01/fl2/watchdog.sh >/dev/null 2>&1 &
bash tools/fl4/go.sh p4v-01 PHerc0268 1 16
```

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
