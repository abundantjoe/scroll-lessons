<p align="center"><img src="docs/dominion_branch_banner.jpg" alt="Title-placement priors and red team: Dominion experiment branch (banner: PHerc0343 CT, no ink shown)" width="100%"></p>

# Title-placement priors and red team

**Dominion experiment branch** `claude/gifted-bell-gavnl5-sib-p4-titulus` · PARIS-4 investigations · 2026-09-26..2026-09-30 · status **COMPLETED** · verdict **NONE**

Part of [Dominion](https://github.com/abundantjoe/dominion): see the [experiment map](https://github.com/abundantjoe/dominion/blob/main/docs/EXPERIMENTS.md) and the [branch index](https://github.com/abundantjoe/dominion/blob/main/BRANCH_INDEX.md). Scrolls: PHercParis4, PHerc1218.

## Question

Using published bibliology and committed numbers only, where, how large and in what ink would the Paris 4 end title most probably be? Are the project's hypothesis register and search windows structured correctly? The lane also answered the orchestrator's questions Q1-Q6.

## Method

Literature research agents covered title geometry, roll manufacture and inks, followed by targeted reading of downloaded sources. Probabilities were graded FIRM/LIKELY/UNCERTAIN with the arithmetic shown. A numbers-only sheet-switch check used mesh vertex distances. The lane red-teamed the hypothesis register and pre-registered later layout tests. No image was viewed, and no title word, author or book number was written.

## What ran on this branch

This ran 2026-09-26 21:40Z to 2026-09-27 07:43Z, producing TITLE_PRIOR v1 (md and json), REDTEAM v1 and QA answers Q1-Q6. The three literature agents stopped on an API rate limit, and their downloaded texts were mined by targeted search. On 2026-09-30 a First Letters worker for PHerc1218 was assigned here. It was not started, because the session safety check refused the self-restarting pipeline (ASK-3).

## Outcome

The priors and red-team findings fed later declarations: the DECL-P4-19 line-structure test and the window order of DECL-P4-17-A1. The red team proposed missing channels: offset (ink transfer), a final-sheet join anchor, and a sparse-block injection control. Two rule questions were left to the orchestrator (ASK-1, ASK-2). This lane gives no experimental verdict.

| key number | meaning | file on this branch |
|---|---|---|
| 0/70 | Herculaneum end titles placed above the column in a published census of 70 titles (95 % upper bound 4 %) | `logs/sib/p4-titulus/QA.md` |
| 4 | deliverables pushed at v1 (TITLE_PRIOR md+json, REDTEAM, QA) | `logs/sib/p4-titulus/STATUS.md` |
| Q1-Q6 | orchestrator questions answered or pre-registered | `logs/sib/p4-titulus/QA.md` |
| 3 | open asks to the orchestrator/owner (ASK-1..ASK-3) | `logs/sib/p4-titulus/ASK.md` |

## Where the records are

- `logs/sib/p4-titulus/TITLE_PRIOR.md`
- `logs/sib/p4-titulus/title_prior.json`
- `logs/sib/p4-titulus/REDTEAM.md`
- `logs/sib/p4-titulus/QA.md`
- `logs/sib/p4-titulus/ASK.md`
- `logs/sib/p4-titulus/sheet_switch_check.txt`
- `tools/sib/p4-titulus/`

## Lesson

Cut search windows by physical column slots, not by tile ranges fixed before the layout was known.

## Related

- sib-p4-research
- sib-p4-tiles-a
- DECL-P4-15
- DECL-P4-17-A1
- DECL-P4-19
- DECL-FL-1

---

This README describes the experiment on this branch. It was written on 2026-10-15 from the branch's own commits and record files by a read-only survey, then audited, under the confidentiality rules of the public release: no letter identities, no locations of candidate features and no reading hints for unread scrolls. Numbers are taken from the files named above, some rounded or summed. The previous README of this branch, the shared operating README of the programme, is kept as [README_HERCULES.md](README_HERCULES.md); only its provenance line was shortened, to remove personal information.

---
*Part of **Dominion**, directed by Joseph Balmaceda and run by Claude research agents (Sept-Oct 2026). Every lesson from every branch, in one file: [MASTER_LESSONS.md](https://github.com/abundantjoe/scroll-lessons/blob/main/MASTER_LESSONS.md). This branch is a scrubbed snapshot of the private archive: personal data removed, files over the size policy listed in `DATA_MANIFEST.tsv`, prize-candidate details withheld.*
